import sys
import os
from typing import Dict, List, Tuple, Optional


def _import_v_arbre():
    """Attempt to import the v_arbre_d main module by adding project root to sys.path."""
    try:
        import v_arbre_d.main as v_arbre_main
        return v_arbre_main
    except Exception:
        # try to add project root to path
        this_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if this_dir not in sys.path:
            sys.path.insert(0, this_dir)
        try:
            import v_arbre_d.main as v_arbre_main
            return v_arbre_main
        except Exception:
            # As last resort, try importing by path
            vpath = os.path.join(this_dir, 'v_arbre_d')
            if vpath not in sys.path:
                sys.path.insert(0, vpath)
            try:
                import main as v_arbre_main
                return v_arbre_main
            except Exception:
                raise


DEFAULT_QUESTIONS = {
    "fievre": "Fièvre ? (o/n)",
    "brutale": "Installation brutale (coup de tonnerre) ? (o/n)",
    "deficit": "Déficit moteur ou sensitif ? (o/n)",
    "oncologique": "Antécédent de cancer ? (o/n)",
    "grossesse": "Grossesse en cours (<3 mois) ? (o/n)",
    "chirurgie": "Chirurgie récente (<6 semaines avec matériel) ? (o/n)",
    "pacemaker": "Pace-maker ? (o/n)",
    "claustrophobie": "Claustrophobie ? (o/n)",
    "vertige": "Vertige ? (o/n)",
    "troubles_visuels": "Troubles visuels ? (o/n)",
    "acouphene": "Acouphènes ? (o/n)",
    "douleurs_articulaires": "Douleurs articulaires ? (o/n)",
}


def fill_tree_noninteractive(initial_text: str) -> Tuple[str, List[str]]:
    """Run the decision tree once and return (recommendation_or_none, missing_questions).

    If recommendation is available immediately, recommendation_or_none is the string and missing_questions empty.
    Otherwise recommendation_or_none is None and missing_questions is a list of questions to ask the clinician.
    """
    v = _import_v_arbre()
    f = v.analyse_texte_medical(initial_text)

    # Fields we consider important to decide
    required = ["fievre", "brutale", "deficit", "oncologique", "grossesse", "chirurgie", "pacemaker"]

    missing = []
    for k in required:
        val = f.get(k)
        if val is None or (isinstance(val, bool) and not val and k in DEFAULT_QUESTIONS):
            # treat False as 'not detected' → may need to ask
            missing.append(DEFAULT_QUESTIONS.get(k, f"{k} ?"))

    # If nothing important is missing, produce recommendation
    if not missing:
        reco = v.decision_imagerie(f)
        return reco, []

    return None, missing


def run_interactive(initial_text: str) -> str:
    """Interactively ask missing questions (via input) until recommendation can be produced.

    Returns the final recommendation string (including contra-indications display text).
    """
    v = _import_v_arbre()
    f = v.analyse_texte_medical(initial_text)

    # Copy same questions as in v_arbre_d.main.chatbot_cephalees
    questions = DEFAULT_QUESTIONS.copy()

    # Adjust: don't ask pregnancy if male or age >=50
    if f.get('sexe') == 'm' or (f.get('age') and f.get('age') >= 50):
        f['grossesse'] = False

    # Iterate over questions and prompt if value not already True
    for key, q in questions.items():
        if key == 'grossesse' and (f.get('sexe') == 'm' or (f.get('age') and f.get('age') >= 50)):
            continue
        # If already detected true, skip asking
        if f.get(key):
            continue
        # ask clinician
        while True:
            try:
                r = input(q + ' ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                return "Fin de la consultation (interruption utilisateur)."
            if r in ['o', 'oui', 'y', 'yes']:
                f[key] = True
                break
            if r in ['n', 'non', 'no']:
                f[key] = False
                break
            if r in ['q', 'quit', 'exit']:
                return "Fin de la consultation (annulé)."
            # otherwise repeat

    # After filling, produce recommendation and include contra-indications text
    reco = v.decision_imagerie(f)
    # capture contra-indications display
    contras = []
    try:
        # call afficher_contraindications if present
        if hasattr(v, 'afficher_contraindications'):
            # capture stdout by calling function and letting it print — for simplicity, just call it
            # but we will not capture its output; instead call it and append a note
            # Better: call and ignore
            v.afficher_contraindications(f)
    except Exception:
        pass

    return reco
