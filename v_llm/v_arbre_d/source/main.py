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
    
    # Remarques spécifiques à la grossesse
    if f["sexe"] == "f" and (not f["age"] or f["age"] < 50):
        if f.get("grossesse_sem") and f.get("grossesse_sem") < 4:
            lines.append("• Le scanner est strictement contre-indiqué pour une grossesse débutante (<4 semaines).")
        elif f.get("grossesse"):
            # Grossesse confirmée : pas besoin de test
            lines.append(f"• Grossesse confirmée ({f.get('grossesse_sem', 'durée précisée')} SA) : précautions d'irradiation à respecter.")
        else:
            # Pas de grossesse connue : recommander le test
            lines.append("• Chez les femmes de moins de 50 ans, un test de grossesse est recommandé avant tout examen radiologique.")
    
    lines.append("• Chez les patients de plus de 60 ans ou ayant des antécédents rénaux, un dosage de la créatinine est nécessaire avant injection de produit de contraste.")
    lines.append("• En cas d'allergie, signaler toute réaction préalable, mais les allergies aux crustacés ou à la Bétadine ne constituent pas une contre-indication au scanner iodé.")
    return "\n".join(lines)


def generer_ordonnance(f, texte_initial, decision, contraindications_text):
    """Génère le contenu d'une ordonnance médicale au format français.
    
    Args:
        f: dictionnaire des informations patient et cliniques
        texte_initial: texte libre du médecin
        decision: recommandation d'imagerie
        contraindications_text: texte des contre-indications
    
    Returns:
        str: contenu formaté de l'ordonnance
    """
    now = datetime.now()
    
    # En-tête de l'ordonnance
    ordonnance = []
    ordonnance.append("=" * 80)
    ordonnance.append(" " * 28 + "ORDONNANCE MÉDICALE")
    ordonnance.append("=" * 80)
    ordonnance.append("")
    
    # Informations du praticien (à personnaliser selon les besoins)
    ordonnance.append("Dr. [NOM DU MÉDECIN]")
    ordonnance.append("[Spécialité]")
    ordonnance.append("[Adresse du cabinet]")
    ordonnance.append("[Code postal et ville]")
    ordonnance.append("Tél : [Numéro de téléphone]")
    ordonnance.append("N° RPPS : [Numéro RPPS]")
    ordonnance.append("")
    ordonnance.append(f"Date : {now.strftime('%d/%m/%Y')}")
    ordonnance.append(f"Heure : {now.strftime('%H:%M')}")
    ordonnance.append("")
    ordonnance.append("-" * 80)
    ordonnance.append("")
    
    # Informations patient
    ordonnance.append("PATIENT(E) :")
    ordonnance.append("")
    ordonnance.append(f"Nom : [À COMPLÉTER]")
    ordonnance.append(f"Prénom : [À COMPLÉTER]")
    if f.get("age"):
        ordonnance.append(f"Âge : {f['age']} ans")
    else:
        ordonnance.append(f"Âge : [À COMPLÉTER]")
    
    if f.get("sexe"):
        sexe_txt = "Féminin" if f['sexe'] == 'f' else "Masculin"
        ordonnance.append(f"Sexe : {sexe_txt}")
    else:
        ordonnance.append(f"Sexe : [À COMPLÉTER]")
    
    ordonnance.append(f"N° Sécurité Sociale : [À COMPLÉTER]")
    ordonnance.append("")
    ordonnance.append("-" * 80)
    ordonnance.append("")
    
    # Motif de consultation
    ordonnance.append("MOTIF DE CONSULTATION :")
    ordonnance.append("")
    ordonnance.append(f"{texte_initial}")
    ordonnance.append("")
    ordonnance.append("-" * 80)
    ordonnance.append("")
    
    # Éléments cliniques recueillis
    ordonnance.append("ÉLÉMENTS CLINIQUES RECUEILLIS :")
    ordonnance.append("")
    
    # Grossesse si applicable
    if f.get("grossesse") is True and f.get("sexe") == "f":
        gs = f.get("grossesse_sem") or "durée non précisée"
        if isinstance(gs, int):
            ordonnance.append(f"• Grossesse en cours : {gs} semaines d'aménorrhée")
        else:
            ordonnance.append(f"• Grossesse en cours : {gs}")
    
    # Signes cliniques et antécédents
    signes_cliniques = []
    if f.get("fievre"):
        signes_cliniques.append("Syndrome fébrile")
    if f.get("brutale"):
        signes_cliniques.append("Installation brutale (céphalée en coup de tonnerre)")
    if f.get("deficit"):
        signes_cliniques.append("Déficit moteur ou sensitif")
    if f.get("vertige"):
        signes_cliniques.append("Vertige")
    if f.get("oncologique"):
        signes_cliniques.append("Antécédent oncologique")
    if f.get("chirurgie"):
        signes_cliniques.append("Chirurgie récente (<6 semaines) avec matériel")
    if f.get("pacemaker"):
        signes_cliniques.append("Porteur de pacemaker")
    if f.get("claustrophobie"):
        signes_cliniques.append("Claustrophobie")
    
    if signes_cliniques:
        for signe in signes_cliniques:
            ordonnance.append(f"• {signe}")
    else:
        ordonnance.append("• Pas de signe de gravité identifié")
    
    ordonnance.append("")
    ordonnance.append("-" * 80)
    ordonnance.append("")
    
    # Raisonnement clinique / Arbre décisionnel
    ordonnance.append("RAISONNEMENT CLINIQUE ET ARBRE DÉCISIONNEL :")
    ordonnance.append("")
    
    # Analyse de la situation
    ordonnance.append("Analyse de la situation :")
    if f["fievre"] or f["brutale"] or f["deficit"] or f["vertige"]:
        ordonnance.append("• Présence de critères d'urgence :")
        if f["fievre"]:
            ordonnance.append("  - Céphalée fébrile → risque de méningite ou d'infection du SNC")
        if f["brutale"]:
            ordonnance.append("  - Installation brutale → risque d'hémorragie méningée")
        if f["deficit"]:
            ordonnance.append("  - Déficit neurologique → risque d'AVC ou de lésion focale")
        if f["vertige"]:
            ordonnance.append("  - Vertige → exploration neurologique nécessaire")
        ordonnance.append("  → Indication à une imagerie en urgence")
    elif f["oncologique"]:
        ordonnance.append("• Contexte oncologique → surveillance des métastases cérébrales")
    elif f["grossesse"]:
        if f.get("grossesse_sem"):
            if f["grossesse_sem"] < 4:
                ordonnance.append("• Grossesse < 4 semaines → contre-indication absolue au scanner")
            elif f["grossesse_sem"] < 12:
                ordonnance.append("• Grossesse < 12 semaines → scanner uniquement si urgence vitale")
                ordonnance.append("• IRM contre-indiquée au 1er trimestre")
            else:
                ordonnance.append("• Grossesse > 12 semaines → imagerie possible avec précautions")
    
    ordonnance.append("")
    ordonnance.append("Choix de l'examen d'imagerie :")
    ordonnance.append(f"{decision}")
    ordonnance.append("")
    ordonnance.append("-" * 80)
    ordonnance.append("")
    
    # Prescription
    ordonnance.append("PRESCRIPTION :")
    ordonnance.append("")
    
    # Déterminer le type d'examen prescrit en fonction des données structurées
    # Vérifier d'abord les contre-indications absolues
    if f.get("grossesse") and f.get("grossesse_sem"):
        if f["grossesse_sem"] < 4:
            # Grossesse < 4 semaines : contre-indication absolue au scanner, IRM aussi
            ordonnance.append("⚠️  AUCUN EXAMEN D'IMAGERIE RECOMMANDÉ")
            ordonnance.append("    Grossesse < 4 semaines : contre-indication au scanner")
            ordonnance.append("    IRM contre-indiquée au 1er trimestre")
            ordonnance.append("    → Surveillance clinique et différer l'imagerie si possible")
        elif f["grossesse_sem"] < 12 and not (f["fievre"] or f["brutale"] or f["deficit"]):
            # Grossesse < 12 semaines SANS urgence
            ordonnance.append("⚠️  IMAGERIE DIFFÉRÉE RECOMMANDÉE")
            ordonnance.append("    Grossesse < 12 semaines sans critère d'urgence vitale")
            ordonnance.append("    Scanner uniquement si urgence vitale (non applicable ici)")
            ordonnance.append("    IRM contre-indiquée au 1er trimestre")
            ordonnance.append("    → Réévaluation après le 1er trimestre")
        elif f["grossesse_sem"] < 12 and (f["fievre"] or f["brutale"] or f["deficit"]):
            # Grossesse < 12 semaines AVEC urgence
            ordonnance.append("☐ SCANNER CÉRÉBRAL SANS INJECTION")
            ordonnance.append("    En URGENCE VITALE (après concertation)")
            ordonnance.append("    Indication : Critères d'urgence avec grossesse < 12 semaines")
            ordonnance.append("    ⚠️  Nécessite avis radiologique et accord de la patiente")
        else:
            # Grossesse >= 12 semaines
            if f["fievre"] or f["brutale"] or f["deficit"]:
                ordonnance.append("☐ SCANNER CÉRÉBRAL SANS INJECTION")
                ordonnance.append("    En urgence")
                ordonnance.append("    Indication : Céphalée aiguë avec critères de gravité")
            else:
                ordonnance.append("☐ IRM CÉRÉBRALE SANS INJECTION")
                ordonnance.append("    Indication : Céphalée sans critère d'urgence (grossesse)")
    elif f["fievre"] or f["brutale"] or f["deficit"] or f["vertige"]:
        # Urgence sans grossesse
        ordonnance.append("☐ SCANNER CÉRÉBRAL SANS INJECTION")
        ordonnance.append("    En urgence")
        ordonnance.append("    Indication : Céphalée aiguë avec critères de gravité")
    elif f["oncologique"]:
        ordonnance.append("☐ SCANNER CÉRÉBRAL AVEC INJECTION")
        ordonnance.append("    Indication : Contexte oncologique, recherche de métastases")
    elif "irm" in decision.lower() and "recommandée" in decision.lower():
        ordonnance.append("☐ IRM CÉRÉBRALE SANS INJECTION")
        ordonnance.append("    Indication : Céphalée sans critère d'urgence")
    else:
        ordonnance.append("☐ [EXAMEN D'IMAGERIE À PRÉCISER]")
        ordonnance.append("    → Consultation médicale pour évaluation")
    
    ordonnance.append("")
    ordonnance.append("-" * 80)
    ordonnance.append("")
    
    # Contre-indications et précautions
    ordonnance.append("CONTRE-INDICATIONS ET PRÉCAUTIONS :")
    ordonnance.append("")
    ordonnance.append(contraindications_text)
    ordonnance.append("")
    
    # Examens complémentaires si nécessaire
    examens_bio_ajoutes = False
    
    # Créatininémie si > 60 ans
    if f.get("age") and f["age"] > 60:
        ordonnance.append("")
        ordonnance.append("EXAMENS BIOLOGIQUES À PRÉVOIR :")
        ordonnance.append("")
        ordonnance.append("☐ Créatininémie + calcul de la clairance (DFG)")
        ordonnance.append("    (Avant injection de produit de contraste)")
        examens_bio_ajoutes = True
    
    # β-hCG UNIQUEMENT si femme < 50 ans ET grossesse NON confirmée
    if f.get("sexe") == "f" and (not f.get("age") or f["age"] < 50) and not f.get("grossesse"):
        if not examens_bio_ajoutes:
            ordonnance.append("")
            ordonnance.append("EXAMENS BIOLOGIQUES À PRÉVOIR :")
            ordonnance.append("")
        ordonnance.append("☐ β-hCG plasmatique (test de grossesse)")
        ordonnance.append("    (Avant tout examen irradiant)")
        examens_bio_ajoutes = True
    
    if examens_bio_ajoutes:
        ordonnance.append("")
    
    ordonnance.append("-" * 80)
    ordonnance.append("")
    
    # Pied de page
    ordonnance.append("Date et signature du praticien :")
    ordonnance.append("")
    ordonnance.append(f"Fait le {now.strftime('%d/%m/%Y')} à {now.strftime('%H:%M')}")
    ordonnance.append("")
    ordonnance.append("")
    ordonnance.append("Signature et cachet :")
    ordonnance.append("")
    ordonnance.append("")
    ordonnance.append("")
    ordonnance.append("=" * 80)
    ordonnance.append("")
    ordonnance.append("Cette ordonnance a été générée avec l'assistance d'un système d'aide à la décision")
    ordonnance.append("clinique. Elle doit être validée par le médecin prescripteur.")
    ordonnance.append("")
    
    return "\n".join(ordonnance)


def save_report(report_text, filename=None):
    """Enregistre le texte `report_text` dans un fichier .txt (UTF-8).
    Si `filename` est None ou vide, génère un nom basé sur la date/heure.
    Retourne le chemin du fichier créé.
    """
    import os
    # Obtenir le répertoire du script (source/) puis remonter au parent (v_arbre_d/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # v_arbre_d/
    reports_dir = os.path.join(project_root, "reports")
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


def save_ordonnance(ordonnance_text, filename=None):
    """Enregistre l'ordonnance dans un fichier .txt (UTF-8) dans le dossier ordonnances/.
    Si `filename` est None ou vide, génère un nom basé sur la date/heure.
    Retourne le chemin du fichier créé.
    """
    import os
    # Obtenir le répertoire du script (source/) puis remonter au parent (v_arbre_d/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # v_arbre_d/
    ordonnances_dir = os.path.join(project_root, "ordonnances")
    os.makedirs(ordonnances_dir, exist_ok=True)

    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ordonnance_{ts}.txt"

    # Si l'utilisateur a fourni un nom simple, l'enregistrer dans ordonnances/
    if not os.path.isabs(filename):
        filename = os.path.join(ordonnances_dir, filename)

    with open(filename, "w", encoding="utf-8") as fh:
        fh.write(ordonnance_text)

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
        
        # Cas spécial pour la grossesse : si détectée dans le texte mais sans durée précise
        if key == "grossesse" and f[key] and f.get("grossesse_sem") is None:
            # La grossesse a été détectée mais pas la durée, il faut la demander
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
            continue
        
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
    decision = decision_imagerie(f)
    print(decision)
    afficher_contraindications(f)

    # Récupérer le texte des contre-indications
    contraindications_text = get_contraindications_text(f)

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
    body.append(decision)

    body.append("")
    body.append("CONTRE-INDICATIONS / REMARQUES :")
    body.append(contraindications_text)

    report_text = "\n".join(hdr + ["\n"] + body)

    # Générer l'ordonnance médicale
    ordonnance_text = generer_ordonnance(f, texte, decision, contraindications_text)

    # Proposer l'enregistrement/impression
    print("\n")
    if demander_oui_non("Voulez-vous enregistrer le rapport récapitulatif"):
        fname = input("Nom du fichier (laisser vide pour générer automatiquement) : ").strip()
        saved_path = save_report(report_text, fname if fname else None)
        print(f"Rapport enregistré : {saved_path}")
    
    # Toujours générer l'ordonnance
    print("\n")
    if demander_oui_non("Voulez-vous générer l'ordonnance médicale"):
        fname_ordonnance = input("Nom de l'ordonnance (laisser vide pour générer automatiquement) : ").strip()
        saved_ordonnance = save_ordonnance(ordonnance_text, fname_ordonnance if fname_ordonnance else None)
        print(f"Ordonnance enregistrée : {saved_ordonnance}")
        print("\n⚠️  IMPORTANT : Cette ordonnance doit être revue et validée par le médecin prescripteur.")

if __name__ == "__main__":
    chatbot_cephalees()