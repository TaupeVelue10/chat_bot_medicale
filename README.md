README
======

Projet: Minimal BioMistral RAG pipeline
-------------------------------------

Ce dépôt contient une version minimale d'un pipeline RAG (retrieval-augmented generation) centré sur BioMistral.
L'objectif est simple :
- indexer / encoder l'input,
- récupérer des documents pertinents depuis un index RAG (objet `collection`),
- construire un prompt en français et appeler le modèle BioMistral via le client `ollama` installé.

Fichiers importants
- `src/ollama.py` : fonction `rag_biomistral_query(question, collection)` — exécute la requête RAG et appelle BioMistral. Ce module n'utilise pas de paramètre de température.
- `src/main.py` : petit runner/CLI (si présent) pour appeler la fonction depuis la ligne de commande.

Prérequis
- Python 3.10+ recommandé.
- Client Ollama installé et modèle `biomistral-clinical:latest` disponible localement (ou via le client utilisé dans votre environnement).

Installation (en local)
README
======

Projet: Minimal BioMistral RAG pipeline
-------------------------------------

Ce dépôt contient une version minimale d'un pipeline RAG (retrieval-augmented generation) centré sur BioMistral.
L'objectif est simple :
- indexer / encoder l'input,
- récupérer des documents pertinents depuis un index RAG (objet `collection`),
- construire un prompt en français et appeler le modèle BioMistral via le client `ollama` installé.

Fichiers importants
- `src/ollama.py` : fonction `rag_biomistral_query(question, collection)` — exécute la requête RAG et appelle BioMistral. Ce module n'utilise pas de paramètre de température.
- `src/main.py` : petit runner/CLI (si présent) pour appeler la fonction depuis la ligne de commande.

Prérequis
- Python 3.10+ recommandé.
- Client Ollama installé et modèle `biomistral-clinical:latest` disponible localement (ou via le client utilisé dans votre environnement).

Installation (en local)
1. Créer un virtualenv :

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Installer les dépendances requises (si vous maintenez un `requirements.txt`) :

```bash
pip install -r requirements.txt
# ou au minimum :
pip install ollama
```

Usage rapide / test d'import
1. Test d'import (sanity) sans appel réseau :

```bash
python -c "import src.ollama as o; print('import ok' if hasattr(o, 'rag_biomistral_query') else 'missing')"
```

2. Exemple d'utilisation (depuis un script ou REPL) :

```python
from src.ollama import rag_biomistral_query

# collection doit implémenter: query(query_texts=[str], n_results=int) -> dict
# exemple minimal de collection de test à fournir si vous testez localement
class SimpleCollection:
    def query(self, query_texts, n_results=3):
        return {'documents': [["Extrait guide 1", "Extrait guide 2"]], 'metadatas': [[{'source': 'local', 'motif': 'guide'}]]}

resp = rag_biomistral_query('Patient avec cephalées...', SimpleCollection())
print(resp)
```

Préparer un push Git propre
1. Le dépôt contient parfois des binaires de modèles volumineux. Avant le push, utilisez `.gitignore` pour exclure les modèles et environnements locaux (fichier `.gitignore` fourni).

2. Commandes recommandées :

```bash
# vérifier l'etat
git status

# ajouter et committer
git add .
git commit -m "chore: minimal BioMistral RAG pipeline and git ignore"

# pousser
git push origin main
```

Notes et bonnes pratiques
- N'incluez pas les gros fichiers de modèle dans le dépôt (formats `.gguf`, `.safetensors`, `.ckpt`, etc.). Placez-les dans un stockage externe si nécessaire.
- Le code est volontairement minimal : ajoutez des validations, tests unitaires et gestion des erreurs pour production.

Licence / Avertissements
- Ce dépôt contient du code de démonstration. Vérifiez les contraintes de licence des modèles et données utilisées avant toute diffusion.
