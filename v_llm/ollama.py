"""
Module providing RAG-based query function for BioMistral.
Uses the installed ollama package safely by importing at runtime.
"""
import importlib
import sys
from pathlib import Path


def _import_installed_ollama():
    """Import the installed ollama package from site-packages."""
    project_dir = str(Path(__file__).resolve().parent)
    removed = False
    if project_dir in sys.path:
        sys.path.remove(project_dir)
        removed = True
    try:
        mod = importlib.import_module('ollama')
        mod = importlib.reload(mod)
        return mod
    finally:
        if removed:
            sys.path.insert(0, project_dir)


def rag_biomistral_query(question: str, collection):
    """
    Interroge BioMistral avec un prompt cadré:
    - Donne les guidelines pertinentes
    - Interdit les inventions de contexte
    - Encourage à poser des questions si besoin
    """

    # Étape 1: récupération du contexte depuis ChromaDB
    results = collection.query(query_texts=[question], n_results=3)

    context = "\n".join(
        f"- {doc} (source: {meta['source']}, motif: {meta['motif']})"
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    )

    # Étape 2: prompt BioMistral  
    prompt = f"""Contexte médical:
{context}

Question: Pour ce patient ({question}), dois-je demander une imagerie? Si oui laquelle et pourquoi? Si je n'ai pas assez d'informations, quelles questions poser?

Réponse:"""

    # Étape 3: appel du modèle BioMistral
    ollama = _import_installed_ollama()
    response = ollama.generate(
        model="biomistral:latest",
        prompt=prompt
    )
    return response["response"].strip()
