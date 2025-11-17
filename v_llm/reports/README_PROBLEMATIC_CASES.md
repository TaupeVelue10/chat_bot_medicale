# Suivi des Cas Problématiques - Chatbot Médical

Ce dossier contient les données de suivi des performances et des cas problématiques du chatbot médical.

## Fichiers Générés

### 📝 `problematic_cases.json`
Contient tous les cas de patients qui ont posé problème lors des tests :
- **Description du cas** : Présentation clinique du patient
- **Réponse attendue** : Ce que le système devrait répondre
- **Réponse obtenue** : Ce que le système a réellement répondu
- **Type d'erreur** : Classification de l'erreur (format, mots-clés, exécution)
- **Score de précision** : Score numérique (0.0 à 1.0)
- **Timestamp** : Date et heure de détection

### 📊 `patient_test_results.json`
Historique complet des sessions de tests :
- **Résultats par session** : Détails de chaque test executé
- **Statistiques globales** : Taux de succès, tendances
- **Statistiques par catégorie** : Performance par spécialité médicale

## Structure des Données

### Cas Problématique
```json
{
  "timestamp": "2025-11-15T14:30:00",
  "case_description": "Patient 35 ans, céphalée brutale, fièvre 39°C",
  "expected_response": "Format: Recommandation:, Mots-clés: ['méningite', 'urgence']",
  "actual_response": "Pour préciser: Depuis quand ?",
  "error_type": "format_error",
  "accuracy_score": 0.25,
  "test_run_id": "20251115_143000"
}
```

### Types d'Erreurs
- **`format_error`** : Mauvais format de réponse (Recommandation: vs Pour préciser:)
- **`keyword_mismatch`** : Mots-clés médicaux manquants ou incorrects
- **`execution_error`** : Erreur technique pendant l'analyse

## Catégories de Patients Testées

### 🧠 **Neurologie**
- Céphalées, traumatismes crâniens
- AVC, méningites
- Troubles de la conscience

### 🤱 **Obstétrique** 
- Grossesse pathologique
- Pré-éclampsie, HTA gravidique
- Imagerie pendant la grossesse

### 🚑 **Traumatologie**
- Traumatismes crâniens
- Échelle de Glasgow
- Indications chirurgicales

### 🏥 **Médecine Générale**
- Cas peu spécifiques
- Demandes de précisions
- Anamnèse incomplète

## Utilisation pour l'Amélioration

### 1. Identifier les Patterns
```bash
# Examiner les types d'erreurs fréquents
grep -o '"error_type": "[^"]*"' problematic_cases.json | sort | uniq -c
```

### 2. Analyser les Catégories Faibles
- Consulter les statistiques par catégorie
- Identifier les spécialités problématiques
- Adapter les prompts ou la base de connaissances

### 3. Réentraînement Ciblé
- Utiliser les cas problématiques comme données d'entraînement
- Améliorer les guidelines médicales
- Affiner les règles de formatage

### 4. Tests de Régression
- Relancer les tests sur les anciens cas problématiques
- Vérifier que les corrections n'introduisent pas de nouveaux problèmes
- Suivre l'évolution du taux de succès global

## Métriques de Suivi

### Seuils d'Alerte
- **Taux de succès < 60%** : Investigation nécessaire
- **> 10 cas problématiques/session** : Problème systémique
- **Même type d'erreur répété** : Bug à corriger

### Tendances à Surveiller
- Évolution du taux de succès dans le temps
- Distribution des erreurs par catégorie
- Temps de réponse sur les cas difficiles

## Intégration Continue

Les fichiers de ce dossier sont automatiquement mis à jour à chaque exécution des tests. Ils peuvent être utilisés pour :

1. **Monitoring automatique** : Alertes si dégradation
2. **Rapports qualité** : Tableaux de bord des performances  
3. **Amélioration continue** : Identification des axes de progression
4. **Tests de non-régression** : Validation des nouvelles versions

---

*Fichiers générés automatiquement par `test_noam.py`*
*Dernière mise à jour : 15 novembre 2025*