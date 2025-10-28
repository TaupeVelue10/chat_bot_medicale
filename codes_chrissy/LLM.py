import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Récupérer la clé API
api_key = os.getenv("HF_API_KEY")

if not api_key:
    raise ValueError(" Clé API Hugging Face introuvable ! Vérifie ton fichier .env")

# Définir la variable d’environnement pour Hugging Face
os.environ["HUGGINGFACEHUB_API_TOKEN"] = api_key

# Initialiser le client API
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    token=api_key
)

# Exemple d’appel
prompt = "Explique moi le rôle de l'adrénaline dans le corps humain."
print("⏳ Envoi de la requête à l'API...")

response = client.chat_completion(
    messages=[{"role": "user", "content": prompt}],
    max_tokens=150
)

print(" Réponse :", response.choices[0].message["content"])
