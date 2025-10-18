
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

    # Quick deterministic pre-check: if the clinical case is very short or lacks
    # key clinical tokens, force clarifying questions without calling the model.
    def _needs_clarification(case_text: str) -> bool:
        ct = case_text.lower()
        # very short descriptions (less than 30 chars) or only "patient X ans, céphalées"
        if len(ct) < 30:
            return True
        # check if it's a minimal case with no detail beyond age+symptom
        # minimal pattern: contains "patient" or age, and main symptom, but nothing else
        has_basic = ('patient' in ct or 'patiente' in ct) and ('céphalée' in ct or 'cephalee' in ct)
        if has_basic and len(ct) < 50:
            # very likely just "patient X ans, céphalées" → needs clarification
            return True
        
        # If it contains multiple key clinical tokens (onset, character, red flags, pregnancy status),
        # then it's well-documented and doesn't need pre-clarification.
        tokens = ['depuis', 'brutal', 'brutale', 'intense', 'progress', 'fièvre', 'fievre', 'vomit', 'convuls', 'déficit', 'deficit', 'enceinte', 'grossesse', 'cancer', 'traumatisme', 'pas de', 'non']
        token_count = sum(1 for t in tokens if t in ct)
        if token_count >= 3:
            # has at least 3 clinical tokens → well-documented, let the model decide
            return False
        
        # Default: if too few tokens, request clarification
        return token_count < 2

    if _needs_clarification(question):
        return ("Pour préciser: Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ? | "
                "Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ? | "
                "La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?")

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

    # First attempt
    resp = _call_model(prompt, temp=temperature)
    text = _normalize_response(resp).strip()

    # If the model didn't follow the strict single-line prefix format, retry once with an explicit short reminder.
    prefixes = ('Pour préciser:', 'Recommandation:')
    if not any(text.startswith(p) for p in prefixes):
        reminder = prompt + "\n\nRAPPEL: Commence ta réponse PAR soit 'Pour préciser:' soit 'Recommandation:' et DONNE UNE SEULE LIGNE."
        resp2 = _call_model(reminder, temp=temperature)
        text2 = _normalize_response(resp2).strip()
        if any(text2.startswith(p) for p in prefixes):
            return text2

    # If still non-conforming, ask for strict JSON output and try to parse it.
    if not any(text.startswith(p) for p in prefixes):
        json_prompt = prompt + "\n\nSI TU NE PEUX PAS RESPECTER LE FORMAT, RÉPONDS PAR UN JSON VALIDE (voir le schéma)."
        resp_json = _call_model(json_prompt, temp=temperature)
        text_json = _normalize_response(resp_json).strip()

        # try extract JSON object from the response
        import json, re

        def _extract_json(s: str):
            try:
                start = s.index('{')
                end = s.rindex('}')
                return s[start:end+1]
            except ValueError:
                return None

        jtxt = _extract_json(text_json)
        if jtxt:
            try:
                parsed = json.loads(jtxt)
                if isinstance(parsed, dict):
                    if parsed.get('type') == 'clarify' and isinstance(parsed.get('questions'), list):
                        qs = parsed['questions']
                        return 'Pour préciser: ' + ' | '.join(qs)
                    if parsed.get('type') == 'recommendation' and isinstance(parsed.get('text'), str):
                        rec_text = parsed['text']
                        # Éviter la duplication si le texte commence déjà par "Recommandation:"
                        if rec_text.strip().startswith('Recommandation:'):
                            return rec_text.strip()
                        return 'Recommandation: ' + rec_text
            except Exception:
                pass

    # Final attempt: if still non-conforming, extract the first non-empty line and try to salvage.
    if text:
        first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), text)
        if any(first_line.startswith(p) for p in prefixes):
            # Consistency check: if the case contains red flags but the model recommends
            # no imaging or is non-urgent, override with a conservative urgent recommendation.
            if first_line.startswith('Recommandation:'):
                lcq = question.lower()
                red_flags = [
                    'brutal', 'brutale', 'soudain', 'déficit', 'deficit', 'déficit neurologique', 'deficit neurologique',
                    'convuls', 'perte de connaissance', 'vomit', 'vomissements', 'fièvre', 'fievre', 'traumatisme', 'trauma',
                ]
                if any(rf in lcq for rf in red_flags):
                    # if recommendation lacks imaging/urgent keywords, override
                    low_priority_terms = ['pas d', 'pas d\'imagerie', 'pas d imagerie', 'traitement symptomatique', 'suivi ambulatoire']
                    imaging_keywords = ['irm', 'scanner', 'imagerie', 'urgence', 'en urgence']
                    low = any(lp in first_line.lower() for lp in low_priority_terms)
                    has_imaging = any(k in first_line.lower() for k in imaging_keywords)
                    if low and not has_imaging:
                        return ("Recommandation: IRM cérébrale en urgence si signes d'alerte (déficit neurologique, céphalée "
                                "d'apparition brutale, convulsions, fièvre ou traumatisme) — justifie par suspicion de lésion structurelle.")
            
            # Additional check: if the model returns "Pour préciser:" but with more than 5 questions
            # or non-standard short tokens (indicates confusion), override with a deterministic recommendation.
            if first_line.startswith('Pour préciser:'):
                qs_part = first_line[len('Pour préciser:'):].strip()
                import re
                qs_candidates = [q.strip() for q in re.split(r'[\?;\|]', qs_part) if q.strip()]
                if len(qs_candidates) > 5:
                    # too many questions; model is confused — force a recommendation based on red flags
                    lcq = question.lower()
                    red_flags = [
                        'brutal', 'brutale', 'soudain', 'déficit', 'deficit', 'déficit neurologique', 'deficit neurologique',
                        'convuls', 'perte de connaissance', 'vomit', 'vomissements', 'fièvre', 'fievre', 'traumatisme', 'trauma',
                    ]
                    if any(rf in lcq for rf in red_flags):
                        return ("Recommandation: IRM cérébrale en urgence si signes d'alerte (déficit neurologique, céphalée "
                                "d'apparition brutale, convulsions, fièvre ou traumatisme) — justifie par suspicion de lésion structurelle.")
                    else:
                        return ("Recommandation: Pas d'imagerie en première intention si absence de signes d'alerte; "
                                "traitement symptomatique et suivi ambulatoire. Refaire une évaluation si persistance/majoration.")
            
            return first_line

    # Heuristic deterministic fallback: inspect the clinical text for red flags and return
    # a safe recommendation in French rather than forcing the user to relaunch.
    def _heuristic_recommendation(case_text: str) -> str:
        lc = case_text.lower()
        # Check for negations before checking red flags
        import re
        
        # Red flag keywords
        red_flag_keywords = [
            'brutal', 'brutale', 'soudain', 'déficit', 'deficit', 'déficit neurologique', 'deficit neurologique',
            'convuls', 'perte de connaissance', 'vomit', 'vomissements', 'fièvre', 'fievre', 'traumatisme', 'trauma',
        ]
        
        # Count how many red flags are present AND not negated
        positive_red_flags = 0
        for rf in red_flag_keywords:
            if rf in lc:
                # check if it's preceded by negation within a short window
                idx = lc.find(rf)
                # look back up to 15 chars for negation words
                preceding = lc[max(0, idx-15):idx]
                negation_words = ['pas de', 'pas d', 'sans', 'aucun', 'aucune', 'non']
                if any(neg in preceding for neg in negation_words):
                    continue  # negated → skip
                positive_red_flags += 1
        
        if positive_red_flags > 0:
            return ("Recommandation: IRM cérébrale en urgence si signes d'alerte présents (déficit neurologique, céphalée "
                    "d'apparition brutale, convulsions, fièvre ou traumatisme) — justifie par suspicion de lésion "
                    "structurelle. Source: directives locales / RAG.")

        # Age-based or duration-based considerations (simple heuristics):
        if re.search(r"\b(\d{1,2})\s*(jours|j|jr|semaines|mois)\b", lc):
            # subacute, no red flags
            return ("Recommandation: Pas d'imagerie en première intention si absence de signes d'alerte; "
                    "traitement symptomatique et suivi ambulatoire. Refaire une évaluation si persistance/majoration.")

        # Default conservative recommendation
        return ("Recommandation: En l'absence d'éléments clairs, privilégier la surveillance clinique et le traitement "
                "symptomatique; demander imagerie (IRM cérébrale) si apparition de signes d'alerte ou aggravation.")

    try:
        import re
        return _heuristic_recommendation(question)
    except Exception:
        # If something unexpected happens, fall back to the safe prompt message
        return "Pour préciser: Le modèle n'a pas respecté le format demandé — merci de préciser le cas ou de relancer la requête."

    # Last-resort fallback: return a strict instruction in French asking for re-run.
    return "Pour préciser: Le modèle n'a pas respecté le format demandé — merci de préciser le cas ou de relancer la requête."

