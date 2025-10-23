from pathlib import Path
from indexage import create_index
import importlib.util
from pathlib import Path as _Path
import argparse
import sys

# Load the local `ollama.py` module explicitly to avoid shadowing by the
# installed `ollama` package in site-packages.
_ollama_path = _Path(__file__).parent / "ollama.py"
spec = importlib.util.spec_from_file_location("local_ollama", str(_ollama_path))
local_ollama = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_ollama)
rag_biomistral_query = local_ollama.rag_biomistral_query

def main():
    print("Assistant d'aide à la prescription d'imagerie")
    print("-------------------------------------------------------------\n")

    # CLI args: by default we use the simple LLM+RAG flow. Pass --deterministic
    # to enable the previous local decision-tree style interception.
    parser = argparse.ArgumentParser(description='Assistant CLI')
    parser.add_argument('--deterministic', action='store_true', help='Enable local deterministic pre-checks (decision tree)')
    args, unknown = parser.parse_known_args()
    deterministic_mode = args.deterministic

    # Chargement du RAG
    guidelines_path = Path(__file__).parent.parent / "data" / "guidelines.json"
    collection = create_index(str(guidelines_path))

    print("Décrivez le cas clinique du patient (ou tapez 'quit' pour quitter)\n")

    case_history = ""
    pending_questions = None
    while True:
        user_input = input("Médecin: ")

        # Check for quit keywords in the latest input
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Fin de session.")
            break

        # If we're currently waiting for answers to pending clarification questions,
        # treat the latest user_input as the answers (either single-line comma/| separated
        # or a single answer) and map them to the pending questions.
        if pending_questions:
            # split answers and attempt to recognize which fragment answers which question
            import re
            fragments = [a.strip() for a in re.split(r"\||,|;", user_input) if a.strip()]

            # Helpers to classify a fragment
            def is_duration_or_character(s: str) -> bool:
                s = s.lower()
                return bool(re.search(r"depuis|\b\d+\s*(h|heures|jours|semaines|mois|ans)\b|brutal|brutale|intense|progress", s))

            def is_redflag(s: str) -> bool:
                s = s.lower()
                return any(w in s for w in ['fièvre', 'fievre', 'vomit', 'vomissements', 'convuls', 'perte de connaissance', 'déficit', 'deficit', 'brutal', 'brutale'])

            def is_preg_onco(s: str) -> bool:
                s = s.lower()
                return any(w in s for w in ['enceinte', 'grossesse', 'cancer', 'oncologique', 'immunod', 'antécédent'])

            # mapping results
            mapped = ["", "", ""]
            # First assign by position when possible
            for i in range(min(len(fragments), 3)):
                mapped[i] = fragments[i]

            # If any fragment seems misplaced, try to reassign based on content
            for frag in fragments:
                if is_duration_or_character(frag) and not is_redflag(frag) and not is_preg_onco(frag):
                    mapped[0] = frag
                elif is_redflag(frag):
                    mapped[1] = frag
                elif is_preg_onco(frag):
                    mapped[2] = frag

            # Ensure duration has explicit duration; if not, ask follow-up
            lc0 = mapped[0].lower()
            if mapped[0] and not re.search(r"depuis|\b\d+\s*(h|heures|jours|semaines|mois|ans)\b", lc0):
                follow = input("Précisez la durée (ex: '2 jours', '1 semaine', '2 semaines', ou 'depuis 3 jours'): ")
                if follow.lower() in ["quit", "exit", "q"]:
                    print("Fin de session.")
                    return
                if follow.strip():
                    if mapped[0]:
                        mapped[0] = mapped[0] + ", depuis " + follow.strip()
                    else:
                        mapped[0] = "depuis " + follow.strip()

            # Append mapped answers to case_history
            for i, q in enumerate(pending_questions):
                case_history = case_history.rstrip() + ", " + q.lstrip() + ": " + (mapped[i] or '')
            pending_questions = None
        else:
            # Accumulate the clinical case: initial description followed by clarifications
            if not case_history:
                case_history = user_input
            else:
                # Append clarification to the case history
                case_history = case_history.rstrip() + ", " + user_input.lstrip()

        # By default use the simple RAG + LLM flow: the prompt instructs the
        # model to ask clarifying questions when information is missing. If the
        # user passed --deterministic we fall back to the local deterministic
        # pre-checks implemented previously.
        response = None
        if deterministic_mode:
            det = None
            try:
                # Load local guidelines_logic dynamically (avoid PYTHONPATH issues)
                import importlib.util, pathlib
                mod_path = pathlib.Path(__file__).parent / 'guidelines_logic.py'
                spec = importlib.util.spec_from_file_location('local_guidelines_logic', str(mod_path))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                analyze_guidelines = getattr(mod, 'analyze_guidelines')
                det = analyze_guidelines(case_history)
            except Exception:
                det = None

            if isinstance(det, str) and det.startswith("Pour préciser:"):
                import re
                questions_text = det[len("Pour préciser:"):].strip()
                candidates = [q.strip() for q in re.split(r"[\?;\n\|]", questions_text) if q.strip()]
                if not candidates:
                    candidates = [questions_text]
                pending_questions = candidates
                print("\nBioMistral : Pour préciser (répondez sur une seule ligne, séparées par '\|' ou des virgules) :")
                print(" | ".join(pending_questions))
                continue
            elif isinstance(det, str) and det:
                if det.startswith("URGENCE"):
                    response = det
                else:
                    response = "Recommandation: " + det
            else:
                response = rag_biomistral_query(case_history, collection)
        else:
            # Simple flow: always call the RAG+LLM. The model is instructed to ask
            # clarifying questions if data is missing.
            response = rag_biomistral_query(case_history, collection)

        # If the model asks for clarifications, extract the questions and set them as pending.
        if isinstance(response, str) and response.startswith("Pour préciser:"):
            questions_text = response[len("Pour préciser:"):].strip()
            import re
            candidates = [q.strip() for q in re.split(r"[\?;\n\|]", questions_text) if q.strip()]
            if not candidates:
                candidates = [questions_text]

            # If the case_history already contains answers, re-query immediately
            def _is_answered(idx, ch_text):
                lc = ch_text.lower()
                if idx == 0:
                    if 'depuis' in lc or re.search(r"\b(\d+\s*(j|jr|jours|semaines|mois|ans))\b", lc) or any(w in lc for w in ['brutal', 'brutale', 'intense', 'progress']):
                        return True
                if idx == 1:
                    if any(w in lc for w in ['fièvre', 'fievre', 'vomit', 'vomissements', 'convuls', 'perte de connaissance', 'déficit', 'deficit']):
                        return True
                if idx == 2:
                    if any(w in lc for w in ['enceinte', 'grossesse', 'cancer', 'immunod', 'traumatisme', 'trauma']):
                        return True
                if any(w in lc for w in ['oui', 'non']) or re.search(r"\d{1,3}", lc):
                    return True
                return False

            answered_flags = [_is_answered(i, case_history) for i in range(len(candidates))]
            if all(answered_flags):
                response = rag_biomistral_query(case_history, collection)
                print(f"\nBioMistral : {response}\n")
                continue

            # Set pending questions and show them as a single-line prompt; next user input will be parsed as answers.
            pending_questions = candidates
            print("\nBioMistral : Pour préciser (répondez sur une seule ligne, séparées par '|' ou des virgules) :")
            print(" | ".join(pending_questions))
            continue

        # If the model failed to respect format and returned the fallback message,
        # proactively ask a short set of essential clarifying questions.
        if isinstance(response, str) and "Le modèle n'a pas respecté le format demandé" in response:
            print("Le modèle n'a pas respecté le format demandé — je vais poser 3 questions clés pour préciser le cas.")
            clarif_qs = [
                "Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ?",
                "Y a‑t‑il fièvre, vomissements, perte de connaissance ou déficit neurologique focal ?",
                "La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?",
            ]
            for q in clarif_qs:
                ans = input(q + " ")
                if ans.lower() in ["quit", "exit", "q"]:
                    print("Fin de session.")
                    return
                case_history = case_history.rstrip() + ", " + q + ": " + ans.strip()

            # Re-query after collecting programmatic clarifications
            response = rag_biomistral_query(case_history, collection)

        print(f"\nBioMistral : {response}\n")

if __name__ == "__main__":
    main()
