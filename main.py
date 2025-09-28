from indexage import create_index
from ollama import get_collection, rag_query

# Étape 1 : Indexer guidelines (création ou mise à jour)
create_index("guidelines.txt")

# Étape 2 : Charger la collection
collection = get_collection()

# Étape 3 : Exemple de question
question = "Patiente 45 ans, céphalées depuis 2 semaines, pas de déficit neurologique."
print("❓ Question :", question)
print("🤖 Réponse :", rag_query(question, collection))
