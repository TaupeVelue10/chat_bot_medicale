# BioMistral Clinical Assistant

Assistant médical basé sur BioMistral-7B fine-tuné pour l'aide à la prescription d'imagerie cérébrale selon les guidelines HAS/SFETD 2017.

##  Fonctionnalités

- **RAG (Retrieval-Augmented Generation)** : Interroge une base de directives médicales
- **Format structuré** : Sorties `Pour préciser:` ou `Recommandation:`
- **Fine-tuning spécialisé** : 200 cas cliniques (céphalées, red flags, grossesse, traumatisme)
- **Modèle quantifié Q8_0** : Balance qualité/performance pour déploiement Ollama

##  Structure du projet

```
v_llm/
├── src/                    # Code source principal
│   ├── main.py            # CLI interactive
│   ├── ollama.py          # Interface Ollama + RAG
│   └── indexage.py        # Indexation ChromaDB
│
├── data/                   # Données et guidelines
│   ├── guidelines.json    # Directives médicales
│   ├── clinical_cases_train.jsonl  # 160 cas d'entraînement
│   └── clinical_cases_val.jsonl    # 40 cas de validation
│
├── training/               # Pipeline d'entraînement
│   ├── generate_finetune_dataset.py    # Génération dataset
│   ├── finetune_biomistral_unsloth.py  # Fine-tuning (Colab)
│   ├── merge_biomistral.py             # Merge LoRA
│   └── convert-hf-to-gguf.py           # Conversion GGUF
│
├── models/                 # Modèles finaux
│   ├── biomistral_clinical_lora_v2/           # Adapters LoRA
│   ├── biomistral_clinical_lora_v2_merged/    # Modèle HF mergé
│   └── biomistral_clinical_lora_v2_merged-q8_0.gguf  # GGUF production
│
├── evaluation/             # Évaluation
│   └── evaluate_model.py  # Script d'évaluation automatique
│
├── docs/                   # Documentation
│   ├── CLEANUP_REPORT.md
│   └── CLEANUP_SUMMARY.md
│
├── gguf-py/               # Bibliothèque GGUF
│
├── Modelfile              # Configuration Ollama
├── requirements.txt       # Dépendances Python
├── run_cli.sh            #  Lancer l'interface CLI
├── run_evaluation.sh     #  Lancer l'évaluation
└── .gitignore
```

##  Démarrage rapide

### 1. Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Créer le modèle Ollama
ollama create biomistral-clinical -f Modelfile

# Vérifier que le modèle est disponible
ollama list | grep biomistral
```

### 2. Utilisation

#### Interface CLI interactive
```bash
./run_cli.sh
# ou
python src/main.py
```

**Exemple d'utilisation :**
```
Médecin: Patient 45 ans, céphalées

BioMistral: Pour préciser: Depuis quand et quel caractère ont les céphalées 
(brutale / intense / progressive) ? | Y a‑t‑il fièvre, vomissements, perte 
de connaissance, convulsions ou déficit neurologique focal ? | La patiente 
est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) 
ou un traumatisme crânien récent ?

Médecin: progressive depuis 3 semaines

BioMistral: Recommandation: Pas d'imagerie en première intention si absence 
de signes d'alerte; traitement symptomatique et suivi ambulatoire. Refaire 
une évaluation si persistance/majoration.
```

#### Évaluation
```bash
# Évaluer sur 5 cas
./run_evaluation.sh --limit 5

# Évaluation complète (40 cas)
./run_evaluation.sh
```

#### Test direct
```bash
ollama run biomistral-clinical "Patient 55 ans, céphalées brutales depuis 2h"
```

##  Workflow d'entraînement

### 1. Génération du dataset
```bash
cd training
python generate_finetune_dataset.py --n 200
# Produit: ../data/clinical_cases_train.jsonl (160 cas)
#         ../data/clinical_cases_val.jsonl (40 cas)
```

### 2. Fine-tuning (Colab recommandé)
```bash
# Sur Colab avec GPU T4/A100
python finetune_biomistral_unsloth.py \
    --model_name BioMistral/BioMistral-7B \
    --train_file ../data/clinical_cases_train.jsonl \
    --val_file ../data/clinical_cases_val.jsonl \
    --output_dir ../models/biomistral_clinical_lora_v2 \
    --num_train_epochs 3 \
    --batch_size 2
```

### 3. Merge des adapters LoRA
```bash
python merge_biomistral.py
# Produit: ../models/biomistral_clinical_lora_v2_merged/
```

### 4. Conversion GGUF
```bash
python convert-hf-to-gguf.py \
    ../models/biomistral_clinical_lora_v2_merged/ \
    --outfile ../models/biomistral_clinical_lora_v2_merged-q8_0.gguf \
    --outtype q8_0
```

### 5. Création du modèle Ollama
```bash
cd ..
ollama create biomistral-clinical -f Modelfile
```

##  Métriques d'évaluation

Le script `evaluate_model.py` calcule :
- **Format compliance** : % de sorties respectant le format attendu
- **Précision de classe** : % de recommandations correctes (clarify/urgent/non-urgent/no imaging)
- **Urgence precision/recall** : Métriques spécifiques aux cas urgents (red flags)

### Exemple de rapport
```
Cas évalués : 40
Format conforme : 95.0% (38/40)
Précision de classe : 72.5% (29/40)
Urgence – précision : 85.7% (TP=6, prédits=7)
Urgence – rappel : 75.0% (positifs réels=8)
```

##  Configuration

### Modelfile (Ollama)
```
FROM ./models/biomistral_clinical_lora_v2_merged-q8_0.gguf

PARAMETER temperature 0.0
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM """Tu es un assistant médical expert..."""
```

### Prompt système
Le prompt dans `src/ollama.py` force :
1. Vérification systématique des signes d'alerte
2. Questions standardisées si info manquante
3. Format strict `Pour préciser:` / `Recommandation:`
4. Justification basée sur les guidelines RAG

##  Guidelines médicales

Le fichier `data/guidelines.json` contient :
- Critères d'imagerie urgente (HAS/SFETD 2017)
- Red flags : céphalée brutale, déficit neuro, fièvre, convulsions, perte de connaissance
- Cas spécifiques : grossesse, immunodépression, traumatisme, âge >50 ans
- Protocoles d'imagerie : IRM vs Scanner, avec/sans injection, délai

## 🛠️ Développement

### Ajouter des guidelines
```json
{
  "id": "guideline_10",
  "motif": "Nouveau contexte",
  "texte": "Description de la directive...",
  "source": "Référence médicale"
}
```

### Modifier le prompt système
Éditer `src/ollama.py`, fonction `rag_biomistral_query()`, variable `prompt`.

### Simplifier la logique CLI
Si le modèle fine-tuné gère bien les clarifications, simplifier `src/main.py` lignes 40-100.

##  Dépendances principales

```
transformers>=4.57.0
peft>=0.17.0
unsloth
torch>=2.9.0
chromadb
ollama
gguf-py (local)
```

##  Notes importantes

1. **Modèle de base** : BioMistral-7B doit être téléchargé séparément (~14 GB)
2. **Fine-tuning** : Nécessite GPU (Colab recommandé, T4 minimum)
3. **Ollama** : Le modèle `biomistral-clinical:latest` doit être créé localement
4. **ChromaDB** : Base RAG reconstruite à chaque lancement (pas de persistance)

##  Debugging

### Le modèle ne respecte pas le format
- Vérifier la température (doit être 0.0 pour déterminisme)
- Relancer avec `./run_evaluation.sh --limit 1` pour tester

### Erreur "Model not found"
```bash
ollama list
# Si absent :
ollama create biomistral-clinical -f Modelfile
```

### Erreur de chemin
Tous les scripts utilisent des chemins relatifs depuis leur position.  
Toujours lancer depuis la racine du projet ou utiliser les wrappers `run_*.sh`.

##  Performance

| Métrique | Valeur |
|----------|--------|
| Taille modèle (Q8_0) | ~7.5 GB |
| Temps d'inférence | ~2-3s par requête |
| Format compliance | >95% |
| Précision clinique | ~70-75% |

##  TODO

- [ ] Améliorer la détection des négations ("sans fièvre" mal interprété)
- [ ] Enrichir les guidelines avec plus de cas edge
- [ ] Ajouter support multilingue (anglais médical)
- [ ] Optimiser la logique de clarification dans `main.py`

##  Licence

Modèle de base : BioMistral-7B (Apache 2.0)  
Code : À définir

##  Contribution

1. Ajouter des cas dans `training/generate_finetune_dataset.py`
2. Fine-tuner avec le dataset étendu
3. Évaluer avec `./run_evaluation.sh`
4. Documenter les changements

---

**Dernière mise à jour** : 20 octobre 2025  
**Version** : 2.0 (structure réorganisée)
