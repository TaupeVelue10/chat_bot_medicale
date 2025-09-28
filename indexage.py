import chromadb

def create_index(guidelines_file="guidelines.txt", db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    collection = chroma_client.get_or_create_collection(collection_name)

    docs = []
    with open(guidelines_file, "r") as f:
        for i, line in enumerate(f):
            if line.strip():
                docs.append({"id": str(i), "text": line.strip()})

    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs]
    )

    print(f"✅ Indexation terminée ({len(docs)} documents).")
    return collection
docs = []
with open("guidelines.txt", "r") as f:
    for i, line in enumerate(f):
        if line.strip():
            docs.append({"id": str(i), "text": line.strip()})

