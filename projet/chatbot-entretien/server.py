import json
import os
import nltk
import numpy as np
import faiss  
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, Request
from pydantic import BaseModel
from tqdm import tqdm
import gc
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from sklearn.linear_model import LogisticRegression  
from fastapi.responses import HTMLResponse


print(f"📂 Répertoire actuel : {os.getcwd()}")

EMBEDDINGS_FILE = "embeddings.npy"
QUESTIONS_FILE = "questions.json"

CHAT_HISTORY_DIR = "chat_histories"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)

session_files = {}

nltk.download('punkt')


print("📥 Chargement du modèle NLP...")
try:
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
except Exception as e:
    model = SentenceTransformer('all-MiniLM-L6-v2')


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
            data = json.load(file)
            if "intents" in data and isinstance(data["intents"], list):
                for intent in data["intents"]:
                   
                    tag = str(intent.get("tag", "")).lower()
                    context_set = str(intent.get("context_set", "")).lower()
                    aliases = [str(alias).lower() for alias in intent.get("aliases", [])]
                    patterns = [str(pattern).lower() for pattern in intent.get("patterns", [])]
                    responses = [str(r).lower() for r in intent.get("responses", ["je ne sais pas."])]
                    response = responses[0]
                   
                    questions = patterns + aliases
         
                    for question in questions:
                        database.append({
                            "tag": tag,
                            "context_set": context_set,
                            "aliases": aliases,
                            "question": str(question).lower(),
                            "response": response
                        })

print(f"\n🔍 {len(database)} questions chargées.")


if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(QUESTIONS_FILE):
    print(f"\n📂 Chargement des embeddings depuis {EMBEDDINGS_FILE}...")
    questions_embeddings = np.load(EMBEDDINGS_FILE)
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        database = json.load(f)
else:
    print("\n🚀 Encodage des données en cours...")
    questions_embeddings = []
    for q in tqdm(database):
     
        text_to_encode = f"{q['question']} [tag: {q['tag']}] [context: {q['context_set']}] [aliases: {', '.join(q['aliases'])}]".lower()
        embedding = model.encode(text_to_encode, convert_to_tensor=False)
        questions_embeddings.append(embedding)
    questions_embeddings = np.array(questions_embeddings).astype('float32')
    np.save(EMBEDDINGS_FILE, questions_embeddings)
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4, ensure_ascii=False)


norms = np.linalg.norm(questions_embeddings, axis=1, keepdims=True)
questions_embeddings_norm = questions_embeddings / norms


d = questions_embeddings_norm.shape[1]  
global_index = faiss.IndexFlatIP(d)
global_index.add(questions_embeddings_norm)
print(f"\nFAISS index global créé avec {global_index.ntotal} entrées.")


tags = [entry["tag"] for entry in database]
clf = LogisticRegression(max_iter=1000)
clf.fit(questions_embeddings, tags)

gc.collect()

print("\n✅ Serveur prêt, lancement de l'API...")


app = FastAPI()

app.mount("/chatbot/static", StaticFiles(directory="/var/www/regniersylvain/projet/chatbot-entretien/static"), name="static")
app.mount("/documents", StaticFiles(directory="/var/www/regniersylvain/projet/chatbot-entretien/documents"), name="documents")



class QuestionRequest(BaseModel):
    question: str
    user_token: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read(), status_code=200)

@app.post("/handle_message")
async def handle_message(request: Request):
    data = await request.json()
   
    user_input = data.get("message", "").lower()
    user_token = data.get("user_token", "unknown")
    if not user_input:
        return {"response": "Veuillez entrer une question valide."}
    result = find_best_response(user_input)
    response_text = result["response"]
    score = result["score"]
    tag = result.get("tag", "")
    save_chat_message(user_token, user_input, response_text, score, tag)
    return {"question": user_input, "response": response_text, "score": score, "tag": tag, "doubt": result.get("doubt", {})}

def save_chat_message(user_token, question, response, score, tag):

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chat_data = {
        "user_token": user_token,
        "timestamp": timestamp,
        "question": question,
        "response": response,
        "score": score,
        "tag": tag 
    }
    
    if user_token not in session_files:
        file_name = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_token}.json"
        session_files[user_token] = file_name
    else:
        file_name = session_files[user_token]

    file_path = os.path.join(CHAT_HISTORY_DIR, file_name)
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([chat_data], f, indent=4)
    else:
        with open(file_path, "r+", encoding="utf-8") as f:
            try:
                chat_history = json.load(f)
            except json.JSONDecodeError:
                chat_history = []
            chat_history.append(chat_data)
            f.seek(0)
            json.dump(chat_history, f, indent=4, ensure_ascii=False)

def find_best_response(user_input):
    if not database:
        return {"response": "Aucune donnée disponible.", "score": 0.0, "doubt": {}, "tag": ""}

    user_embedding = model.encode(user_input, convert_to_tensor=False)
    user_embedding = np.array(user_embedding, dtype='float32')
    
    user_embedding_norm = user_embedding / np.linalg.norm(user_embedding)
    user_embedding_norm = user_embedding_norm.reshape(1, -1)
    
    proba = clf.predict_proba(user_embedding.reshape(1, -1))[0]
    predicted_tag = clf.classes_[np.argmax(proba)]
    doubt = {tag: float(prob) for tag, prob in zip(clf.classes_, proba)}
    print(f"Tag prédit: {predicted_tag} avec confiance {max(proba):.2f}")
    print("Distribution des probabilités:", doubt)
    

    filtered_indices = [i for i, entry in enumerate(database) if entry["tag"] == predicted_tag]
    
    if filtered_indices:
        similarities = []
        for i in filtered_indices:
            sim = np.dot(questions_embeddings_norm[i], user_embedding_norm[0])
            similarities.append(sim)
        best_filtered_idx = np.argmax(similarities)
        best_match_index = filtered_indices[best_filtered_idx]
        best_match_score = similarities[best_filtered_idx]
        print(f"Score dans le sous-ensemble '{predicted_tag}': {best_match_score:.2f}")
        if best_match_score > 0.55:  
            return {"response": database[best_match_index]["response"],
                    "score": float(best_match_score),
                    "doubt": doubt,
                    "tag": predicted_tag}
    
 
    k = 1
    D, I = global_index.search(user_embedding_norm, k)
    best_match_index = I[0][0]
    best_match_score = D[0][0]
    print(f"Score global: {best_match_score:.2f}")
    if best_match_score > 0.6:
        return {"response": database[best_match_index]["response"],
                "score": float(best_match_score),
                "doubt": doubt,
                "tag": predicted_tag}
    else:
        return {"response": "Désolé, je n'ai pas encore appris.",
                "score": float(best_match_score),
                "doubt": doubt,
                "tag": predicted_tag}

# Pour démarrer le serveur
# uvicorn server:app --reload
