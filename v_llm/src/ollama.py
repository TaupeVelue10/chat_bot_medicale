
"""
ollama.py - RAG query helper for BioMistral via the installed Ollama SDK.

This module imports the installed `ollama` package at runtime (removing the
workspace folder from sys.path while importing) to avoid accidental shadowing
by a local file named `ollama.py`.

Function provided:
- rag_biomistral_query(question: str, collection) -> str

"""
from pathlib import Path
import importlib
import sys
from typing import Any


def _import_installed_ollama():
    """Import and return the installed `ollama` package from site-packages.

    Temporarily removes the project directory from sys.path so local files do not
    shadow the installed package.
    """
    project_dir = str(Path(__file__).resolve().parent)
    removed = False
    if project_dir in sys.path:
        sys.path.remove(project_dir)
        removed = True
    try:
        mod = importlib.import_module('ollama')
        return importlib.reload(mod)
    finally:
        if removed:
            sys.path.insert(0, project_dir)


def _normalize_response(resp: Any) -> str:
    """Return a plain-text assistant response for several possible SDK shapes."""
    if resp is None:
        return ""
    if isinstance(resp, dict):
        # common keys
        return str(resp.get('response') or resp.get('message', {}).get('content') or resp)
    if hasattr(resp, 'response'):
        return str(getattr(resp, 'response'))
    if hasattr(resp, 'message'):
        msg = getattr(resp, 'message')
        if hasattr(msg, 'content'):
            return str(msg.content)
        if isinstance(msg, dict):
            return str(msg.get('content', msg))
    if hasattr(resp, 'content'):
        return str(getattr(resp, 'content'))
    return str(resp)


def rag_biomistral_query(question: str, collection, temperature: float = 0.0) -> str:
    """Run a RAG query: pull context from ChromaDB, build a strict prompt and call BioMistral.

    - If required decision criteria are missing in the case, the model MUST ask
      clarifying questions (begin response with "Pour préciser:").
    - If information is sufficient, the model MUST give a short recommendation
      beginning with "Recommandation:" and a brief justification tied to the
      supplied guidelines.
    """

    # Step 1: retrieve context from ChromaDB
    results = collection.query(query_texts=[question], n_results=3)
    context = "\n".join(
        f"- {doc} (source: {meta.get('source')}, motif: {meta.get('motif')})"
        for doc, meta in zip(results['documents'][0], results['metadatas'][0])
    )

    # Step 2: build a strict prompt that forces questions when info is missing
    prompt = f"""GUIDELINES (source: local RAG):
{context}

CAS CLINIQUE:
{question}

FORMAT attendu (NE PAS répéter ces lignes dans la réponse):
- Si information MANQUANTE → la réponse DOIT COMMENCER PAR exactement: Pour préciser: [questions]
- Si information SUFFISANTE → la réponse DOIT COMMENCER PAR exactement: Recommandation: [examen — urgence — justification courte]

INSTRUCTIONS STRICTES (FR) — RÉPONDRE SUR UNE SEULE LIGNE:
1) Tu n'utilises QUE les informations écrites dans "CAS CLINIQUE". Tout non écrit est MANQUANT.
2) Vérifie: signes d'alarme (céphalée brutale, déficit neurologique, fièvre), âge >50 ans, durée, antécédents (cancer, immunodépression), grossesse, changement de pattern.
3) Si des informations manquent → TU DOIS POSER EXACTEMENT CES 3 QUESTIONS, dans CET ORDRE, sur UNE SEULE LIGNE, précédées de 'Pour préciser:' et séparées par ' | ' :
     - Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ?
     - Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ?
     - La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?
     Exemple attendu si manque d'info :
     Pour préciser: Depuis quand et quel caractère ... ? | Y a‑t‑il fièvre ... ? | La patiente est‑elle enceinte ... ?
4) Si suffisant → DONNE une recommandation concise (commence par "Recommandation:").
8) N'UTILISEZ LE MOT « urgence » (ou « en urgence ») QUE SI le CAS CLINIQUE CONTIENT AU MOINS UN DES SIGNES D'ALERTE LISTÉS (brutal, déficit neurologique, convulsions, fièvre, traumatisme). Si doute, choisissez la formulation la moins urgente (préférez « surveiller / consultation rapide » à « en urgence »).
5) RÉPONDRE UNIQUEMENT en FRANÇAIS.
6) RÉPONDRE SUR UNE SEULE LIGNE, sans préambule ni explication supplémentaire.
7) NE PAS fournir d'autres questions ni d'exemples supplémentaires.

SI TU NE PEUX PAS RESPECTER LE FORMAT CI-DESSUS, RÉPONDS EXCLUSIVEMENT AVEC UN OBJET JSON VALIDE, PAR EXEMPLE:
    {{"type": "clarify", "questions": ["q1", "q2", "q3"]}}
ou
    {{"type": "recommendation", "text": "..."}}
Le JSON doit être la SEULE chose dans la réponse (aucun autre texte).

RÉPONDS maintenant en FRANÇAIS.
"""



    # Step 3: import installed ollama SDK and call the model
    ollama = _import_installed_ollama()

    # Prefer generate, fallback to chat/create
    def _call_model(p: str, temp: float = 0.0):
        # Try to pass the temperature when calling the SDK; fall back to calls without it if unsupported.
        # Ollama's Python API supports a temperature param for many ops; we attempt to include it.
        try:
            if hasattr(ollama, 'generate'):
                return ollama.generate(model='biomistral-clinical:latest', prompt=p, temperature=temp)
            if hasattr(ollama, 'chat'):
                return ollama.chat(model='biomistral-clinical:latest', messages=[{'role': 'user', 'content': p}], temperature=temp)
            if hasattr(ollama, 'create'):
                return ollama.create(model='biomistral-clinical:latest', prompt=p, temperature=temp)
        except TypeError:
            # some SDK versions may not accept temperature; retry without it
            pass
        # retry without temperature
        if hasattr(ollama, 'generate'):
            return ollama.generate(model='biomistral-clinical:latest', prompt=p)
        if hasattr(ollama, 'chat'):
            return ollama.chat(model='biomistral-clinical:latest', messages=[{'role': 'user', 'content': p}])
        if hasattr(ollama, 'create'):
            return ollama.create(model='biomistral-clinical:latest', prompt=p)
        raise RuntimeError('Installed ollama package does not expose generate/chat/create API')

    # Call the model and return its response
    resp = _call_model(prompt, temp=temperature)
    text = _normalize_response(resp).strip()

    # Check if output follows expected format
    prefixes = ('Pour préciser:', 'Recommandation:')
    if any(text.startswith(p) for p in prefixes):
        return text

    # Retry once with explicit reminder if format not respected
    reminder = prompt + "\n\nRAPPEL: Commence ta réponse PAR soit 'Pour préciser:' soit 'Recommandation:' et DONNE UNE SEULE LIGNE."
    resp2 = _call_model(reminder, temp=temperature)
    text2 = _normalize_response(resp2).strip()
    if any(text2.startswith(p) for p in prefixes):
        return text2

    # Fallback: return safe clarification request
    return ("Pour préciser: Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ? | "
            "Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ? | "
            "La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?")

