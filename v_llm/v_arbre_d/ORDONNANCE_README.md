# Génération d'Ordonnances Médicales

## Description

Le système génère automatiquement une ordonnance médicale au format français à la fin de chaque consultation. Cette ordonnance contient :

1. **En-tête** : Informations du praticien et date
2. **Informations patient** : Identité, âge, sexe, numéro de sécurité sociale
3. **Motif de consultation** : Texte libre du médecin
4. **Éléments cliniques** : Tous les signes et symptômes détectés
5. **Raisonnement clinique** : Arbre décisionnel complet expliquant le choix de l'examen
6. **Prescription** : L'examen d'imagerie recommandé
7. **Contre-indications et précautions** : Tous les points d'attention
8. **Examens complémentaires** : Biologie à prévoir si nécessaire
9. **Signature** : Zone pour validation et cachet médical

## Format de l'Ordonnance

L'ordonnance suit le format standard français avec :
- Un en-tête professionnel
- Des sections clairement délimitées
- Un raisonnement clinique transparent
- Toutes les informations nécessaires à la validation médicale
- Un pied de page avec rappel de validation nécessaire

## Utilisation

À la fin de l'exécution du programme, deux options vous sont proposées :

1. **Rapport récapitulatif** : Version condensée pour archivage interne
2. **Ordonnance médicale** : Document formaté prêt pour validation et remise au patient

Les fichiers sont enregistrés dans le dossier `reports/` avec horodatage automatique.

## Exemple de Contenu

```
================================================================================
                            ORDONNANCE MÉDICALE
================================================================================

Dr. [NOM DU MÉDECIN]
[Spécialité]
[Adresse du cabinet]
...

PATIENT(E) :

Nom : [À COMPLÉTER]
Prénom : [À COMPLÉTER]
Âge : 45 ans
Sexe : Féminin
...

MOTIF DE CONSULTATION :

Patiente de 45 ans présentant une céphalée brutale, type coup de tonnerre...

ÉLÉMENTS CLINIQUES RECUEILLIS :

• Installation brutale (céphalée en coup de tonnerre)
• Pas d'antécédent particulier

RAISONNEMENT CLINIQUE ET ARBRE DÉCISIONNEL :

Analyse de la situation :
• Présence de critères d'urgence :
  - Installation brutale → risque d'hémorragie méningée
  → Indication à une imagerie en urgence

Choix de l'examen d'imagerie :
La personne présente une céphalée brutale évoquant une situation d'urgence...

PRESCRIPTION :

☐ SCANNER CÉRÉBRAL SANS INJECTION
    En urgence
    Indication : Céphalée aiguë avec critères de gravité
...
```

## Important

⚠️ **Cette ordonnance est générée par un système d'aide à la décision et DOIT être validée par le médecin prescripteur avant remise au patient.**

Le système trace le raisonnement clinique pour :
- Faciliter la validation médicale
- Assurer la traçabilité des décisions
- Permettre la relecture et l'audit
- Former les internes et étudiants

## Personnalisation

Pour personnaliser l'en-tête de l'ordonnance avec vos informations :
1. Ouvrez `source/main.py`
2. Modifiez la fonction `generer_ordonnance()`
3. Remplacez les champs `[NOM DU MÉDECIN]`, `[Spécialité]`, etc.

Ou créez un fichier de configuration séparé pour vos informations professionnelles.
