"""
prepare_finetuning_data.py - Génère un dataset JSONL pour fine-tuner BioMistral

Ce script crée des exemples d'entraînement structurés au format attendu par Unsloth/HuggingFace.
"""
import json
from pathlib import Path


def create_training_examples():
    """Génère des exemples d'entraînement pour le fine-tuning."""
    
    examples = []
    
    # ===== CATÉGORIE 1: CAS COURTS → CLARIFICATIONS =====
    
    # Exemple 1.1 : Cas minimal
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 22 ans, céphalées\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Pour préciser: Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ? | Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ? | La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?",
        "category": "short_case",
        "expected_output": "clarify"
    })
    
    # Exemple 1.2 : Variante féminine
    examples.append({
        "instruction": "CAS CLINIQUE:\npatiente 35 ans, maux de tête\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Pour préciser: Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ? | Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ? | La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?",
        "category": "short_case",
        "expected_output": "clarify"
    })
    
    # Exemple 1.3 : Patient âgé
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 68 ans, céphalées\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Pour préciser: Depuis quand et quel caractère ont les céphalées (brutale / intense / progressive) ? | Y a‑t‑il fièvre, vomissements, perte de connaissance, convulsions ou déficit neurologique focal ? | La patiente est‑elle enceinte, a‑t‑elle des antécédents majeurs (cancer, immunodépression) ou un traumatisme crânien récent ?",
        "category": "short_case",
        "expected_output": "clarify"
    })
    
    # ===== CATÉGORIE 2: RED FLAGS → IRM URGENCE =====
    
    # Exemple 2.1 : Déficit neurologique + fièvre
    examples.append({
        "instruction": "CAS CLINIQUE:\npatiente 22 ans, céphalées progressives depuis 2 semaines, déficit neurologique, fièvre, elle n'est pas enceinte\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: IRM cérébrale en urgence — présence de signes d'alerte (déficit neurologique, fièvre) justifiant suspicion de lésion structurelle (AVC, infection, tumeur). Source: HAS/SFETD 2017.",
        "category": "red_flags",
        "expected_output": "urgent_imaging"
    })
    
    # Exemple 2.2 : Céphalée brutale (suspicion hémorragie)
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 45 ans, céphalée brutale d'apparition soudaine depuis 2 heures, vomissements, pas de fièvre, pas d'antécédents\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: IRM cérébrale en urgence (ou scanner si IRM non disponible) — céphalée brutale évoque hémorragie sous-arachnoïdienne. Justification: HAS 2017 / critères Ottawa.",
        "category": "red_flags",
        "expected_output": "urgent_imaging"
    })
    
    # Exemple 2.3 : Traumatisme crânien
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 30 ans, céphalées depuis traumatisme crânien il y a 3 jours, vomissements, pas de perte de connaissance, pas de fièvre\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Scanner cérébral en urgence — traumatisme crânien récent avec vomissements justifie imagerie pour exclure hématome intracrânien. Source: critères canadiens TC.",
        "category": "red_flags",
        "expected_output": "urgent_imaging"
    })
    
    # Exemple 2.4 : Convulsions
    examples.append({
        "instruction": "CAS CLINIQUE:\npatiente 28 ans, céphalées intenses depuis 5 jours, convulsions ce matin, pas de fièvre, pas d'antécédents épilepsie, pas enceinte\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: IRM cérébrale en urgence — première crise convulsive chez adulte avec céphalées justifie recherche de lésion structurelle. Source: SFNC / HAS.",
        "category": "red_flags",
        "expected_output": "urgent_imaging"
    })
    
    # Exemple 2.5 : Patient >50 ans + changement pattern
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 62 ans, céphalées inhabituelles depuis 3 semaines, changement de pattern par rapport à ses migraines habituelles, pas de fièvre, pas de déficit neurologique, antécédent de cancer prostate traité\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: IRM cérébrale en urgence différée (sous 7 jours) — patient >50 ans + antécédent cancer + changement pattern justifient recherche de métastases cérébrales ou autre lésion. Source: HAS 2017.",
        "category": "red_flags",
        "expected_output": "urgent_imaging"
    })
    
    # ===== CATÉGORIE 3: PAS DE RED FLAGS → SURVEILLANCE =====
    
    # Exemple 3.1 : Céphalées progressives, pas de red flags
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 25 ans, céphalées progressives depuis 3 semaines, pas de fièvre, pas de vomissements, pas de déficit neurologique, pas d'antécédents\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Pas d'imagerie en première intention — absence de signes d'alerte. Traitement symptomatique (antalgiques, anti-inflammatoires) et suivi clinique. Refaire évaluation si persistance >4 semaines ou apparition de signes d'alerte. Source: HAS/SFETD 2017.",
        "category": "no_red_flags",
        "expected_output": "surveillance"
    })
    
    # Exemple 3.2 : Migraine probable
    examples.append({
        "instruction": "CAS CLINIQUE:\npatiente 32 ans, céphalées hémicrâniques pulsatiles depuis 2 jours, photophobie, pas de fièvre, pas de déficit neurologique, antécédent de migraines similaires, pas enceinte\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Pas d'imagerie — tableau compatible avec migraine sans aura. Traitement symptomatique (triptans si pas de contre-indication). Imagerie uniquement si changement pattern ou apparition signes d'alerte. Source: SFEMC 2021.",
        "category": "no_red_flags",
        "expected_output": "surveillance"
    })
    
    # Exemple 3.3 : Céphalée tension
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 40 ans, céphalées en casque depuis 1 semaine, pas de photophobie, pas de vomissements, pas de fièvre, contexte de stress professionnel, pas d'antécédents\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Pas d'imagerie — céphalée de tension probable (facteurs de stress, caractère en casque, absence signes d'alerte). Traitement symptomatique + gestion du stress. Réévaluation si persistance >1 mois. Source: HAS/SFETD 2017.",
        "category": "no_red_flags",
        "expected_output": "surveillance"
    })
    
    # ===== CATÉGORIE 4: CAS AMBIGUS (pour enseigner nuances) =====
    
    # Exemple 4.1 : Fièvre isolée (infection ORL possible)
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 28 ans, céphalées depuis 3 jours, fièvre 38.5°C, pas de déficit neurologique, pas de raideur nuque, pas de vomissements, rhinorrhée, pas d'antécédents\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Pas d'imagerie en première intention si absence de signes méningés (raideur nuque, photophobie sévère, troubles conscience) — probable infection ORL. Traitement symptomatique + réévaluation clinique. Imagerie si aggravation ou signes méningés. Source: SPILF.",
        "category": "ambiguous",
        "expected_output": "surveillance_conditional"
    })
    
    # Exemple 4.2 : Grossesse (considérations spécifiques)
    examples.append({
        "instruction": "CAS CLINIQUE:\npatiente 26 ans enceinte (12 SA), céphalées depuis 5 jours, pas de signes visuels, pas de vomissements, tension artérielle normale, pas de protéinurie, pas d'antécédents\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Pas d'imagerie si TA normale et absence signes pré-éclampsie — céphalées fréquentes au 1er trimestre. Traitement symptomatique adapté grossesse (paracétamol). IRM si signes pré-éclampsie ou éclampsie (HTA, protéinurie, troubles visuels). Source: CNGOF.",
        "category": "ambiguous",
        "expected_output": "surveillance_conditional"
    })
    
    # ===== CATÉGORIE 5: NÉGATIONS (apprentissage important) =====
    
    # Exemple 5.1 : Toutes négations
    examples.append({
        "instruction": "CAS CLINIQUE:\npatient 30 ans, céphalées depuis 1 semaine, pas de fièvre, pas de vomissements, pas de convulsions, pas de déficit neurologique, pas de traumatisme, pas d'antécédents\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Pas d'imagerie en première intention — absence complète de signes d'alerte. Traitement symptomatique et suivi ambulatoire. Imagerie uniquement si persistance >4 semaines ou apparition signes d'alerte. Source: HAS/SFETD 2017.",
        "category": "negations",
        "expected_output": "surveillance"
    })
    
    # Exemple 5.2 : Négations multiples
    examples.append({
        "instruction": "CAS CLINIQUE:\npatiente 35 ans, céphalées progressives depuis 2 semaines, absence de fièvre, absence de déficit neurologique, absence de vomissements, elle n'est pas enceinte, sans antécédents\n\nRÉPONDS en français, commence par 'Pour préciser:' ou 'Recommandation:'",
        "response": "Recommandation: Pas d'imagerie en première intention — aucun signe d'alerte identifié. Traitement symptomatique (antalgiques palier 1) et surveillance clinique. Réévaluation si aggravation ou apparition nouveaux symptômes. Source: HAS/SFETD 2017.",
        "category": "negations",
        "expected_output": "surveillance"
    })
    
    return examples


def save_jsonl(examples, output_file="clinical_cases_train.jsonl"):
    """Sauvegarde les exemples au format JSONL."""
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            # Format attendu par les outils de fine-tuning
            record = {
                "instruction": example["instruction"],
                "response": example["response"]
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"✓ Dataset sauvegardé : {output_path}")
    print(f"  Nombre d'exemples : {len(examples)}")
    
    # Statistiques
    categories = {}
    for ex in examples:
        cat = ex.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\nRépartition par catégorie :")
    for cat, count in categories.items():
        pct = (count / len(examples)) * 100
        print(f"  - {cat}: {count} ({pct:.1f}%)")


def create_validation_split(examples, val_ratio=0.2):
    """Crée un split validation à partir des exemples."""
    import random
    random.seed(42)
    
    shuffled = examples.copy()
    random.shuffle(shuffled)
    
    split_idx = int(len(shuffled) * (1 - val_ratio))
    train = shuffled[:split_idx]
    val = shuffled[split_idx:]
    
    return train, val


def main():
    print("=== Génération du Dataset de Fine-Tuning ===\n")
    
    # Générer les exemples
    examples = create_training_examples()
    
    # Créer split train/validation
    train_examples, val_examples = create_validation_split(examples)
    
    # Sauvegarder
    save_jsonl(train_examples, "clinical_cases_train.jsonl")
    save_jsonl(val_examples, "clinical_cases_val.jsonl")
    
    print("\n=== Prochaines étapes ===")
    print("1. Vérifiez les fichiers générés (clinical_cases_train.jsonl, clinical_cases_val.jsonl)")
    print("2. Ajoutez vos propres exemples si nécessaire (variantes, reformulations)")
    print("3. Lancez le fine-tuning avec Unsloth (voir FINE_TUNING_GUIDE.md)")
    print("\nConseil : visez 150-300 exemples au total pour un fine-tuning optimal.")


if __name__ == "__main__":
    main()
