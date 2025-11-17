# Tests de Performance - Chatbot Médical

Ce document explique comment utiliser les tests unitaires pour évaluer les performances du chatbot médical.

## Auteur
- **Noam** - Tests de performance et d'évaluation

## Vue d'ensemble

Le fichier `test_noam.py` contient une suite complète de tests pour évaluer :
- ⏱️ **Performance temporelle** (indexation, requêtes)
- 🎯 **Précision des réponses** (comparaison avec cas de référence)
- 📝 **Qualité du format** des réponses
- 🔄 **Robustesse** (gestion des cas limites)
- 💾 **Récupération ChromaDB** (qualité de la recherche vectorielle)
- 🚀 **Résistance** (test de stress avec multiples requêtes)

## Structure des Tests

### 1. `TestPerformanceChatbotMedical`
Tests principaux de performance :

- **`test_01_indexing_performance`** : Mesure le temps d'indexation ChromaDB
- **`test_02_query_response_time`** : Évalue les temps de réponse
- **`test_03_response_format_validation`** : Valide le format des réponses
- **`test_04_accuracy_on_test_cases`** : Compare avec les cas de validation
- **`test_05_edge_cases`** : Teste la gestion des cas limites
- **`test_06_chromadb_retrieval_quality`** : Évalue la qualité de récupération
- **`test_07_patient_cases_comprehensive`** : 🆕 Tests de cas patients réalistes avec suivi des problèmes
- **`test_08_stress_test`** : Test de résistance avec 50 requêtes

### 2. `TestIntegrationChatbot`
Tests d'intégration :

- **`test_integration_complete_workflow`** : Teste le workflow complet

## Exécution des Tests

### Option 1 : Exécution directe
```bash
# Depuis le dossier v_llm
python tests/test_noam.py
```

### Option 2 : Avec unittest
```bash
# Test spécifique
python -m unittest tests.test_noam.TestPerformanceChatbotMedical.test_01_indexing_performance -v

# Tous les tests
python -m unittest tests.test_noam -v
```

### Option 3 : Script d'exécution (recommandé)
```bash
# Depuis la racine du projet
python run_tests.py

# Mode verbeux
python run_tests.py --verbose

# Avec rapport
python run_tests.py --report
```

## Métriques de Performance

### Seuils d'Acceptation
- **Temps d'indexation** : < 30 secondes
- **Temps de réponse moyen** : < 5 secondes
- **Précision globale** : ≥ 60%
- **Score format** : ≥ 50%
- **Taux de succès stress test** : ≥ 95%

### Métriques Collectées
```
Temps d'indexation: X.XXs
Temps moyen de requête: X.XXs
Temps min/max de requête: X.XXs / X.XXs
Précision moyenne: X.XX
Score format moyen: X.XX
```

## Données de Test

### Fichiers Utilisés
- **`data/guidelines.json`** : Base de connaissances médicales
- **`data/clinical_cases_val.jsonl`** : Cas cliniques de validation

### Exemple de Cas de Test
```json
{
  "instruction": "Vous êtes un assistant médical expert...\n\nCas clinique:\nPatient 25 ans, céphalée brutale depuis 2 heures, avec fièvre",
  "response": "Recommandation: IRM cérébrale en urgence (<24h). Justification: présence de signes d'alerte (fièvre)."
}
```

## Mocking et Tests

Les tests utilisent des **mocks** pour éviter les appels réels au modèle Ollama :
- Temps de réponse rapides et reproductibles
- Pas besoin du modèle réel installé
- Tests isolés et déterministes

## Interprétation des Résultats

### ✅ Tests Réussis
- Tous les seuils de performance sont respectés
- Le système est stable et performant

### ⚠️ Tests en Échec
- **Temps trop long** : Optimisation nécessaire
- **Précision faible** : Améliorer le RAG ou les prompts
- **Format incorrect** : Revoir la génération de réponses

## Extensions Possibles

### Améliorations Futures
1. **Tests de charge** : Plus de requêtes simultanées
2. **Tests A/B** : Comparer différentes versions
3. **Métriques métier** : Satisfaction médicale, sécurité
4. **Tests d'intégration** : Avec base de données réelle
5. **Benchmarks** : Comparaison avec autres solutions

### Nouveau Tests Personnalisés
```python
def test_custom_scenario(self):
    \"\"\"Votre test personnalisé\"\"\"
    # Votre logique de test ici
    pass
```

## 🔍 Suivi des Cas Problématiques

### Nouveauté : Mémorisation des Échecs
Le système garde maintenant en mémoire les cas de patients qui posent problème :

#### 📝 Fichiers Générés
- **`v_llm/reports/problematic_cases.json`** : Cas problématiques détectés
- **`v_llm/reports/patient_test_results.json`** : Historique complet des tests

#### 🏥 Cas de Patients Testés
- **Neurologie** : Céphalées, traumatismes, méningites
- **Obstétrique** : Grossesse pathologique, pré-éclampsie  
- **Traumatologie** : Traumatismes crâniens, Glasgow
- **Médecine Générale** : Cas peu spécifiques

#### 📊 Types d'Erreurs Trackées
- **`format_error`** : Mauvais format de réponse
- **`keyword_mismatch`** : Mots-clés médicaux manquants
- **`execution_error`** : Erreurs techniques

#### 🎯 Métriques par Cas
```
✅ Cas 1: NEUROLOGIE - Score: 0.85 - RÉUSSI
❌ Cas 2: OBSTÉTRIQUE - Score: 0.45 - ÉCHOUÉ
   Format: ✗ | Mots-clés: 0.60 | Temps: 1.23s
```

#### 📈 Rapport Final Étendu
```
⚠️  CAS PROBLÉMATIQUES IDENTIFIÉS: 3
• format_error: 2 cas
• keyword_mismatch: 1 cas

📊 STATISTIQUES TESTS PATIENTS
• neurologie: 4/5 (80%)
• obstétrique: 1/3 (33%)
Sessions de test: 1
Taux de succès moyen: 68.5%
```

## Dépendances

### Packages Requis
- `chromadb` : Base vectorielle
- `unittest.mock` : Mocking (standard Python)
- `psutil` : Monitoring mémoire (optionnel)

### Installation
```bash
pip install chromadb psutil
```

## Troubleshooting

### Problèmes Fréquents

1. **Import Error** : Vérifier le PYTHONPATH
```bash
cd v_llm/src
python -c "import indexage; print('OK')"
```

2. **Fichier manquant** : Vérifier les chemins
```bash
ls data/guidelines.json
ls data/clinical_cases_val.jsonl
```

3. **Lenteur** : Réduire le nombre de cas de test
```python
sample_size = min(5, len(self.test_cases))  # Au lieu de 10
```

## Contribution

Pour ajouter de nouveaux tests :
1. Hériter de `TestPerformanceChatbotMedical`
2. Nommer la méthode `test_XX_nom_descriptif`
3. Ajouter des assertions appropriées
4. Documenter les seuils d'acceptation

---

*Dernière mise à jour : 15 novembre 2025*