import json
import os
import nltk
import numpy as np
import faiss  # Pour l'indexation et la recherche de similarités
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, Request
from pydantic import BaseModel
from tqdm import tqdm
import gc
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from sklearn.linear_model import LogisticRegression  # Pour la classification
import re
from nltk.corpus import wordnet
from nltk.corpus import wordnet as wn
import unicodedata
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from langdetect import detect, DetectorFactory
from fastapi.responses import FileResponse, HTMLResponse

DetectorFactory.seed = 0

# Télécharger les ressources NLTK nécessaires
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')
nltk.download('punkt_tab')

def get_synonyms_fr(word):
    word = remove_accents(word.lower())
    synonyms = set()
    for syn in wn.synsets(word, lang='fra'):
        if syn.pos() != 'v':  # exemple : ne garder que les noms ('n'), ignorer les verbes pour éviter "abolir"
            continue
        for lemma in syn.lemmas(lang='fra'):
            lemma_clean = remove_accents(lemma.name().lower().replace('_', ' '))
            if lemma_clean != word:
                synonyms.add(lemma_clean)
    return synonyms


def build_synonym_mapping_from_questions(questions):
    word_to_pivot = {}
    pivot_to_group = {}
    for q in questions:
        for token in re.findall(r"\b\w+\b", q.lower()):
            if token in word_to_pivot:
                continue
            synonyms = get_synonyms_fr(token)
            if synonyms:
                pivot = sorted(synonyms)[0]
                for syn in synonyms:
                    word_to_pivot[syn] = pivot
                pivot_to_group[pivot] = synonyms
    return word_to_pivot, pivot_to_group

def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^\w\s']", "", text)
    text = re.sub(r"[^\w\s]", "", text)  # supprime la ponctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text



def normalize_with_synonyms(text, word_to_pivot_map):
    tokens = re.findall(r"\b\w+\b", text.lower())
    return " ".join([word_to_pivot_map.get(t, t) for t in tokens])

def remove_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# --- Fonction de normalisation d'argot ---
def normalize_argot(text: str) -> str:
    # Dictionnaire des expressions argotiques et leurs équivalents standard
    slang_mapping = {
        "yo": "bonjour",
        "wesh": "bonjour",
        "hey": "bonjour",
        "coucou": "bonjour",
        "comment ca va": "bonjour",
        "comment ça va": "bonjour",
       
    }
    text = remove_accents(text.lower())
    tokens = text.split()
    normalized_tokens = [slang_mapping.get(token.lower(), token) for token in tokens]
    normalized_text = " ".join(normalized_tokens)
    print(f"Texte normalisé: '{normalized_text}'")
    return normalized_text

def remove_salutations(text: str) -> str:
    salutations = {"bonjour", "salut", "yo", "hey", "hello", "coucou", "wesh", "plop", "hi", "bien le bonjour"}
    text = text.strip().lower()
    tokens = text.split()

    # Si le premier mot est une salutation, on le retire
    if tokens and tokens[0] in salutations:
        return " ".join(tokens[1:]).lstrip(",.!? ")
    return text

# def split_into_subquestions(text: str) -> list[str]:
#     # Remplace les "?", "!" par des points pour faciliter le découpage
#     text = text.strip().replace("?", ".").replace("!", ".")
    
#     # Coupe les phrases sur certains mots de coordination si un verbe suit
#     clauses = re.split(r'\b(?:et|ainsi que|mais aussi|puis|pour|afin de)\b\s+(?=\w+)', text, flags=re.IGNORECASE)

#     result = []
#     for clause in clauses:
#         # Découpe chaque clause en phrases avec nltk
#         sentences = nltk.sent_tokenize(clause)
#         result.extend(sentences)

#     # Nettoyage final
#     return [s.strip() for s in result if s.strip()]

def split_into_subquestions(text: str) -> list[str]:
    """
    Découpe uniquement sur ponctuation forte (., ?, !).
    Si le texte ne contient qu’une seule phrase complète, le garde intact.
    """
    text = text.strip()

    # Normalise la ponctuation
    text = re.sub(r"[!?]", ".", text)

    # Découpe en phrases sur les points
    raw_sentences = re.split(r"\.\s*", text)

    # Nettoyage
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    # S’il n’y a qu’une seule phrase ou si la phrase est longue (>20 mots), on ne segmente pas
    if len(sentences) == 1 or len(text.split()) < 25:
        return [text.strip()]
    else:
        return sentences



def expand_synonyms(text: str) -> str:
    tokens = nltk.word_tokenize(text.lower())
    syns = set()
    for token in tokens:
        for syn in wordnet.synsets(token, lang='fra'):
            for lemma in syn.lemmas(lang='fra'):
                syns.add(lemma.name().replace('_', ' '))
    return text + ' ' + ' '.join(syns)

# --- Fonction de traitement conditionnel ---
def process_text(text: str) -> str:
    # Pour les textes courts (1 ou 2 mots), on évite l'expansion des synonymes
    if len(text.split()) <= 2:
        return text
    else:
        return expand_synonyms(text)

# --- Fonction pour extraire l'âge d'un texte ---
def extract_age(text: str) -> str:

    print(f"Extraction d'âge sur : '{text}'")

    match = re.search(r"(\d+)\s*ans", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None
def extract_frere(text: str) -> str:
    print(f"Extract frere ou soeur : '{text}'")
    match = re.search(r"(?:j'ai|ai)?\s*(un|une|\d+)\s*(frère|frere|soeur|sœur)s?", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def search_frere_soeur_in_database(target_tag="presentation_sylvain_regnier") -> str:
    for entry in database:
        if entry.get("tag", "") == target_tag:
            frere = extract_frere(entry.get("response", ""))
            if frere:
                print(f"Frere/soeur trouvé dans le tag '{target_tag}': {frere}")
                return frere
    return None

# --- Fonction pour chercher l'âge dans la base ---
def search_age_in_database(target_tag="presentation_sylvain_regnier") -> str:
    # Filtrer les entrées qui correspondent au tag cible
    for entry in database:
        if entry.get("tag", "") == target_tag:
            age = extract_age(entry.get("response", ""))
            if age:
                print(f"Âge trouvé dans le tag '{target_tag}': {age} dans '{entry.get('response', '')}'")
                return age
    return None

def search_daughter_age_in_database(target_tag="presentation_fille_sylvain") -> str:
    for entry in database:
        if entry.get("tag", "") == target_tag:
            age = extract_age(entry.get("response", ""))
            if age:
                print(f"Âge de la fille trouvé dans le tag '{target_tag}': {age} ans.")
                return age
    return None



# --- Chargement des fichiers et préparation des embeddings ---
EMBEDDINGS_FILE = "embeddings.npy"
QUESTIONS_FILE = "questions.json"
FALLBACK_FILE = "fallback_text.txt"

# Dossier pour sauvegarder l'historique de chat par session
CHAT_HISTORY_DIR = "chat_histories"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)
session_files = {}

print("📥 Chargement du modèle NLP...")
try:
    # model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
except Exception:
    model = SentenceTransformer('all-MiniLM-L6-v2')

# Liste des fichiers d'intents
json_files = [
    "intents/css_cleaned.json",
    "intents/employeur_cleaned.json",
    "intents/futur_cleaned.json",
    "intents/html_cleaned.json",
    "intents/php_cleaned.json",
    "intents/programmation_cleaned.json",
    "intents/parcours_cleaned.json",
    "intents/professionnel_cleaned.json",
    "intents/personnel_cleaned.json",
    "intents/politesses_cleaned.json",
    "intents/recherche_cleaned.json",
    "intents/vieentreprise_cleaned.json",
    "intents/question_cleaned.json"
]

# --- Création de la nouvelle base de données à partir des fichiers JSON ---
database = []
for file_path in json_files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if "intents" in data and isinstance(data["intents"], list):
                local_count = 0
                print(f"\n📂 Traitement de {file_path}...")
                for intent in data["intents"]:
                    tag = str(intent.get("tag", "")).lower()
                    context_set = str(intent.get("context_set", "")).lower()
                    aliases = [str(alias).strip().lower() for alias in intent.get("aliases", [])]
                    patterns = [str(p).strip().lower() for p in intent.get("patterns", [])]
                    responses = [str(r).strip().lower() for r in intent.get("responses", ["je ne sais pas."])]
                    response = responses[0]
                    questions = patterns + aliases

                    for question in questions:
                        question_clean = remove_accents(question.strip().lower())
                        if not question_clean or len(question_clean) <= 3:
                            continue
                        database.append({
                        "tag": tag,
                        "context_set": context_set,
                        "aliases": aliases,
                        "question": question_clean,
                        "response": response
                    })



# --- Mise à jour incrémentale des embeddings ---
if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(QUESTIONS_FILE):
    # Charger les embeddings et la base de données existante
    loaded_embeddings = np.load(EMBEDDINGS_FILE)
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        loaded_database = json.load(f)
    
    # Créer un ensemble de questions déjà présentes pour comparaison
    existing_questions = {entry["question"] for entry in loaded_database}
    
    # Identifier les nouvelles entrées (questions absentes)
    additional_entries = [entry for entry in database if entry["question"] not in existing_questions]
    
    print(f"➕ {len(additional_entries)} nouvelles entrées détectées.")
    
    if additional_entries:
        additional_embeddings = []
        for q in tqdm(additional_entries, desc="Encodage des nouvelles entrées"):
            text_to_encode = f"{q['question']} [tag: {q['tag']}] [context: {q['context_set']}] [aliases: {', '.join(q['aliases'])}]"
            text_to_encode = remove_accents(text_to_encode.lower())

            additional_embeddings.append(model.encode(text_to_encode))
        additional_embeddings = np.array(additional_embeddings, dtype='float32')
        
        # Concaténer les nouvelles embeddings aux embeddings existants
        questions_embeddings = np.concatenate([loaded_embeddings, additional_embeddings], axis=0)
        
        # Mettre à jour la base de données
        loaded_database.extend(additional_entries)
        
        # Sauvegarder les mises à jour sur disque
        np.save(EMBEDDINGS_FILE, questions_embeddings)
        with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(loaded_database, f, indent=4, ensure_ascii=False)
        
        database = loaded_database
        
        print("🧠 Ré-entraîne le vectorizer et le classifieur...")

        X = [entry["question"] for entry in database]
        y = [entry["tag"] for entry in database]

        vectorizer = TfidfVectorizer()
        X_vect = vectorizer.fit_transform(X)

        classifier = LogisticRegression(max_iter=1000)
        classifier.fit(X_vect, y)

        # 💾 Sauvegarde les modèles entraînés
        joblib.dump(vectorizer, "vectorizer.joblib")
        joblib.dump(classifier, "classifier.joblib")

        # Recharge pour usage immédiat
        vectorizer = joblib.load("vectorizer.joblib")
        classifier = joblib.load("classifier.joblib")

        print("✅ Vectorizer et classifieur ré-entrainés et sauvegardés.")




    else:
        print("Aucune nouvelle entrée détectée.")
        questions_embeddings = loaded_embeddings
        database = loaded_database

else:
    # Aucun fichier existant : encodage complet de la base
    print("\n🚀 Encodage complet des données en cours...")
    questions_embeddings = []
    for q in tqdm(database, desc="Encodage complet"):
        text_to_encode = f"{q['question']} [tag: {q['tag']}] [context: {q['context_set']}] [aliases: {', '.join(q['aliases'])}]"
        text_to_encode = remove_accents(text_to_encode.lower())
        questions_embeddings.append(model.encode(text_to_encode))
    questions_embeddings = np.array(questions_embeddings, dtype='float32')
    np.save(EMBEDDINGS_FILE, questions_embeddings)
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4, ensure_ascii=False)
    database = database

# Normalisation des embeddings pour obtenir des vecteurs de norme 1 (pour la similarité cosinus)
norms = np.linalg.norm(questions_embeddings, axis=1, keepdims=True)
questions_embeddings_norm = questions_embeddings / norms

d = questions_embeddings_norm.shape[1]
global_index = faiss.IndexFlatIP(d)
global_index.add(questions_embeddings_norm)
print(f"\nFAISS index global créé avec {global_index.ntotal} entrées.")

# --- Fallback ---
with open(FALLBACK_FILE, encoding="utf-8") as f:
    fallback_text = f.read().lower()
fallback_sentences = nltk.sent_tokenize(fallback_text)
fallback_emb = np.array([model.encode(s) for s in fallback_sentences], dtype='float32')
fallback_index = faiss.IndexFlatIP(fallback_emb.shape[1])
fallback_index.add(fallback_emb / np.linalg.norm(fallback_emb, axis=1, keepdims=True))

# --- Classification par tags ---
tags = [entry["tag"] for entry in database]
clf = LogisticRegression(max_iter=1000).fit(questions_embeddings, tags)

gc.collect()
print("\n✅ Serveur prêt, lancement de l'API...")

# --- Création de l'API FastAPI ---
app = FastAPI(root_path="/chatbot")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/documents", StaticFiles(directory="documents"), name="documents")

@app.get("/", response_class=HTMLResponse)
def redirect_to_index():
    return FileResponse("static/index.html")

class QuestionRequest(BaseModel):
    question: str
    user_token: str


@app.post("/handle_message")
async def handle_message(request: Request):
    print("🟢 handle_message start")
    data = await request.json()
    raw = data.get("message", "")
    raw_original = raw  # pour garder une trace si tu modifies raw plus tard
    print(f"🔹 Message reçu : {raw}")

    salutations_detectees = {"bonjour", "salut", "yo", "wesh", "coucou", "hey"}
    if normalize_text(raw_original) in salutations_detectees:
        return {
         "response": "Bonjour, bienvenue sur mon ChatBot de pré-entretien !",
            "score": 1.0,
            "tag": "salutation"
        }


# Normalise les accents et argot AVANT découpage
    text_with_slang_handled = normalize_argot(raw_original)
    text_without_salut = remove_salutations(text_with_slang_handled)
   

    print(f"🔹 Texte normalisé : {text_without_salut}")


    responses = []
    best_fallback_response = ""
    best_score = -1.0
    best_tag = ""

    sub_questions = split_into_subquestions(text_without_salut)
    print(f"🔍 Sous-questions détectées : {sub_questions}")

    for sub_q in sub_questions:
        emb_input = remove_accents(sub_q.lower())
        resp = find_best_response(emb_input)

        score = resp.get("score", 0.0)
        response = resp["response"].strip()
        tag = resp.get("tag", "")

        if response and "je n'ai pas encore appris" not in response.lower() and response not in responses:
            responses.append(response)

        if score > best_score:
            best_score = score
            best_tag = tag
            best_fallback_response = response

    final_response = "\n".join(responses).strip() if responses else best_fallback_response


    result = {
        "response": final_response,
        "score": best_score,
        "tag": best_tag
    }

    user_token = data.get("user_token", "unknown")
    base_text = next((entry["response"] for entry in database if entry.get("tag") == "presentation_sylvain_regnier"), "")
    print(f"🔸 Texte de base pour extraction : {base_text}")

    # --- Détection frère / sœur ---
    if (re.search(r"\b(fr[eè]re|soeur|sœur)s?\b", raw_original.lower())
        and result["tag"] not in ["extraction_frere_soeur"]
        and (result["score"] is None or result["score"] < 0.85)):

        print("🟡 Détection frere/soeur (contrôlée)")
        match_frere = re.search(r"(?:j'ai|ai)?\s*(un|\d+)\s*(fr[eè]re)s?", base_text, re.IGNORECASE)
        match_soeur = re.search(r"(?:j'ai|ai)?\s*(une|un|\d+)\s*(sœur|soeur)s?", base_text, re.IGNORECASE)

        if match_frere:
            val = match_frere.group(1)
            txt = "un frère." if val == "1" or val.lower() == "un" else f"{val} frères."
            result["response"] = f"J'ai {txt}"
            result["tag"] = "extraction_frere_soeur"
            result["score"] = None
            print(f"✅ Frère(s) détecté(s) : {txt}")
        elif match_soeur:
            val = match_soeur.group(1)
            txt = "une sœur." if val == "1" or val.lower() == "une" else f"{val} sœurs."
            result["response"] = f"J'ai {txt}"
            result["tag"] = "extraction_frere_soeur"
            result["score"] = None
            print(f"✅ Sœur(s) détectée(s) : {txt}")

    # --- Détection âge personnel / fille ---
    if (re.search(r"\b(?:âge|age|\d+\s*ans)\b", raw_original.lower())
        and result["tag"] not in ["presentation_sylvain_regnier", "extraction_age", "extraction_age_fille"]
        and (result["score"] is None or result["score"] < 0.85)):

        print("🟡 Détection possible d'âge")
        if "fille" in raw_original.lower():
            match = re.search(r"fille (?:de|a)\s*(\d+)\s*ans", base_text, re.IGNORECASE)
            if match:
                daughter_age = match.group(1)
                result["response"] = f"Ma fille a {daughter_age} ans."
                result["score"] = None
                result["tag"] = "extraction_age_fille"
                print(f"✅ Âge fille détecté : {daughter_age}")
        else:
            my_age = extract_age(base_text)
            if my_age:
                result["response"] = f"J'ai {my_age} ans."
                result["score"] = None
                result["tag"] = "extraction_age"
                print(f"✅ Âge personnel détecté : {my_age}")

    print(f"📝 Sauvegarde du message avec réponse : {result['response']}")
    save_chat_message(user_token, raw, result["response"], result["score"], result["tag"])
    print("✅ Réponse renvoyée")
    return result

# 👉 Cette fonction traite un message complet
def test_handle_message(message: str):
    print("🔹 Message reçu :", message)

    # Étape 1 : découpe en sous-questions sur le message brut
    subquestions = split_into_subquestions(message)
    print("🔍 Sous-questions détectées :", subquestions)

    all_results = []

    for subq in subquestions:
        # Étape 2 : normalise CHAQUE sous-question
        normalized = normalize_text(subq)
        print("→ Texte normalisé :", normalized)

        # Étape 3 : classification
        vector = vectorizer.transform([normalized])
        proba = classifier.predict_proba(vector)[0]
        predicted_tag = classifier.classes_[proba.argmax()]
        confidence = max(proba)

        print(f"🔮 Classifieur LogisticRegression → {predicted_tag} avec confiance {confidence:.2f}")
        all_results.append({
            "subquestion": subq,
            "normalized": normalized,
            "tag": predicted_tag,
            "confidence": confidence,
            "probas": dict(zip(classifier.classes_, proba))
        })

    return all_results




def find_best_response(user_input):
    user_input = user_input.strip().lower()
    normalized_input = normalize_text(user_input)
# 🔍 Matching exact dans les patterns (avant toute logique NLP)
    for entry in database:
        if normalize_text(entry["question"]) == normalized_input:
            print("✅ Matching exact trouvé dans les patterns → réponse prioritaire")
            return {
                "response": entry["response"],
                "score": 1.0,
                "doubt": {},
                "tag": entry["tag"]
            }

# 🔹 Salutations détectées manuellement
    salutations = {"bonjour", "salut", "yo", "hey", "hello", "coucou", "wesh", "plop", "hi", "bien le bonjour"}
    if user_input in salutations:
        print("🔸 Salutation reconnue directement sans NLP")
        return {
            "response": "Bonjour, bienvenue sur mon ChatBot de pré-entretient",
            "score": 1.0,
            "doubt": {},
            "tag": "salutation"
        }

    

    # 🏢 Tags liés aux entreprises
    ENTREPRISE_TAGS = {
        "conforama": "experience_conforama",
        "darty": "experience_darty",
        "internity": "experience_internity",
        "sncf": "experience_sncf",
        "securifrance": "experience_securifrance",
        "brice": "experience_brice",
        "sofi informatique": "experience_sofi_informatique"
    }

    # 🔍 Embedding utilisateur
    user_emb = model.encode(user_input).astype('float32')
    user_norm = user_emb / np.linalg.norm(user_emb)
    user_norm = user_norm.reshape(1, -1)

    # 🧠 Classification (LogisticRegression)
    proba = clf.predict_proba(user_emb.reshape(1, -1))[0]
    predicted_tag = clf.classes_[np.argmax(proba)]
    doubt = {tag: float(prob) for tag, prob in zip(clf.classes_, proba)}
    print(f"🔮 Classifieur LogisticRegression → {predicted_tag} avec confiance {max(proba):.2f}")
    print("📊 Distribution des probabilités:", doubt)

    # 🎯 Recherche dans les questions du tag prédit
    filtered_indices = [i for i, entry in enumerate(database) if entry["tag"] == predicted_tag]
    best_match_score = 0.0
    best_match_entry = None

    if filtered_indices:
        similarities = [np.dot(questions_embeddings_norm[i], user_norm[0]) for i in filtered_indices]
        best_filtered_idx = np.argmax(similarities)
        best_match_index = filtered_indices[best_filtered_idx]
        best_match_score = similarities[best_filtered_idx]
        best_match_entry = database[best_match_index]
        print(f"📈 Score dans le tag '{predicted_tag}': {best_match_score:.2f}")

# 🔁 Fallback global FAISS
    D, I = global_index.search(user_norm, 1)
    faiss_index = I[0][0]
    faiss_score = D[0][0]
    faiss_entry = database[faiss_index]
    # 🩹 Forçage si mot-clé entreprise détecté
    for keyword, tag in ENTREPRISE_TAGS.items():
        if keyword in user_input:
            print(f"🔁 Forçage direct tag '{tag}' à cause du mot-clé '{keyword}'")
            for entry in database:
                if entry["tag"] == tag:
                    return {
                        "response": entry["response"],
                        "score": 0.99,
                        "doubt": doubt,
                        "tag": tag
                    }
# 💡 On compare les deux résultats et garde le meilleur
    if faiss_score > best_match_score:
        print("✅ Meilleur score FAISS global, réponse prioritaire")
        return {
            "response": faiss_entry["response"],
            "score": float(faiss_score),
            "doubt": doubt,
            "tag": faiss_entry["tag"]
        }
    elif best_match_entry:
        return {
            "response": best_match_entry["response"],
            "score": float(best_match_score),
            "doubt": doubt,
            "tag": best_match_entry["tag"]
        }





    # ✅ Fallback FAISS normal
    threshold = 0.5 if len(user_input.split()) <= 2 else 0.6
    if faiss_score > threshold:
        return {
            "response": database[faiss_index]["response"],
            "score": float(faiss_score),
            "doubt": doubt,
            "tag": database[faiss_index]["tag"]
        }

    # ❌ Dernier recours
    return {
        "response": "Désolé, je n'ai pas encore appris.",
        "score": float(faiss_score),
        "doubt": doubt,
        "tag": predicted_tag
    }



def save_chat_message(user_token, question, response, score, tag):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = {"user_token": user_token, "timestamp": timestamp, "question": question, "response": response, "score": score, "tag": tag}
    fname = session_files.setdefault(user_token, f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_token}.json")
    path = os.path.join(CHAT_HISTORY_DIR, fname)
    history = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f)
    history.append(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def test_top_k_intents(user_input, k=5):
    user_emb = model.encode(user_input).astype('float32')
    user_norm = user_emb / np.linalg.norm(user_emb)
    scores = []
    for i, emb in enumerate(questions_embeddings_norm):
        sim = np.dot(emb, user_norm)
        scores.append((i, sim))
    top_k = sorted(scores, key=lambda x: x[1], reverse=True)[:k]
    print(f"\n🔍 Top {k} intents pour : '{user_input}'\n")
    for idx, sim in top_k:
        print(f"  {sim:.4f} | tag: {database[idx]['tag']} | q: {database[idx]['question']}")

# 🔁 FORCING training and saving even if no new entries detected
X = [entry["question"] for entry in database]
y = [entry["tag"] for entry in database]

vectorizer = TfidfVectorizer()
X_vect = vectorizer.fit_transform(X)

classifier = LogisticRegression(max_iter=1000)
classifier.fit(X_vect, y)

# 💾 Sauvegarde
joblib.dump(vectorizer, "vectorizer.joblib")
joblib.dump(classifier, "classifier.joblib")



test_top_k_intents("C’est quoi pour toi une base de données relationnelle")

# Pour démarrer le serveur, exécute par exemple :
# uvicorn testserver:app --reload

