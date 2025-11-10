import re
import unicodedata
import readchar
from datetime import datetime

# seuils de grossesses en semaine
GROSSESSE_EARLY_THRESHOLD = 4  
GROSSESSE_FIRST_TRIMESTER = 12  
GROSSESSE_MAX_WEEKS = 45

# si jamais l'input utilisateur n'est pas un int -> on demande si il se situe dans ces 3 catégories 
# < 3, <8 ou <16 semaines
GROSSESSE_EXAMPLE_LT4 = 3
GROSSESSE_EXAMPLE_4_12 = 8
GROSSESSE_EXAMPLE_GT12 = 16

def analyse_texte_medical(texte):
    """Analyse le texte libre du médecin pour extraire les informations détectées.

    Améliorations :
    - normalisation ASCII (suppression des accents) pour faire des recherches plus robustes,
    - utilisation de motifs avec bornes de mots et groupes nommés,
    - contrôles de plausibilité sur les valeurs numériques extraites.
    """
    # Normaliser le texte pour les recherches : enlever les accents et travailler en ascii minuscule
    t_norm = unicodedata.normalize("NFKD", texte)
    t_norm = t_norm.encode("ascii", "ignore").decode("ascii").lower()

    # Précompiler patterns
    age_re = re.compile(r"\b(?P<age>\d{1,3})\s*ans?\b")
    preg_detect_re = re.compile(r"\b(?:enceinte|grossesse|gestation)\b")
    sem_re = re.compile(r"\b(?:enceinte|grossesse).*?(?P<weeks>\d{1,2})\s*(?:sem(?:aines?)?|sa|semaine)\b")
    mois_re = re.compile(r"\b(?:enceinte|grossesse).*?(?P<months>\d{1,2})\s*mois\b")

    # Age
    age_match = age_re.search(t_norm)
    age = int(age_match.group('age')) if age_match else None
    if age is not None and not (0 <= age <= 120):
        age = None

    # detection du sexe
    if re.search(r"\bpatiente\b", t_norm):
        sexe = "f"
    elif re.search(r"\bpatient\b", t_norm):
        sexe = "m"
    else:
        sexe = None

    # Détection grossesse et extraction durée
    grossesse_detectee = bool(preg_detect_re.search(t_norm))
    sem_match = sem_re.search(t_norm)
    mois_match = mois_re.search(t_norm)
    semaines = None
    if sem_match:
        try:
            semaines = int(sem_match.group('weeks'))
        except (ValueError, TypeError):
            semaines = None
    elif mois_match:
        try:
            mois = int(mois_match.group('months'))
            semaines = mois * 4
        except (ValueError, TypeError):
            semaines = None
    if semaines is not None and not (0 <= semaines <= 45):
        semaines = None

    # Détections binaires (patterns ascii simplifiés)
    return {
        "age": age,
        "sexe": sexe,
        "grossesse": grossesse_detectee,
        "grossesse_sem": semaines,
    # fièvre / fébrile / febrile
    "fievre": bool(re.search(r"\b(?:fievre|febrile|febr|fiev)\b", t_norm)),
    # détecte 'brutal', 'brutale', 'brutales' et l'expression 'coup de tonnerre'
    "brutale": bool(re.search(r"\b(?:brutal\w*|coup de tonnerre)\b", t_norm)),
    # déficit moteur / paralysie / paresie / hémiplégie / troubles sensitifs
    "deficit": bool(re.search(r"\b(?:deficit|deficitaire|paralys(?:ie|is)?|paresi(?:e)?|hemipleg(?:ie)?|trouble moteur|trouble sensitif)\b", t_norm)),
    # oncologie / cancer / tumeur / métastase
    "oncologique": bool(re.search(r"\b(?:cancer|oncolog|tumeur|metast)\b", t_norm)),
    # chirurgie, opératoire, matériel, prothèse, ostéosynthèse, postop
    "chirurgie": bool(re.search(r"\b(?:chirurg|oper(?:at(?:ion|oire))?|materiel|prothese|osteosynth|postop|postoperatoire)\b", t_norm)),
    # pacemaker / pace-maker / stimulateur
    "pacemaker": bool(re.search(r"\b(?:pace[- _]?maker|pacemaker|stimulateur)\b", t_norm)),
    # claustrophobie*
    "claustrophobie": bool(re.search(r"\bclaustro\w*\b", t_norm)),
    # vertige / vertiges
    "vertige": bool(re.search(r"\bvertig\w*\b", t_norm))
    }

def decision_imagerie(f):
    """Recommandation clinique rédigée."""
    texte = ""

    # Sujet neutre pour les recommandations
    sujet = "La personne"

    if f["fievre"] or f["brutale"] or f["deficit"] or f["vertige"]:
        # Construire une description précise : privilégier 'fébrile' ou 'brutale' selon le signe
        adjs = []
        if f["fievre"]:
            adjs.append("fébrile")
        if f["brutale"]:
            adjs.append("brutale")

        # ajouter détails neurologiques si présents
        extras = []
        if f["deficit"]:
            extras.append("déficit neurologique")
        if f["vertige"]:
            extras.append("vertige")

        if adjs:
            headline = "céphalée " + " et ".join(adjs)
        else:
            headline = "céphalée"

        if extras:
            headline = f"{headline} (" + ", ".join(extras) + ")"

        texte += (
            f"{sujet} présente une {headline} évoquant une situation d’urgence. "
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

# fonction principale -> affiche dans le terminal et ouvre une input box
def chatbot_cephalees():
    print("\nAIDE À LA PRESCRIPTION\n")

    texte = input("Médecin : ").strip()
    f = analyse_texte_medical(texte)

    if f["age"]:
        print(f"Âge détecté : {f['age']} ans")
    if f["sexe"]:
        print(f"Sexe détecté : {'femme' if f['sexe']=='f' else 'homme'}")

# ici sous forme de tuple avec la key f qui correspond au return de analyse_texte_medicale et le texte qui est la question à poser
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

    i = 0
    while i < len(questions):
        key, q = questions[i]
        if f[key]:
            i += 1
            continue

        # éviter les cas illogiques (homme ou femme ménopausée enceinte)
        if key == "grossesse" and ((f["sexe"] == "m") or (f["age"] and f["age"] >= 50)):
            f["grossesse"] = False
            i += 1
            continue
        # retour en arrière possible 
        r = demander_oui_non(q)
        if r == "back":
            i = max(0, i - 1)
            continue
        f[key] = r

        if key == "grossesse" and r:
            # Demander le nombre exact de semaines si possible, sinon proposer des catégories
            print("\nDurée de la grossesse :")
            raw = input("Nombre de semaines (laisser vide si inconnu) : ").strip()
            if raw:
                try:
                    w = int(raw)
                    if 0 <= w <= GROSSESSE_MAX_WEEKS:
                        f["grossesse_sem"] = w
                    else:
                        print(f"Nombre de semaines hors plage (0-{GROSSESSE_MAX_WEEKS}), valeur ignorée.")
                        f["grossesse_sem"] = None
                except ValueError:
                    # entrée non numérique -> retomber sur des catégories 
                    if demander_oui_non("Moins de 4 semaines ?") == True:
                        f["grossesse_sem"] = GROSSESSE_EXAMPLE_LT4
                    elif demander_oui_non("Entre 4 et 12 semaines ?") == True:
                        f["grossesse_sem"] = GROSSESSE_EXAMPLE_4_12
                    else:
                        f["grossesse_sem"] = GROSSESSE_EXAMPLE_GT12
            else:
                # utilisateur n'a pas fourni de nombre -> proposer des choix rapides
                if demander_oui_non("Moins de 4 semaines ?") == True:
                    f["grossesse_sem"] = GROSSESSE_EXAMPLE_LT4
                elif demander_oui_non("Entre 4 et 12 semaines ?") == True:
                    f["grossesse_sem"] = GROSSESSE_EXAMPLE_4_12
                else:
                    f["grossesse_sem"] = GROSSESSE_EXAMPLE_GT12
        i += 1

    print("\nSYNTHÈSE CLINIQUE")
    if f["sexe"]:
        print(f"  Sexe : {'femme' if f['sexe']=='f' else 'homme'}")
    if f["age"]:
        print(f"  Âge : {f['age']} ans")
    # Afficher la grossesse uniquement si le sujet est une femme
    if f.get("sexe") == "f" and f.get("grossesse") and f.get("grossesse_sem"):
        print(f"  Grossesse : {f['grossesse_sem']} semaines")

    for k, v in f.items():
        # On exclut les champs déjà affichés 
        if k in ["age", "sexe", "grossesse", "grossesse_sem"]:
            continue
        if v:
            print(f"  - {k}")

    print("\nRECOMMANDATION FINALE")
    print(decision_imagerie(f))
    afficher_contraindications(f)

    # Construire un rapport texte récapitulatif 
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
    # n'ajouter la ligne grossesse que pour les patientes
    if f.get("grossesse") is True and f.get("sexe") == "f":
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
