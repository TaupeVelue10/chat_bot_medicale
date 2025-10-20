"""
generate_finetune_dataset.py

Génère un dataset étendu pour fine-tuning de BioMistral.
- Lit `prepare_finetuning_data.py` si présent pour réutiliser exemples existants
- Génère variations par templates pour atteindre ~200 exemples (train/val 80/20)

Usage:
python generate_finetune_dataset.py --n 200
"""
import argparse
import json
import random
from pathlib import Path

random.seed(42)

# Small templates for instructions and responses by category
TEMPLATES = {
    "short_case": [
        ("Patient {} ans, {}", "Pour préciser: De quel côté/localisation ? Durée ? Signes associés ?"),
    ],
    "red_flags": [
        ("Patient {} ans, céphalée {} depuis {}, avec {}",
         "Recommandation: IRM cérébrale en urgence (<24h). Justification: présence de signes d'alerte ({})."),
    ],
    "no_red_flags": [
        ("Patient {} ans, céphalées {} depuis {}, sans signes d'alerte",
         "Recommandation: Pas d'imagerie en première intention; traitement symptomatique et suivi.")
    ],
    "ambiguous": [
        ("Patient {} ans, céphalée {}, antécédent {}",
         "Pour préciser: Durée ? Fièvre/vomissements/convulsions ? Antécédents détaillés ?")
    ],
    "negations": [
        ("Patient {} ans, céphalée {} depuis {}, PAS de fièvre, PAS de vomissements",
         "Recommandation: Pas d'imagerie en première intention; surveillance clinique.")
    ],
    "pregnancy": [
        ("Patiente {} ans, enceinte {}SA, céphalées {} depuis {}, TA {}",
         "Recommandation: IRM cérébrale SANS gadolinium en semi-urgence; éliminer pré-éclampsie.")
    ],
    "immuno": [
        ("Patient {} ans, immunodéprimé ({}), fièvre {}, confusion {}",
         "Recommandation: IRM cérébrale urgente avec injection; envisager PL après élimination d'effet de masse.")
    ],
    "trauma": [
        ("Patient {} ans, traumatisme crânien, perte de connaissance {}, vomissements {}",
         "Recommandation: Scanner cérébral sans injection en urgence.")
    ],
}

DURATIONS = ["2 heures", "4 heures", "12 heures", "1 jour", "2 jours", "3 jours", "1 semaine", "2 semaines"]
CHARACTER = ["brutale", "intense", "progressive", "soudaine", "oppressive"]
ASSOCIATED = ["vomissements", "fièvre", "perte de connaissance", "convulsions", "déficit neurologique"]
IMMUNO = ["VIH", "chimiothérapie", "greffe", "cancer avancé"]

def gen_examples(n=200):
    examples = []
    categories = [
        ("red_flags", 0.35),
        ("no_red_flags", 0.2),
        ("pregnancy", 0.08),
        ("immuno", 0.08),
        ("trauma", 0.07),
        ("ambiguous", 0.07),
        ("negations", 0.08),
        ("short_case", 0.07),
    ]
    weights = [c[1] for c in categories]
    cat_names = [c[0] for c in categories]

    for i in range(n):
        cat = random.choices(cat_names, weights=weights, k=1)[0]
        tmpl = random.choice(TEMPLATES[cat])
        age = random.randint(1, 90)
        dur = random.choice(DURATIONS)
        char = random.choice(CHARACTER)
        assoc = random.choice(ASSOCIATED)
        imm = random.choice(IMMUNO)
        preg_w = random.randint(6, 38)
        loc = random.choice(["frontale", "hémicrânienne droite", "hémicrânienne gauche", "péri-orbitaire"]) 

        if cat == 'red_flags':
            instr = tmpl[0].format(age, char, dur, assoc)
            resp = tmpl[1].format(assoc)
        elif cat == 'no_red_flags':
            instr = tmpl[0].format(age, char, dur)
            resp = tmpl[1]
        elif cat == 'pregnancy':
            instr = tmpl[0].format(age, preg_w, char, dur, f"{random.randint(110, 140)}/{random.randint(60, 90)}")
            resp = tmpl[1]
        elif cat == 'immuno':
            instr = tmpl[0].format(age, imm, random.choice(["38.5°C", "39°C", "37.8°C"]), random.choice(["confusion modérée", "confusion sévère"]))
            resp = tmpl[1]
        elif cat == 'trauma':
            instr = tmpl[0].format(age, random.choice(["oui", "non"]), random.choice(["oui", "non"]))
            resp = tmpl[1]
        elif cat == 'ambiguous':
            instr = tmpl[0].format(age, char, "antécédent de migraine")
            resp = tmpl[1]
        elif cat == 'negations':
            instr = tmpl[0].format(age, char, dur)
            resp = tmpl[1]
        else:
            instr = tmpl[0].format(age, "céphalée")
            resp = tmpl[1]

        instruction = "Vous êtes un assistant médical expert. Répondez strictement en français.\n\nCas clinique:\n" + instr
        response = resp
        examples.append({
            "instruction": instruction,
            "response": response,
            "category": cat
        })

    return examples


def save_examples(examples, train_ratio=0.8):
    random.shuffle(examples)
    split = int(len(examples) * train_ratio)
    train = examples[:split]
    val = examples[split:]
    train_file = Path(__file__).parent / "clinical_cases_train.jsonl"
    val_file = Path(__file__).parent / "clinical_cases_val.jsonl"
    with open(train_file, 'w', encoding='utf-8') as f:
        for ex in train:
            f.write(json.dumps({"instruction": ex['instruction'], "response": ex['response']}, ensure_ascii=False) + "\n")
    with open(val_file, 'w', encoding='utf-8') as f:
        for ex in val:
            f.write(json.dumps({"instruction": ex['instruction'], "response": ex['response']}, ensure_ascii=False) + "\n")
    print(f"Saved train: {len(train)} examples to {train_file}")
    print(f"Saved val: {len(val)} examples to {val_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=200)
    args = parser.parse_args()
    ex = gen_examples(args.n)
    save_examples(ex)
    print("Done")
