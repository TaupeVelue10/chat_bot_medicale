import requests
import chromadb

def get_collection(db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_collection(collection_name)

def query_ollama(prompt, model="mistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

def rag_query(user_input, collection):
    results = collection.query(
        query_texts=[user_input],
        n_results=3
    )

    docs = results["documents"][0]
    metas = results.get("metadatas", [[]])[0]  # safe fallback

    context = "\n".join(
        f"- {doc} (source: {meta.get('source', 'inconnue')}, motif: {meta.get('motif', 'inconnu')})"
        if isinstance(meta, dict) else f"- {doc}"
        for doc, meta in zip(docs, metas)
    )

    prompt = f"""
    Tu es un assistant médical.
    Question du médecin : {user_input}
    Voici des extraits des recommandations officielles :
    {context}
    Réponds uniquement en t'appuyant sur ces recommandations.
    """

    return query_ollama(prompt)


