#!/bin/bash
# Wrapper pour lancer l'évaluation depuis n'importe où

cd "$(dirname "$0")"
python evaluation/evaluate_model.py "$@"
