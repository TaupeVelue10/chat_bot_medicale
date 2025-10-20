# Rapport de nettoyage du projet BioMistral

## 📊 État actuel du workflow

### Workflow de production (à conserver)
1. **Génération dataset** → `generate_finetune_dataset.py` ✅
2. **Fine-tuning** → `finetune_biomistral_unsloth.py` (Colab) ✅
3. **Merge LoRA** → `merge_biomistral.py` ✅
4. **Conversion GGUF** → `convert-hf-to-gguf.py` ✅
5. **Indexation RAG** → `indexage.py` ✅
6. **Interface Ollama** → `ollama.py` ✅
7. **CLI interactive** → `main.py` ✅
8. **Évaluation** → `evaluate_model.py` ✅

### Données essentielles (à conserver)
- `guidelines.json` - Directives médicales
- `clinical_cases_train.jsonl` - Dataset d'entraînement (160 exemples)
- `clinical_cases_val.jsonl` - Dataset de validation (40 exemples)
- `Modelfile` - Configuration Ollama
- `requirements.txt` - Dépendances Python

---

## 🗑️ Fichiers à supprimer

### 1. Scripts obsolètes
- ❌ **`prepare_finetuning_data.py`** (213 lignes)
  - Remplacé par `generate_finetune_dataset.py`
  - Générait seulement ~30 exemples vs 200 maintenant
  - Format d'instruction obsolète

### 2. Dossiers temporaires de build
- ❌ **`llama.cpp-temp/`** (clone complet llama.cpp)
  - Utilisé uniquement pour conversion GGUF
  - Seul `gguf-py/` est nécessaire
  - Occupé plusieurs centaines de MB

### 3. Modèles intermédiaires non utilisés
- ❌ **`biomistral_clinical_lora_v2_merged-f16.gguf`** (~14 GB)
  - Format F16 non quantifié, très lourd
  - `biomistral_clinical_lora_v2_merged-q8_0.gguf` suffit (Q8 balance taille/qualité)
  - F16 conservé uniquement si besoin de conversion ultérieure

### 4. Checkpoints intermédiaires de training
- ❌ **`biomistral_clinical_lora_v2/checkpoint-20/`**
- ❌ **`biomistral_clinical_lora_v2/checkpoint-40/`**
- ⚠️ **`biomistral_clinical_lora_v2/checkpoint-60/`** (garder si c'est le meilleur)
  - Ne conserver que le checkpoint final utilisé pour le merge

### 5. Documentation obsolète
- ⚠️ **`FINE_TUNING_GUIDE.md`**
  - À vérifier si contient des infos non documentées ailleurs
  - Sinon peut être archivé

### 6. Cache Python
- ❌ **`__pycache__/`**
  - Régénéré automatiquement
  - Ajouté au `.gitignore`

### 7. Base de données RAG locale
- ⚠️ **`rag_db/`**
  - ChromaDB locale recréée à chaque run
  - Peut être supprimée (elle se reconstruit via `indexage.py`)

---

## 🧹 Code mort à nettoyer dans les fichiers actifs

### `ollama.py` - Fonctions heuristiques redondantes

Le fichier contient **3 fonctions de fallback** qui ne sont plus nécessaires car le modèle fine-tuné respecte maintenant le format :

```python
# LIGNES À SUPPRIMER (lignes ~112-300)

def _needs_clarification(case_text: str) -> bool:
    # Logique heuristique pour détecter si clarification nécessaire
    # ❌ Non utilisée - le modèle décide maintenant

def _heuristic_recommendation(case_text: str) -> str:
    # Logique heuristique pour recommandation d'imagerie
    # ❌ Non utilisée - le modèle génère les recommandations

def _extract_json(s: str):
    # Extraction JSON de réponses structurées
    # ❌ Format JSON abandonné au profit de texte libre structuré
```

**Impact** : Réduction de ~180 lignes, simplification de la maintenance.

### `main.py` - Logique de parsing complexe

```python
# LIGNES À SIMPLIFIER (lignes ~40-100)

# Logique complexe de mapping réponses → questions avec follow-ups
# Si le modèle est assez robuste, cette complexité peut être réduite
# en posant simplement les questions en séquence sans parsing sophistiqué
```

**Recommandation** : Tester si le modèle fine-tuné gère bien les clarifications itératives sans cette orchestration.

### `evaluate_model.py` - Imports redondants

```python
# LIGNE 4
from pathlib import Path

# LIGNE 8  
import importlib.util
```

Ces imports sont déjà présents, vérifier les doublons.

---

## 📝 Actions recommandées

### Phase 1 : Suppression sans risque (immédiat)
```bash
# Supprimer scripts obsolètes
rm prepare_finetuning_data.py

# Supprimer dossier temporaire llama.cpp
rm -rf llama.cpp-temp/

# Supprimer checkpoints intermédiaires (garder uniquement le final)
rm -rf biomistral_clinical_lora_v2/checkpoint-20/
rm -rf biomistral_clinical_lora_v2/checkpoint-40/

# Supprimer cache Python
rm -rf __pycache__/

# Supprimer base RAG locale (se reconstruit)
rm -rf rag_db/
```

### Phase 2 : Nettoyage conditionnel (après vérification)
```bash
# Si F16 non nécessaire pour futures conversions
rm biomistral_clinical_lora_v2_merged-f16.gguf  # Économise ~14 GB

# Si checkpoint-60 n'est pas le meilleur
rm -rf biomistral_clinical_lora_v2/checkpoint-60/
```

### Phase 3 : Refactoring code (après tests)
1. Nettoyer `ollama.py` :
   - Supprimer `_needs_clarification()`
   - Supprimer `_heuristic_recommendation()`
   - Supprimer `_extract_json()`
   - Garder uniquement `_call_model()` et `rag_biomistral_query()`

2. Simplifier `main.py` :
   - Réduire la logique de parsing si le modèle gère bien les clarifications

3. Vérifier imports dans `evaluate_model.py`

---

## 📦 Structure finale recommandée

```
v_llm/
├── core/                           # Scripts principaux
│   ├── ollama.py                   # Interface Ollama (nettoyée)
│   ├── indexage.py                 # Indexation RAG
│   └── main.py                     # CLI interactive
├── training/                       # Scripts d'entraînement
│   ├── generate_finetune_dataset.py
│   ├── finetune_biomistral_unsloth.py
│   └── merge_biomistral.py
├── conversion/                     # Conversion GGUF
│   ├── convert-hf-to-gguf.py
│   └── gguf-py/
├── evaluation/                     # Évaluation
│   └── evaluate_model.py
├── data/                           # Données
│   ├── guidelines.json
│   ├── clinical_cases_train.jsonl
│   └── clinical_cases_val.jsonl
├── models/                         # Modèles finaux
│   ├── biomistral_clinical_lora_v2/       # Adapters LoRA finaux
│   ├── biomistral_clinical_lora_v2_merged/ # Modèle HF mergé
│   └── biomistral_clinical_lora_v2_merged-q8_0.gguf  # GGUF Ollama
├── Modelfile
├── requirements.txt
└── README.md
```

---

## 💾 Estimation du gain d'espace

| Élément | Taille | Gain |
|---------|--------|------|
| `llama.cpp-temp/` | ~500 MB | ✅ |
| `biomistral_clinical_lora_v2_merged-f16.gguf` | ~14 GB | ⚠️ (si non nécessaire) |
| Checkpoints intermédiaires | ~2-3 GB | ✅ |
| `__pycache__/` | ~5 MB | ✅ |
| `rag_db/` | ~20 MB | ✅ |
| **Total minimum** | **~3 GB** | |
| **Total avec F16** | **~17 GB** | |

---

## ⚠️ Précautions

1. **Backup avant suppression** : 
   ```bash
   tar -czf v_llm_backup_$(date +%Y%m%d).tar.gz v_llm/
   ```

2. **Tester après nettoyage** :
   ```bash
   python evaluate_model.py --limit 5
   python main.py
   ```

3. **Git tracking** : Si sous git, commit avant nettoyage pour rollback facile

4. **Modèles de base** : Ne PAS supprimer `/Users/alexpeirano/Desktop/commande_entreprise/BioMistral-7B` (hors projet)
