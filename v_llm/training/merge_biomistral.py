from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Chemins à adapter selon ton organisation
base_model_path = "/Users/alexpeirano/Desktop/commande_entreprise/BioMistral-7B"  # Dossier du modèle HuggingFace
lora_adapters_path = "/Users/alexpeirano/Desktop/commande_entreprise/v_llm/models/biomistral_clinical_lora_v2"  # Dossier dézippé des adapters

# Charger le modèle de base
model = AutoModelForCausalLM.from_pretrained(base_model_path, torch_dtype="auto")
tokenizer = AutoTokenizer.from_pretrained(base_model_path)

# Appliquer les adapters LoRA
model = PeftModel.from_pretrained(model, lora_adapters_path)
model = model.merge_and_unload()

# Sauvegarder le modèle fusionné
output_dir = "../models/biomistral_clinical_lora_v2_merged"
model.save_pretrained(output_dir, safe_serialization=True)
tokenizer.save_pretrained(output_dir)