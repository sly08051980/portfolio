import json
import os
import nltk
import numpy as np
from sentence_transformers import SentenceTransformer, util
from fastapi import FastAPI, Request
from pydantic import BaseModel
from tqdm import tqdm
import gc
from fastapi.staticfiles import StaticFiles

# 📌 Fichiers d'apprentissage
EMBEDDINGS_FILE = "embeddings.npy"
QUESTIONS_FILE = "questions.json"
CHAT_HISTORY_FILE = "chat_history.json"

# Télécharger les données nécessaires de NLTK
nltk.download('punkt')

# 📥 Chargement du modèle NLP
print("📥 Chargement du modèle NLP...")
try:
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
except:
    print("⚠️ Erreur avec 'paraphrase-MiniLM-L6-v2', tentative avec un modèle plus léger...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

# 📌 Chargement des fichiers JSON contenant les questions
json_files = [
    "intents/css.json",
    "intents/employeur.json",
    "intents/futur.json",
    "intents/html.json",
    "intents/php.json",
    "intents/programmation.json",
    "intents/parcours.json",
    "intents/professionnel.json",
    "intents/personnel.json",
    "intents/politesses.json",
    "intents/recherche.json",
    "intents/vieentreprise.json",
    "intents/question.json"
]

print("🔍 Vérification des fichiers JSON...")
database = []
for file_path in json_files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                if "intents" in data and isinstance(data["intents"], list):
                    for intent in data["intents"]:
                        for pattern in intent.get("patterns", []):
                            database.append({
                                "question": pattern,
                                "response": intent.get("responses", ["Je ne sais pas."])[0]
                            })
                else:
                    print(f"⚠️ Problème de format dans {file_path}")
            except json.JSONDecodeError:
                print(f"❌ Erreur : {file_path} est un fichier JSON invalide")

print(f"\n🔍 {len(database)} questions chargées.")

# 🛠 Vérification si les embeddings existent
if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(QUESTIONS_FILE):
    print(f"\n📂 Chargement des embeddings et des questions depuis {EMBEDDINGS_FILE} et {QUESTIONS_FILE}...")
    questions_embeddings = np.load(EMBEDDINGS_FILE)

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        database = json.load(f)

    print(f"✅ {len(database)} questions et embeddings chargés.")
else:
    print("\n🚀 Aucune sauvegarde trouvée, encodage des données...")
    progress_bar = tqdm(total=len(database), desc="Encodage", dynamic_ncols=True)
    questions_embeddings = []
    for question in database:
        embedding = model.encode(question["question"], convert_to_tensor=False)
        questions_embeddings.append(embedding)
        progress_bar.update(1)
    progress_bar.close()

    np.save(EMBEDDINGS_FILE, np.array(questions_embeddings))
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4, ensure_ascii=False)

    gc.collect()

print("\n✅ Tout est prêt, lancement du serveur API...")

# 🚀 Création de l'API FastAPI
app = FastAPI()

# 🎯 Servir les fichiers statiques (HTML, CV)
app.mount("/static", StaticFiles(directory="static"), name="static")

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur le Chatbot d'entretien professionnel"}

@app.post("/handle_message")
async def handle_message(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    user_token = data.get("user_token", "unknown")

    if not user_input:
        return {"response": "Veuillez entrer une question valide."}

    response = find_best_response(user_input)
    
    save_chat_message(user_token, user_input, response)

    return {"question": user_input, "response": response}

# 🔥 Sauvegarde en temps réel des conversations
def save_chat_message(user_token, question, response):
    chat_data = {"user_token": user_token, "question": question, "response": response}
    if not os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([chat_data], f, indent=4, ensure_ascii=False)
    else:
        with open(CHAT_HISTORY_FILE, "r+", encoding="utf-8") as f:
            chat_history = json.load(f)
            chat_history.append(chat_data)
            f.seek(0)
            json.dump(chat_history, f, indent=4, ensure_ascii=False)

def find_best_response(user_input):
    if not database:
        return "Aucune donnée disponible pour répondre."

    user_embedding = model.encode(user_input, convert_to_tensor=False)
    scores = util.pytorch_cos_sim(np.array(user_embedding), np.array(questions_embeddings))[0]
    best_match_index = scores.argmax().item()
    best_match_score = scores[best_match_index].item()

    if best_match_score > 0.6:
        return database[best_match_index]["response"]
    else:
        return "Désolé, je n'ai pas trouvé de réponse précise à cette question."

# 🚀 Démarrer le serveur avec :
# uvicorn server:app --reload
