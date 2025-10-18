# Guide de Fine-Tuning pour BioMistral

## Vue d'ensemble

Ce guide vous explique comment fine-tuner BioMistral pour améliorer sa compliance au format de réponse structuré ("Pour préciser:" / "Recommandation:") et sa capacité à analyser les cas cliniques de céphalées.

## Objectifs du Fine-Tuning

1. **Améliorer la reconnaissance des informations manquantes** : le modèle doit détecter quand des éléments clés sont absents (durée, red flags, antécédents) et poser exactement les 3 questions standard.
2. **Forcer le respect du format** : toutes les réponses doivent commencer par "Pour préciser:" ou "Recommandation:".
3. **Améliorer la détection des red flags** : reconnaître "déficit neurologique", "fièvre", "brutale", etc. même quand formulés différemment.
4. **Gérer les négations** : comprendre "pas de fièvre", "pas de déficit" comme absence de red flags.

## Approches de Fine-Tuning

### Option 1 : LoRA (Low-Rank Adaptation) — Recommandé

**Avantages** :
- Rapide (quelques heures sur GPU consumer)
- Nécessite peu de données (~50-200 exemples)
- Conserve le modèle de base intact
- Faible coût mémoire

**Outils** :
- [Unsloth](https://github.com/unslothai/unsloth) (très rapide, optimisé pour LoRA)
- [Axolotl](https://github.com/OpenAccess-AI-Collective/axolotl) (configuration YAML simple)
- [HuggingFace PEFT](https://github.com/huggingface/peft)

### Option 2 : Full Fine-Tuning

**Avantages** :
- Maximum d'adaptation au domaine
- Meilleure performance finale

**Inconvénients** :
- Nécessite GPU puissant (A100 / 4090)
- Plusieurs centaines d'exemples requis
- Risque d'oubli catastrophique

## Préparation des Données

### Format Dataset

Créez un fichier JSONL avec des paires instruction/réponse. Chaque ligne contient un exemple :

```jsonl
{"instruction": "CAS CLINIQUE:\npatient 22 ans, céphalées\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'", "response": "Pour préciser: Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ? | Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ? | La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?"}
{"instruction": "CAS CLINIQUE:\npatiente 22 ans, céphalées progressives depuis 2 semaines, déficit neurologique, fièvre, elle n'est pas enceinte\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'", "response": "Recommandation: IRM cérébrale en urgence si signes d'alerte (déficit neurologique, fièvre) — justifie par suspicion de lésion structurelle. Source: HAS/SFETD 2017."}
```

### Nombre d'Exemples Recommandés

- **Minimum** : 50 exemples (LoRA)
- **Optimal** : 150-300 exemples
- **Répartition** :
  - 40% cas courts → clarifications
  - 30% red flags → IRM urgence
  - 20% pas de red flags → surveillance
  - 10% cas ambigus

## Script de Préparation des Données

Voir `prepare_finetuning_data.py` dans ce répertoire.

## Fine-Tuning avec Unsloth (LoRA)

### Installation

```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps "xformers<0.0.27" trl peft accelerate bitsandbytes
```

### Script d'Entraînement

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# 1. Charger BioMistral
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="BioMistral/BioMistral-7B",  # ou votre chemin local
    max_seq_length=2048,
    dtype=None,  # auto-détection
    load_in_4bit=True,  # quantization 4-bit pour économiser mémoire
)

# 2. Configurer LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # rang LoRA (8-32 recommandé)
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0.0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# 3. Charger dataset
dataset = load_dataset("json", data_files="clinical_cases_train.jsonl", split="train")

# 4. Formater les prompts
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    responses = examples["response"]
    texts = []
    for instruction, response in zip(instructions, responses):
        text = f"### Instruction:\n{instruction}\n\n### Response:\n{response}"
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(formatting_prompts_func, batched=True)

# 5. Configurer l'entraînement
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=3,  # 3-5 epochs pour LoRA
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir="outputs_biomistral_lora",
        report_to="none",  # ou "wandb" si vous voulez logger
    ),
)

# 6. Lancer l'entraînement
trainer.train()

# 7. Sauvegarder le modèle fine-tuné
model.save_pretrained("biomistral_clinical_lora")
tokenizer.save_pretrained("biomistral_clinical_lora")

# 8. (Optionnel) Merger LoRA avec le modèle de base pour déploiement
model.save_pretrained_merged("biomistral_clinical_merged", tokenizer, save_method="merged_16bit")
```

### Temps d'Entraînement Estimés

- **GPU T4 (Colab gratuit)** : ~2-3h pour 100 exemples, 3 epochs
- **GPU 4090** : ~30-45min
- **GPU A100** : ~15-20min

## Intégration dans Ollama

### Option A : Convertir le modèle fine-tuné en format GGUF (recommandé)

```bash
# 1. Installer llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# 2. Convertir le modèle PyTorch en GGUF
python convert.py /path/to/biomistral_clinical_merged --outfile biomistral_clinical.gguf --outtype q8_0

# 3. Créer un Modelfile pour Ollama
cat > Modelfile <<EOF
FROM ./biomistral_clinical.gguf

PARAMETER temperature 0.0
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM """Tu es un assistant médical spécialisé dans l'aide à la prescription d'imagerie pour les céphalées. 
Tu dois TOUJOURS répondre en français et commencer ta réponse par "Pour préciser:" ou "Recommandation:".
"""
EOF

# 4. Créer le modèle dans Ollama
ollama create biomistral-clinical -f Modelfile
```

### Option B : Utiliser le modèle directement depuis HuggingFace

Si vous hébergez votre modèle sur HuggingFace, vous pouvez modifier `ollama.py` pour charger via transformers :

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "votre-username/biomistral-clinical-lora"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_name)

def generate_response(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.0)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## Évaluation du Modèle Fine-Tuné

### Métriques à Suivre

1. **Format Compliance Rate** : % de réponses commençant par "Pour préciser:" ou "Recommandation:"
2. **Question Accuracy** : % de cas courts où les 3 questions sont posées
3. **Red Flag Detection** : % de cas avec red flags correctement identifiés
4. **False Positive Rate** : % de cas sans red flags incorrectement classés comme urgents

### Script d'Évaluation

Utilisez le script `test_scenarios.py` existant et ajoutez :

```python
def evaluate_model(model_name: str, test_cases: list):
    results = {
        "format_compliance": 0,
        "question_accuracy": 0,
        "red_flag_detection": 0,
        "false_positives": 0
    }
    
    for case in test_cases:
        response = rag_biomistral_query(case["input"], collection, temperature=0.0)
        
        # Check format
        if response.startswith(("Pour préciser:", "Recommandation:")):
            results["format_compliance"] += 1
        
        # Check question accuracy (pour cas courts)
        if case["expected_type"] == "clarify":
            if response.startswith("Pour préciser:") and all(q in response for q in ["caractère", "fièvre", "enceinte"]):
                results["question_accuracy"] += 1
        
        # Check red flag detection
        if case["has_red_flags"] and "urgence" in response.lower():
            results["red_flag_detection"] += 1
        elif not case["has_red_flags"] and "urgence" not in response.lower():
            results["false_positives"] += 1
    
    # Calculate percentages
    total = len(test_cases)
    for key in results:
        results[key] = (results[key] / total) * 100
    
    return results
```

## Bonnes Pratiques

### 1. Augmentation des Données

Créez des variations de chaque exemple :
- Reformulations ("patient" → "patiente", "céphalées" → "maux de tête")
- Ordre différent des informations
- Négations ("pas de fièvre" vs "absence de fièvre")

### 2. Équilibrage du Dataset

Assurez-vous d'avoir une distribution équilibrée :
- 40-50% exemples "Pour préciser:"
- 50-60% exemples "Recommandation:" (dont 50% urgence, 50% non-urgence)

### 3. Validation Set

Séparez 20% de vos données pour validation :
```python
from sklearn.model_selection import train_test_split

train_data, val_data = train_test_split(dataset, test_size=0.2, random_state=42)
```

### 4. Early Stopping

Surveillez la loss de validation et arrêtez si elle augmente (overfitting).

## Ressources Supplémentaires

- [Unsloth Documentation](https://github.com/unslothai/unsloth/wiki)
- [Axolotl Examples](https://github.com/OpenAccess-AI-Collective/axolotl/tree/main/examples)
- [HuggingFace PEFT Guide](https://huggingface.co/docs/peft)
- [Ollama Model Creation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)

## Coût Estimé

### Cloud GPU (si pas de GPU local)

- **Google Colab Pro** : 10€/mois (GPU T4, suffisant pour LoRA)
- **Paperspace Gradient** : ~0.50€/h (GPU A4000)
- **Lambda Labs** : ~0.60€/h (GPU A6000)

### Temps Total

- Préparation données : 2-4h
- Fine-tuning : 1-3h (selon GPU)
- Évaluation : 1h
- **Total** : 1 journée de travail

## Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs d'entraînement pour détecter overfitting (loss validation vs train)
2. Réduisez le learning rate si la loss oscille
3. Augmentez le nombre d'epochs si la loss ne converge pas
4. Consultez les issues GitHub des outils utilisés

---

**Prochaine étape recommandée** : Exécutez `prepare_finetuning_data.py` pour générer votre premier dataset d'entraînement, puis lancez le fine-tuning avec Unsloth sur Google Colab.
