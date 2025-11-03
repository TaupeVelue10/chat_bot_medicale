import re
import readchar
from datetime import datetime

def analyse_texte_medical(texte):
    """Analyse le texte libre du médecin pour extraire les informations détectées."""
    t = texte.lower()
    age_match = re.search(r"(\d{1,3})\s*ans", t)
    age = int(age_match.group(1)) if age_match else None

    if "patiente" in t:
        sexe = "f"
    elif "patient" in t:
        sexe = "m"
    else:
        sexe = None

    grossesse_detectee = bool(re.search(r"enceinte|grossesse|gestation", t))
    sem_match = re.search(r"(?:enceinte|grossesse).*?(\d{1,2})\s*(?:sem|semaine|sa)", t)
    mois_match = re.search(r"(?:enceinte|grossesse).*?(\d{1,2})\s*mois", t)
    semaines = None
    if sem_match:
        semaines = int(sem_match.group(1))
    elif mois_match:
        semaines = int(mois_match.group(1)) * 4

    return {
        "age": age,
        "sexe": sexe,
        "grossesse": grossesse_detectee,
        "grossesse_sem": semaines,
        "fievre": bool(re.search(r"fièv|fiev|fébr", t)),
        "brutale": bool(re.search(r"brutal|coup de tonnerre", t)),
        "deficit": bool(re.search(r"déficit|paralys|hémiplég|trouble moteur|trouble sensitif", t)),
        "oncologique": bool(re.search(r"cancer|oncolog|tumeur|métast", t)),
        "chirurgie": bool(re.search(r"chirurg|opér|matériel|prothèse|ostéosynth", t)),
        "pacemaker": bool(re.search(r"pace.?maker|stimulateur", t)),
        "claustrophobie": bool(re.search(r"claustro", t)),
        "vertige": bool(re.search(r"vertig", t))
    }

def decision_imagerie(f):
    """Recommandation clinique rédigée."""
    texte = ""

    if f["fievre"] or f["brutale"] or f["deficit"] or f["vertige"]:
        texte += (
            "Le patient présente une céphalée fébrile ou brutale évoquant une situation d’urgence. "
            "Il est recommandé de l’adresser sans délai aux urgences pour la réalisation d’un scanner cérébral sans injection. "
        )
        if f["grossesse"]:
            if f["grossesse_sem"] and f["grossesse_sem"] < 4:
                texte += (
                    "Toutefois, la grossesse étant inférieure à 4 semaines, "
                    "le scanner est contre-indiqué. Il convient d’en discuter avec le service de radiologie pour une prise en charge adaptée."
                )
            elif f["grossesse_sem"] and f["grossesse_sem"] < 12:
                texte += (
                    "La grossesse étant inférieure à 3 mois, "
                    "le scanner ne doit être envisagé qu’en cas d’urgence vitale, en concertation avec la radiologie."
                )
            else:
                texte += (
                    "La grossesse étant supérieure à 12 semaines, "
                    "le scanner peut être réalisé sous les précautions habituelles."
                )
        return texte

    if f["oncologique"]:
        return (
            "Dans le cadre d’un contexte oncologique, "
            "la réalisation d’un scanner cérébral avec injection est indiquée en première intention."
        )

    if f["grossesse"]:
        if f["grossesse_sem"] and f["grossesse_sem"] < 4:
            return (
                "Le scanner est contre-indiqué en raison d’une grossesse débutante "
                "(moins de 4 semaines). Il convient de différer l’examen ou de privilégier une approche alternative."
            )
        elif f["grossesse_sem"] and f["grossesse_sem"] < 12:
            return (
                "L’IRM est contre-indiquée avant 3 mois de grossesse. "
                "Un scanner pourra être envisagé uniquement en cas d’urgence vitale, après avis spécialisé."
            )
        else:
            return (
                "La grossesse étant supérieure à 3 mois, "
                "les examens d’imagerie peuvent être réalisés selon l’indication clinique."
            )

    if f["chirurgie"]:
        return (
            "Une chirurgie récente avec pose de matériel métallique (<6 semaines) a été signalée. "
            "L’IRM est contre-indiquée jusqu’à la 6e semaine postopératoire."
        )

    if f["pacemaker"]:
        return (
            "La présence d’un pacemaker impose de vérifier la compatibilité du dispositif avant toute IRM."
        )

    texte = (
        "En l’absence de critère de gravité ou de contre-indication, "
        "une IRM cérébrale sans injection est recommandée en première intention. "
        "Un scanner pourra être envisagé si l’IRM est contre-indiquée ou non réalisable."
    )
    return texte

def afficher_contraindications(f):
    """Affiche les rappels en style fluide."""
    print(get_contraindications_text(f))


def get_contraindications_text(f):
    """Retourne le texte des remarques/contre-indications pour affichage et export."""
    lines = []
    lines.append("Remarques complémentaires :")
    if f["sexe"] == "f" and (not f["age"] or f["age"] < 50):
        if f.get("grossesse_sem") and f.get("grossesse_sem") < 4:
            lines.append("• Le scanner est strictement contre-indiqué pour une grossesse débutante (<4 semaines).")
        else:
            lines.append("• Chez les femmes de moins de 50 ans, un test de grossesse est recommandé avant tout examen radiologique.")
    lines.append("• Chez les patients de plus de 60 ans ou ayant des antécédents rénaux, un dosage de la créatinine est nécessaire avant injection de produit de contraste.")
    lines.append("• En cas d’allergie, signaler toute réaction préalable, mais les allergies aux crustacés ou à la Bétadine ne constituent pas une contre-indication au scanner iodé.")
    return "\n".join(lines)


def save_report(report_text, filename=None):
    """Enregistre le texte `report_text` dans un fichier .txt (UTF-8).
    Si `filename` est None ou vide, génère un nom basé sur la date/heure.
    Retourne le chemin du fichier créé.
    """
    import os
    # Créer le dossier reports si nécessaire
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rapport_cephalees_{ts}.txt"

    # Si l'utilisateur a fourni un nom simple, l'enregistrer dans reports/
    if not os.path.isabs(filename):
        filename = os.path.join(reports_dir, filename)

    with open(filename, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    return os.path.abspath(filename)

def demander_oui_non(prompt):
    """Lecture directe d'une touche (o/n ou ← retour)."""
    print(prompt + " (o/n) : ", end="", flush=True)
    while True:
        key = readchar.readkey()
        if key.lower() == "o":
            print("o")
            return True
        elif key.lower() == "n":
            print("n")
            return False
        elif key == readchar.key.LEFT:
            print("\n⬅ Retour à la question précédente.")
            return "back"

def chatbot_cephalees():
    print("\nAIDE À LA PRESCRIPTION\n")

    texte = input("Médecin : ").strip()
    f = analyse_texte_medical(texte)

    if f["age"]:
        print(f"Âge détecté : {f['age']} ans")
    if f["sexe"]:
        print(f"Sexe détecté : {'femme' if f['sexe']=='f' else 'homme'}")

    questions = [
        ("fievre", "Fièvre ?"),
        ("brutale", "Installation brutale (coup de tonnerre) ?"),
        ("deficit", "Déficit moteur ou sensitif ?"),
        ("oncologique", "Antécédent de cancer ?"),
        ("grossesse", "Grossesse en cours ?"),
        ("chirurgie", "Chirurgie récente (<6 semaines avec matériel) ?"),
        ("pacemaker", "Pace-maker ?"),
        ("claustrophobie", "Claustrophobie ?")
    ]

    # Info pour l'utilisateur : les signes détectés automatiquement seront affichés
    # à l'écran. Si vous souhaitez modifier une réponse, utilisez la flèche gauche
    # lors d'une question pour revenir à la question précédente.
    print("\nRemarque : les signes détectés automatiquement sont affichés ;\nsi vous voulez corriger une détection, utilisez la flèche gauche lors d'une question pour revenir en arrière.")

    i = 0
    while i < len(questions):
        key, q = questions[i]

        # Si la grossesse est impossible (homme ou age >=50), on la marque False et on passe
        if key == "grossesse" and ((f["sexe"] == "m") or (f["age"] and f["age"] >= 50)):
            f["grossesse"] = False
            i += 1
            continue

        # Si un signe a été détecté automatiquement depuis le texte libre,
        # l'afficher et passer sans demander de confirmation (évite la redondance).
        if f.get(key):
            print(f"(Détection automatique depuis le texte) {q} détecté.")
            i += 1
            continue

        # Sinon, poser la question normalement.
        r = demander_oui_non(q)
        if r == "back":
            i = max(0, i - 1)
            continue
        f[key] = r

        if key == "grossesse" and r:
            print("\nDurée de la grossesse :")
            if demander_oui_non("Moins de 4 semaines ?") == True:
                f["grossesse_sem"] = 3
            elif demander_oui_non("Entre 4 et 12 semaines ?") == True:
                f["grossesse_sem"] = 8
            else:
                f["grossesse_sem"] = 16
        i += 1

    print("\nSYNTHÈSE CLINIQUE")
    if f["sexe"]:
        print(f"  Sexe : {'femme' if f['sexe']=='f' else 'homme'}")
    if f["age"]:
        print(f"  Âge : {f['age']} ans")
    if f["grossesse"] and f["grossesse_sem"]:
        print(f"  Grossesse : {f['grossesse_sem']} semaines")

    for k, v in f.items():
        # On exclut les champs déjà affichés ou redondants
        if k in ["age", "sexe", "grossesse", "grossesse_sem"]:
            continue
        if v:
            print(f"  - {k}")

    print("\nRECOMMANDATION FINALE")
    print(decision_imagerie(f))
    afficher_contraindications(f)

    # Construire un rapport texte récapitulatif (formaté)
    now = datetime.now()
    hdr = []
    hdr.append("========================================")
    hdr.append("ASSISTANT MÉDICAL")
    hdr.append(now.strftime("Date : %Y-%m-%d    Heure : %H:%M:%S"))
    hdr.append("========================================")

    body = []
    body.append("CLINICIEN — TEXTE FOURNI:")
    body.append(texte)
    body.append("")
    body.append("INFORMATIONS DÉTECTÉES:")
    if f.get("age"):
        body.append(f"- Âge : {f['age']} ans")
    if f.get("sexe"):
        body.append(f"- Sexe : {'femme' if f['sexe']=='f' else 'homme'}")
    if f.get("grossesse") is True:
        gs = f.get("grossesse_sem") or "inconnue"
        body.append(f"- Grossesse : oui ({gs} semaines)")
    # autres signes
    signs = [k for k, v in f.items() if k not in ["age", "sexe", "grossesse", "grossesse_sem"] and v]
    if signs:
        body.append("- Signes/antécédents :")
        for s in signs:
            body.append(f"    • {s}")
    else:
        body.append("- Signes/antécédents : aucun détecté")

    body.append("")
    body.append("RECOMMANDATION :")
    body.append(decision_imagerie(f))

    body.append("")
    body.append("CONTRE-INDICATIONS / REMARQUES :")
    body.append(get_contraindications_text(f))

    report_text = "\n".join(hdr + ["\n"] + body)

    # Proposer l'enregistrement/impression
    if demander_oui_non("Voulez-vous imprimer le résultat"):
        fname = input("Nom du fichier (laisser vide pour générer automatiquement) : ").strip()
        saved_path = save_report(report_text, fname if fname else None)
        print(f"Rapport enregistré : {saved_path}")

if __name__ == "__main__":
    chatbot_cephalees()
