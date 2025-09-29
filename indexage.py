import chromadb
import json

def create_index(guidelines_file="guidelines.json", db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(collection_name)

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

    print(f"✅ Indexation terminée ({len(docs)} documents).")
    return collection

docs = []
with open("guidelines.txt", "r") as f:
    for i, line in enumerate(f):
        if line.strip():
            docs.append({"id": str(i), "text": line.strip()})

