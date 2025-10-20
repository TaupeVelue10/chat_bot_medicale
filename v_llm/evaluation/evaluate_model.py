#!/usr/bin/env python3
"""Evaluate the BioMistral clinical assistant against the held-out validation set.

The script measures:
- Format compliance: percentage of outputs starting with "Pour préciser:" or "Recommandation:".
- Recommendation accuracy: agreement between predicted and expected action class
  (clarify / urgent imaging / non-urgent imaging / no imaging).
- Urgency precision/recall to highlight behaviour on red-flag cases.

Usage:
    python evaluate_model.py [--limit N]

Requires the Ollama model `biomistral-clinical:latest` to be created locally
(using the accompanying Modelfile) and the ChromaDB index initialised via
`indexage.create_index`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# Add src directory to path to import indexage
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from indexage import create_index

import importlib.util

# Load the local ollama helper without shadowing the installed package
_ollama_path = Path(__file__).parent.parent / "src" / "ollama.py"
spec = importlib.util.spec_from_file_location("local_ollama", str(_ollama_path))
local_ollama = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_ollama)  # type: ignore[attr-defined]
rag_biomistral_query = local_ollama.rag_biomistral_query


@dataclass
class CaseResult:
    case: str
    expected: str
    prediction: str
    format_ok: bool
    expected_cls: str
    predicted_cls: str


def load_cases(path: Path) -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            instruction = obj["instruction"]
            expected = obj["response"].strip()
            # Extract the clinical vignette after "Cas clinique:\n"
            match = re.search(r"Cas clinique:\n(.+)", instruction, re.DOTALL)
            if not match:
                raise ValueError(f"Cas clinique introuvable dans l'instruction: {instruction!r}")
            case_text = match.group(1).strip()
            cases.append((case_text, expected))
    return cases


def classify_action(text: str) -> str:
    stripped = text.strip()
    lowered = stripped.lower()

    if stripped.startswith("Pour préciser"):
        return "clarify"

    # Explicit "pas d'imagerie" or pure surveillance count as negative imaging.
    if "pas d'imagerie" in lowered or "pas d imagerie" in lowered:
        return "no_imaging"
    if stripped.startswith("Recommandation") and "surveillance" in lowered and "imagerie" not in lowered:
        return "no_imaging"

    # Extract the main payload after "Recommandation:" when available.
    recommendation_match = re.search(r"recommandation\s*:\s*(.*)", lowered)
    payload = recommendation_match.group(1) if recommendation_match else lowered

    if "scanner" in payload or "irm" in payload or "imagerie" in payload:
        if re.search(r"semi[- ]?urgence", payload) or "semi urgence" in payload or "programm" in payload:
            return "imaging_nonurgent"

        # Treat conditional urgencies ("en urgence si...") as undetermined.
        if re.search(r"en urgence\s+si", payload) or re.search(r"si .* en urgence", payload):
            return "other"

        if "urgence" in payload or "urgent" in payload:
            return "imaging_urgent"

        return "imaging_nonurgent"

    if "clarifier" in lowered:
        return "clarify"

    if "urgence" in lowered:
        return "imaging_urgent"

    return "other"


def evaluate(cases: Iterable[tuple[str, str]] , collection, limit: int | None = None) -> list[CaseResult]:
    results: list[CaseResult] = []
    for idx, (case_text, expected) in enumerate(cases):
        if limit is not None and idx >= limit:
            break
        prediction = rag_biomistral_query(case_text, collection, temperature=0.0).strip()
        format_ok = prediction.startswith("Pour préciser:") or prediction.startswith("Recommandation:")
        expected_cls = classify_action(expected)
        predicted_cls = classify_action(prediction)
        results.append(
            CaseResult(
                case=case_text,
                expected=expected,
                prediction=prediction,
                format_ok=format_ok,
                expected_cls=expected_cls,
                predicted_cls=predicted_cls,
            )
        )
    return results


def summarise(results: list[CaseResult]) -> str:
    total = len(results)
    if total == 0:
        return "Aucun cas évalué"

    format_ok = sum(1 for r in results if r.format_ok)
    accuracy = sum(1 for r in results if r.expected_cls == r.predicted_cls)

    # Precision/recall for urgent recommendations
    urgent_expected = [r for r in results if r.expected_cls == "imaging_urgent"]
    urgent_predicted = [r for r in results if r.predicted_cls == "imaging_urgent"]
    urgent_tp = sum(1 for r in results if r.expected_cls == r.predicted_cls == "imaging_urgent")
    precision = urgent_tp / len(urgent_predicted) if urgent_predicted else 0.0
    recall = urgent_tp / len(urgent_expected) if urgent_expected else 0.0

    lines = [
        f"Cas évalués : {total}",
        f"Format conforme : {format_ok / total:.1%} ({format_ok}/{total})",
        f"Précision de classe : {accuracy / total:.1%} ({accuracy}/{total})",
        f"Urgence – précision : {precision:.1%} (TP={urgent_tp}, prédits={len(urgent_predicted)})",
        f"Urgence – rappel : {recall:.1%} (positifs réels={len(urgent_expected)})",
    ]

    # Collect mismatches for debugging
    mismatches = [r for r in results if r.expected_cls != r.predicted_cls]
    if mismatches:
        lines.append("\nCas mal classés :")
        for r in mismatches:
            lines.append(
                f"- {r.case}\n  attendu={r.expected_cls} → '{r.expected}'\n  obtenu={r.predicted_cls} → '{r.prediction}'"
            )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue le prototype biomistral-clinical")
    parser.add_argument("--limit", type=int, help="Nombre de cas à évaluer (par défaut: dataset complet)")
    args = parser.parse_args()

    dataset_path = Path(__file__).parent.parent / "data" / "clinical_cases_val.jsonl"
    cases = load_cases(dataset_path)

    guidelines_path = Path(__file__).parent.parent / "data" / "guidelines.json"
    collection = create_index(str(guidelines_path))

    results = evaluate(cases, collection, limit=args.limit)
    report = summarise(results)
    print(report)


if __name__ == "__main__":
    main()
