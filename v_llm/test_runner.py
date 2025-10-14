from pathlib import Path
import importlib.util
from indexage import create_index
from pathlib import Path as _Path

# load local ollama module same as main
_ollama_path = _Path(__file__).parent / "ollama.py"
spec = importlib.util.spec_from_file_location("local_ollama", str(_ollama_path))
local_ollama = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_ollama)
rag_biomistral_query = local_ollama.rag_biomistral_query


def run_test(case_initial: str, answers: list, temperature: float = 0.0):
    guidelines_path = Path(__file__).parent / "guidelines.json"
    collection = create_index(str(guidelines_path))

    print("=== TEST START ===")
    case = case_initial
    print(f"CASE: {case}")

    resp = rag_biomistral_query(case, collection, temperature=temperature)
    print(f"MODEL: {resp}\n")

    if isinstance(resp, str) and resp.startswith("Pour préciser:"):
        # split by ' | ' as enforced by prompt
        qs_part = resp[len("Pour préciser:"):].strip()
        qs = [q.strip() for q in qs_part.split('|') if q.strip()]
        # use provided answers in order
        for i, q in enumerate(qs):
            ans = answers[i] if i < len(answers) else ""
            print(f"Q: {q}\nA: {ans}\n")
            case = case.rstrip() + ", " + q + ": " + ans

        # re-query
        final = rag_biomistral_query(case, collection, temperature=temperature)
        print(f"FINAL MODEL: {final}\n")
    else:
        print("No clarifications requested by model.")

    print("=== TEST END ===")


if __name__ == '__main__':
    # Example simulated clinician inputs
    initial = "patiente 22 ans, céphalées"
    answers = ["progressive depuis 2 semaines", "non", "oui traumatisme crânien"]
    run_test(initial, answers, temperature=0.0)
