from typing import Any
from indexage import create_index

# ---- If using Hugging Face transformers ----
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# --- Load local HuggingFace cached model automatically ---
MODEL_NAME = "BioMistral/BioMistral-7B"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    dtype=torch.bfloat16,
    device_map="auto"
)

def _normalize_response(resp: Any) -> str:
    """Normalize the model response into a string."""
    if resp is None:
        return ""
    if isinstance(resp, dict):
        return str(resp.get("response") or resp.get("message", {}).get("content") or resp)
    if hasattr(resp, "response"):
        return str(getattr(resp, "response"))
    if hasattr(resp, "message"):
        msg = getattr(resp, "message")
        if hasattr(msg, "content"):
            return str(msg.content)
        if isinstance(msg, dict):
            return str(msg.get("content", msg))
    if hasattr(resp, "content"):
        return str(getattr(resp, "content"))
    return str(resp)


def _call_local_model(prompt: str, max_new_tokens: int = 200) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")
    for k,v in inputs.items ():
        inputs [k]= v.to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text.strip()


def rag_biomistral_query(question: str, collection) -> str:
    """Query local RAG context and generate response using the local model."""

    # 1 - retrieve context from ChromaDB
    results = collection.query(query_texts=[question], n_results=3)
    context = "\n".join(
        f"- {doc} (source: {meta.get('source')}, motif: {meta.get('motif')})"
        for doc, meta in zip(results['documents'][0], results['metadatas'][0])
    )

    # 2 - build the prompt
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
4) Si suffisant → DONNE une recommandation concise (commence par "Recommandation:").
5) RÉPONDRE UNIQUEMENT en FRANÇAIS.
6) RÉPONDRE SUR UNE SEULE LIGNE, sans préambule ni explication supplémentaire.
"""

    # 3 - call the local model
    text = _call_local_model(prompt)

    # 4 - validate format
    prefixes = ("Pour préciser:", "Recommandation:")
    if any(text.startswith(p) for p in prefixes):
        return text

    # fallback reminder
    reminder = prompt + "\n\nRAPPEL: Commence ta réponse PAR soit 'Pour préciser:' soit 'Recommandation:' et DONNE UNE SEULE LIGNE."
    text2 = _call_local_model(reminder)
    if any(text2.startswith(p) for p in prefixes):
        return text2

    # hardcoded fallback if format fails
    return (
        "Pour préciser: Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ? | "
        "Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ? | "
        "La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?"
    )
