Assistant médical — céphalées

Petit outil CLI pour aider à la prescription d'examens d'imagerie devant une céphalée.

Fonctionnalités
- Analyse simple du texte libre fourni par le clinicien (âge, sexe, grossesse, signes évocateurs).
- Questionnaire interactif pour compléter les informations manquantes (lecture d'une touche sans entrée).
- Recommandation d'imagerie (scanner/IRM) et rappel des contre-indications.
- Export du compte-rendu au format texte (dossier `reports/`) avec en-tête et horodatage.

Installation
1. Créer et activer un environnement Python (recommandé) :

   python3 -m venv .venv
   source .venv/bin/activate

2. Installer les dépendances :

   python -m pip install -r requirements.txt

Utilisation
- Lancer le script principal :

   python main.py

- Suivre les questions interactives. En fin de session, il est proposé d'enregistrer le rapport dans `reports/`.

Remarques
- Ce script est fourni à titre indicatif. Il ne remplace pas la décision clinique ni l'avis spécialisé.
- Adapter et vérifier la compatibilité avec votre environnement Python et vos conventions de déploiement.
