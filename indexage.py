import chromadb
import json

# vectorisation du fichier guidelines
def create_index(guidelines_file="guidelines.json", db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # Recréer la collection proprement à chaque fois
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass  # La collection n'existe pas encore
    
    collection = chroma_client.create_collection(collection_name)

    docs = []
    with open(guidelines_file, "r") as f:
        guidelines = json.load(f)

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

    return collection

