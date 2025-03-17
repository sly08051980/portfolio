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
from datetime import datetime
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

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
                    response = intent.get("responses", ["Je ne sais pas."])[0]
              
                    for pattern in intent.get("patterns", []):
                        database.append({
                            "question": pattern,
                            "response": response
                        })
                  
                    for alias in intent.get("aliases", []):
                        database.append({
                            "question": alias,
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
    questions_embeddings = [model.encode(q["question"], convert_to_tensor=False) for q in tqdm(database)]
    np.save(EMBEDDINGS_FILE, np.array(questions_embeddings))
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4)

gc.collect()

print("\n✅ Serveur prêt, lancement de l'API...")


app = FastAPI(root_path="/chatbot")

app.mount("/static", StaticFiles(directory="static"), name="static")

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
    user_input = data.get("message", "")
    user_token = data.get("user_token", "unknown")

    if not user_input:
        return {"response": "Veuillez entrer une question valide."}

 
    result = find_best_response(user_input)
    response_text = result["response"]
    score = result["score"]


    save_chat_message(user_token, user_input, response_text, score)

    return {"question": user_input, "response": response_text, "score": score}

def save_chat_message(user_token, question, response, score):

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chat_data = {
        "user_token": user_token,
        "timestamp": timestamp,
        "question": question,
        "response": response,
        "score": score
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
            json.dump(chat_history, f, indent=4)

def find_best_response(user_input):
    if not database:
        return {"response": "Aucune donnée disponible.", "score": 0.0}

    user_embedding = model.encode(user_input, convert_to_tensor=False)
   
    scores = util.pytorch_cos_sim(np.array(user_embedding), np.array(questions_embeddings))[0]
    best_match_index = scores.argmax().item()
    best_match_score = scores[best_match_index].item()

   
    if best_match_score > 0.6:
        return {"response": database[best_match_index]["response"], "score": best_match_score}
    else:
        return {"response": "Désolé, réponse inconnue.", "score": best_match_score}

# 🚀 Démarrer le serveur avec :
# uvicorn server:app --reload
