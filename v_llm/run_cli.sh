#!/bin/bash
# Wrapper pour lancer l'interface CLI depuis n'importe où

cd "$(dirname "$0")"
python src/main.py "$@"
