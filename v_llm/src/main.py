from pathlib import Path
from indexage import create_index
import importlib.util
from pathlib import Path as _Path

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

    # Chargement du RAG
    guidelines_path = Path(__file__).parent.parent / "data" / "guidelines.json"
    collection = create_index(str(guidelines_path))

    print("Décrivez le cas clinique du patient (ou tapez 'quit' pour quitter)\n")

    case_history = ""
    pending_questions = None
    while True:
        user_input = input("Médecin: ")

        # mot clés pour quitter le système
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Fin de session.")
            break

        # Si on attend des réponses aux questions de clarification en cours 
        # On traite le dernier input utilisateur comme une réponse 
        if pending_questions:
            import re
            answers = [a.strip() for a in re.split(r"\||,|;", user_input) if a.strip()]
            # associe les réponses aux questions
            for i, q in enumerate(pending_questions):
                ans = answers[i] if i < len(answers) else ''
                # on vérifie que la durée des symptomes est donnée dans la première réponse, sinon on demande à clarifier
                if i == 0:
                    lcans = ans.lower()
                    # cherce les mots clés
                    if not ("depuis" in lcans or re.search(r"\b(\d+\s*(h|heures|jours|jours|semaines|mois|ans))\b", lcans)):
                        # demande la duration
                        follow = input("Précisez la durée (ex: '2 jours', '1 semaine', '2 semaines', ou 'depuis 3 jours'): ")
                        if follow.lower() in ["quit", "exit", "q"]:
                            print("Fin de session.")
                            return
                        if follow.strip():
                            # associe caractères et la duration si elle est donnée
                            if ans:
                                ans = ans + ", depuis " + follow.strip()
                            else:
                                ans = "depuis " + follow.strip()
                case_history = case_history.rstrip() + ", " + q.lstrip() + ": " + ans
            pending_questions = None
        else:
            # accumule les données en les stockant dans case_history
            if not case_history:
                case_history = user_input
            else:
                # on ajoute la clarification à case_history
                case_history = case_history.rstrip() + ", " + user_input.lstrip()

        response = rag_biomistral_query(case_history, collection)

        # si le modèle demande des clarifications, on extrait les questions et on les labeles comme en cours dans l'array candidates
        if isinstance(response, str) and response.startswith("Pour préciser:"):
            questions_text = response[len("Pour préciser:"):].strip()
            import re
            candidates = [q.strip() for q in re.split(r"[\?;\n\|]", questions_text) if q.strip()]
            if not candidates:
                candidates = [questions_text]

            # si dans case_history on y trouve deja les infos que demande le modèle, on refait une query
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

            # associe les questions en cours a l'array candidates
            pending_questions = candidates
            print("\nBioMistral : Pour préciser (répondez sur une seule ligne, séparées par '|' ou des virgules) :")
            print(" | ".join(pending_questions))
            continue

        # si le modèle ne respecte pas le format, on return ce fallback hardcoder avec des questions pour clarifier
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

            # refaire une query du rag avec les nouveaux inputs stockés dans case_history
            response = rag_biomistral_query(case_history, collection)

        print(f"\nBioMistral : {response}\n")

if __name__ == "__main__":
    main()
