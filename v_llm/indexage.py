import chromadb
import json
from chromadb.utils import embedding_functions

def create_index(guidelines_file="guidelines.json", collection_name="guidelines_collection"):
    client = chromadb.Client()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )

    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    with open(guidelines_file, "r", encoding="utf-8") as f:
        data = json.load(f)["guidelines"]

    for entry in data:
        collection.add(
            ids=[entry["id"]],
            documents=[entry["texte"]],
            metadatas=[{"motif": entry["motif"], "source": entry["source"]}]
        )

    return collection
