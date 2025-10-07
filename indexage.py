import chromadb
import json

def create_index(guidelines_file="guidelines.json", db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    #1: Utiliser BlueBERT - Modèle médical le plus performant (50% pertinence)
    from chromadb.utils import embedding_functions
    medical_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="bionlp/bluebert_pubmed_mimic_uncased_L-12_H-768_A-12"
    )
    collection = chroma_client.get_or_create_collection(collection_name, embedding_function=medical_ef)
    
    #2: Alternative modèle par défaut (désactivé)
    # collection = chroma_client.get_or_create_collection(collection_name)

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

