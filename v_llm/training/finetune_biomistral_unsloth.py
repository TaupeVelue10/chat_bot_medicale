"""
finetune_biomistral_unsloth.py - Script de fine-tuning BioMistral avec Unsloth (LoRA)

Prérequis:
- GPU CUDA (recommandé : T4, 4090, A100)
- Unsloth installé (voir instructions ci-dessous)
- Dataset préparé (clinical_cases_train.jsonl)

Installation Unsloth:
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps "xformers<0.0.27" trl peft accelerate bitsandbytes

Usage:
python finetune_biomistral_unsloth.py --model_name BioMistral/BioMistral-7B --train_file clinical_cases_train.jsonl --val_file clinical_cases_val.jsonl --output_dir biomistral_clinical_lora
"""

import argparse
import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune BioMistral avec Unsloth LoRA")
    parser.add_argument("--model_name", type=str, default="BioMistral/BioMistral-7B",
                        help="Nom ou chemin du modèle de base")
    parser.add_argument("--train_file", type=str, default="clinical_cases_train.jsonl",
                        help="Fichier JSONL d'entraînement")
    parser.add_argument("--val_file", type=str, default="clinical_cases_val.jsonl",
                        help="Fichier JSONL de validation")
    parser.add_argument("--output_dir", type=str, default="biomistral_clinical_lora",
                        help="Répertoire de sortie pour le modèle fine-tuné")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                        help="Longueur maximale de séquence")
    parser.add_argument("--lora_r", type=int, default=16,
                        help="Rang LoRA (8-32 recommandé)")
    parser.add_argument("--lora_alpha", type=int, default=16,
                        help="Alpha LoRA")
    parser.add_argument("--learning_rate", type=float, default=2e-4,
                        help="Learning rate")
    parser.add_argument("--num_train_epochs", type=int, default=3,
                        help="Nombre d'epochs")
    parser.add_argument("--batch_size", type=int, default=2,
                        help="Batch size par device")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4,
                        help="Étapes d'accumulation de gradient")
    return parser.parse_args()


def formatting_prompts_func(examples):
    """Formate les exemples au format attendu par le modèle."""
    instructions = examples["instruction"]
    responses = examples["response"]
    texts = []
    for instruction, response in zip(instructions, responses):
        # Format Alpaca-style
        text = f"""### Instruction:
{instruction}

### Response:
{response}"""
        texts.append(text)
    return {"text": texts}


def main():
    args = parse_args()
    
    print("="*70)
    print("FINE-TUNING BIOMISTRAL AVEC UNSLOTH (LoRA)")
    print("="*70)
    print(f"\nModèle de base: {args.model_name}")
    print(f"Fichier train: {args.train_file}")
    print(f"Fichier validation: {args.val_file}")
    print(f"Output: {args.output_dir}")
    print(f"LoRA rank: {args.lora_r}")
    print(f"Learning rate: {args.learning_rate}")
    print(f"Epochs: {args.num_train_epochs}\n")
    
    # 1. Charger le modèle avec Unsloth
    print("📥 Chargement du modèle...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_name,
        max_seq_length=args.max_seq_length,
        dtype=None,  # auto-détection (float16 ou bfloat16)
        load_in_4bit=True,  # quantization 4-bit pour économiser mémoire
    )
    
    # 2. Configurer LoRA
    print("🔧 Configuration LoRA...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", 
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=args.lora_alpha,
        lora_dropout=0.0,  # Unsloth recommande 0 pour optimisation
        bias="none",
        use_gradient_checkpointing="unsloth",  # optimisation mémoire
        random_state=42,
    )
    
    # 3. Charger les datasets
    print("📂 Chargement des datasets...")
    train_dataset = load_dataset("json", data_files=args.train_file, split="train")
    val_dataset = load_dataset("json", data_files=args.val_file, split="train")
    
    print(f"  Train: {len(train_dataset)} exemples")
    print(f"  Validation: {len(val_dataset)} exemples")
    
    # 4. Formater les prompts
    train_dataset = train_dataset.map(formatting_prompts_func, batched=True)
    val_dataset = val_dataset.map(formatting_prompts_func, batched=True)
    
    # 5. Configurer l'entraînement
    print("\n⚙️  Configuration de l'entraînement...")
    
    training_args = TrainingArguments(
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_steps=10,
        num_train_epochs=args.num_train_epochs,
        learning_rate=args.learning_rate,
    fp16=False,
    bf16=False,
        logging_steps=10,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir=args.output_dir,
        eval_strategy="epoch",  # évaluation à chaque epoch (changé de evaluation_strategy)
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
        report_to="none",  # ou "wandb" si vous voulez logger sur Weights & Biases
    )
    
    trainer_kwargs = dict(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        args=training_args,
    )

    trainer = None
    trainer_attempts = [
        {"tokenizer": tokenizer, "dataset_text_field": "text"},
        {"processing_class": tokenizer, "dataset_text_field": "text"},
        {"tokenizer": tokenizer},
        {"processing_class": tokenizer},
    ]

    last_exc = None
    for extra_kwargs in trainer_attempts:
        try:
            trainer = SFTTrainer(**trainer_kwargs, **extra_kwargs)
            break
        except TypeError as exc:
            last_exc = exc
    if trainer is None:
        raise last_exc
    
    # 6. Lancer l'entraînement
    print("\n🚀 Démarrage du fine-tuning...\n")
    trainer.train()
    
    # 7. Sauvegarder le modèle
    print("\n💾 Sauvegarde du modèle fine-tuné...")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # 8. (Optionnel) Merger LoRA avec le modèle de base pour déploiement
    print("🔗 Merge LoRA avec le modèle de base...")
    merged_output = f"{args.output_dir}_merged"
    model.save_pretrained_merged(merged_output, tokenizer, save_method="merged_16bit")
    
    print("\n" + "="*70)
    print("✅ FINE-TUNING TERMINÉ")
    print("="*70)
    print(f"\nModèle LoRA sauvegardé: {args.output_dir}")
    print(f"Modèle merged sauvegardé: {merged_output}")
    print("\nProchaines étapes:")
    print("1. Testez le modèle avec test_scenarios.py")
    print("2. Convertissez en GGUF pour Ollama (voir FINE_TUNING_GUIDE.md)")
    print("3. Créez un Modelfile et ajoutez à Ollama\n")


if __name__ == "__main__":
    main()
