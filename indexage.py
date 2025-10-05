import chromadb
import json

def create_index(guidelines_file="guidelines.json", db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # Option 1: Utiliser un modèle d'embedding médical si disponible
    # from chromadb.utils import embedding_functions
    # medical_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="emilyalsentzer/Bio_ClinicalBERT")
    # collection = chroma_client.get_or_create_collection(collection_name, embedding_function=medical_ef)
    
    # Option 2: Pour l'instant, utiliser le modèle par défaut optimisé
    collection = chroma_client.get_or_create_collection(collection_name)

    docs = []
    with open(guidelines_file, "r") as f:
        data = json.load(f)
        guidelines = data["guidelines"]

    for g in guidelines:
        docs.append({
            "id": g["id"],
            "text": g["texte"],
            "motif": g["motif"],
            "source": g["source"]
        })

    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[{"motif": d["motif"], "source": d["source"]} for d in docs]
    )

    print(f"✅ Indexation terminée ({len(docs)} documents).")
    return collection

if __name__ == "__main__":
    create_index()

