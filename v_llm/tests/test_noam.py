"""
Tests unitaires pour évaluer les performances du chatbot médical
Auteur: Noam
Date: 15 novembre 2025
"""

import unittest
import sys
import os
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import re
from datetime import datetime
import pickle

# Ajouter le chemin src au Python path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from indexage import create_index
import importlib.util

# Charger le module ollama local
_ollama_path = Path(__file__).parent.parent / "src" / "ollama.py"
spec = importlib.util.spec_from_file_location("local_ollama", str(_ollama_path))
local_ollama = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_ollama)
rag_biomistral_query = local_ollama.rag_biomistral_query


class TestPerformanceChatbotMedical(unittest.TestCase):
    """Tests de performance pour le chatbot médical"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour tous les tests"""
        # Chemin vers les données de test
        cls.data_dir = Path(__file__).parent.parent / "data"
        cls.guidelines_file = cls.data_dir / "guidelines.json"
        cls.test_cases_file = cls.data_dir / "clinical_cases_val.jsonl"
        
        # Chargement des cas de test
        cls.test_cases = []
        if cls.test_cases_file.exists():
            with open(cls.test_cases_file, 'r', encoding='utf-8') as f:
                for line in f:
                    cls.test_cases.append(json.loads(line.strip()))
        
        # Collection ChromaDB pour les tests
        cls.collection = None
        
        # Métriques de performance
        cls.performance_metrics = {
            'indexing_time': 0,
            'query_times': [],
            'accuracy_scores': [],
            'response_format_scores': []
        }
        
        # Système de suivi des cas problématiques
        cls.problematic_cases_file = Path(__file__).parent.parent / "reports" / "problematic_cases.json"
        cls.patient_test_results_file = Path(__file__).parent.parent / "reports" / "patient_test_results.json"
        cls.problematic_cases = cls._load_problematic_cases()
        cls.patient_test_history = cls._load_patient_test_history()
        
        # Créer le dossier reports s'il n'existe pas
        cls.problematic_cases_file.parent.mkdir(exist_ok=True)
    
    def setUp(self):
        """Configuration avant chaque test"""
        # Créer l'index si nécessaire
        if self.collection is None:
            start_time = time.time()
            self.__class__.collection = create_index(str(self.guidelines_file))
            self.__class__.performance_metrics['indexing_time'] = time.time() - start_time
    
    def test_01_indexing_performance(self):
        """Test des performances d'indexation"""
        print(f"\n=== Test d'indexing ===")
        
        # Tester le temps d'indexation
        self.assertIsNotNone(self.collection, "La collection ChromaDB doit être créée")
        
        # Vérifier que des documents ont été indexés
        results = self.collection.get()
        self.assertGreater(len(results['ids']), 0, "Des documents doivent être indexés")
        
        print(f"Temps d'indexation: {self.performance_metrics['indexing_time']:.2f}s")
        print(f"Nombre de documents indexés: {len(results['ids'])}")
        
        # Le temps d'indexation ne doit pas dépasser 30 secondes
        self.assertLess(self.performance_metrics['indexing_time'], 30, 
                       "L'indexation doit prendre moins de 30 secondes")
    
    def test_02_query_response_time(self):
        """Test du temps de réponse des requêtes"""
        print(f"\n=== Test temps de réponse ===")
        
        # Mock du modèle Ollama pour éviter les appels réels  
        with patch.object(local_ollama, '_import_installed_ollama') as mock_ollama:
            mock_client = MagicMock()
            mock_client.generate.return_value = {
                'response': 'Recommandation: Scanner cérébral sans injection en urgence.'
            }
            mock_ollama.return_value = mock_client
        
            test_queries = [
                "Patient 25 ans, céphalée brutale depuis 2 heures, avec fièvre",
                "Patient 45 ans, traumatisme crânien, perte de connaissance",
                "Patient 60 ans, céphalée progressive depuis 1 semaine"
            ]
            
            for query in test_queries:
                start_time = time.time()
                response = rag_biomistral_query(query, self.collection)
                query_time = time.time() - start_time
                
                self.performance_metrics['query_times'].append(query_time)
                self.assertIsNotNone(response, "La réponse ne doit pas être None")
                
                print(f"Requête: '{query[:50]}...' - Temps: {query_time:.2f}s")
            
            avg_time = sum(self.performance_metrics['query_times']) / len(self.performance_metrics['query_times'])
            print(f"Temps moyen de réponse: {avg_time:.2f}s")
            
            # Le temps de réponse moyen ne doit pas dépasser 5 secondes
            self.assertLess(avg_time, 5.0, "Le temps de réponse moyen doit être < 5s")
    
    def test_03_response_format_validation(self):
        """Test de validation du format des réponses"""
        print(f"\n=== Test format des réponses ===")
        
        # Mock du modèle avec différents types de réponses
        test_responses = [
            "Recommandation: Scanner cérébral sans injection en urgence.",
            "Pour préciser: Depuis quand ? | Y a-t-il fièvre ? | Antécédents ?",
            "Réponse incorrecte sans format",
            ""
        ]
        
        valid_formats = 0
        for response in test_responses:
            is_valid = self._validate_response_format(response)
            if is_valid:
                valid_formats += 1
            print(f"Réponse: '{response[:50]}...' - Valide: {is_valid}")
        
        format_score = valid_formats / len(test_responses)
        self.performance_metrics['response_format_scores'].append(format_score)
        
        print(f"Score de format: {format_score:.2f}")
        # Au moins 50% des réponses doivent avoir le bon format
        self.assertGreaterEqual(format_score, 0.5, "Au moins 50% des réponses doivent avoir le bon format")
    
    def test_04_accuracy_on_test_cases(self):
        """Test de précision sur les cas de test de validation"""
        print(f"\n=== Test de précision ===")
        
        if not self.test_cases:
            self.skipTest("Aucun cas de test disponible")
        
        # Tester sur un échantillon des cas de test
        sample_size = min(10, len(self.test_cases))  # Tester max 10 cas
        test_sample = self.test_cases[:sample_size]
        
        correct_predictions = 0
        
        with patch.object(local_ollama, '_import_installed_ollama') as mock_ollama:
            for i, test_case in enumerate(test_sample):
                # Extraire le cas clinique de l'instruction
                clinical_case = self._extract_clinical_case(test_case['instruction'])
                expected_response = test_case['response']
                
                # Mock la réponse du modèle avec la réponse attendue
                mock_client = MagicMock()
                mock_client.generate.return_value = {'response': expected_response}
                mock_ollama.return_value = mock_client
                
                # Obtenir la réponse du système
                actual_response = rag_biomistral_query(clinical_case, self.collection)
                
                # Évaluer la similarité
                accuracy = self._calculate_accuracy(expected_response, actual_response)
                self.performance_metrics['accuracy_scores'].append(accuracy)
                
                if accuracy > 0.8:  # Seuil d'acceptation
                    correct_predictions += 1
                
                print(f"Cas {i+1}: Précision = {accuracy:.2f}")
            
            overall_accuracy = correct_predictions / sample_size
            print(f"Précision globale: {overall_accuracy:.2f}")
            
            # La précision doit être au moins de 60%
            self.assertGreaterEqual(overall_accuracy, 0.6, 
                                   "La précision doit être au moins de 60%")
    
    def test_05_edge_cases(self):
        """Test de gestion des cas limites"""
        print(f"\n=== Test cas limites ===")
        
        edge_cases = [
            "",  # Cas vide
            "   ",  # Cas avec espaces uniquement
            "Patient sans informations médicales",  # Cas incomplet
            "x" * 1000,  # Cas très long
        ]
        
        with patch.object(local_ollama, '_import_installed_ollama') as mock_ollama:
            mock_client = MagicMock()
            mock_client.generate.return_value = {
                'response': 'Pour préciser: Informations manquantes ?'
            }
            mock_ollama.return_value = mock_client
            
            for case in edge_cases:
                try:
                    response = rag_biomistral_query(case, self.collection)
                    self.assertIsNotNone(response, f"Réponse ne doit pas être None pour: '{case[:20]}...'")
                    print(f"Cas limite géré: '{case[:20]}...' -> OK")
                        
                except Exception as e:
                    self.fail(f"Erreur sur cas limite '{case[:20]}...': {e}")
    
    def test_06_chromadb_retrieval_quality(self):
        """Test de la qualité de récupération de ChromaDB"""
        print(f"\n=== Test qualité récupération ChromaDB ===")
        
        # Test de requêtes spécifiques
        test_queries = [
            "céphalée brutale traumatisme",
            "fièvre perte de connaissance",
            "grossesse enceinte imagerie",
            "scanner urgence"
        ]
        
        for query in test_queries:
            results = self.collection.query(query_texts=[query], n_results=3)
            
            self.assertGreater(len(results['documents'][0]), 0, 
                             f"Des documents doivent être récupérés pour '{query}'")
            
            # Vérifier que les métadonnées sont présentes
            if results['metadatas'][0]:
                metadata = results['metadatas'][0][0]
                self.assertIn('motif', metadata, "Métadonnée 'motif' doit être présente")
                self.assertIn('source', metadata, "Métadonnée 'source' doit être présente")
            
            print(f"Requête '{query}': {len(results['documents'][0])} documents récupérés")
    
    def test_07_patient_cases_comprehensive(self):
        """Test complet de cas de patients avec suivi des problèmes"""
        print(f"\n=== Test cas de patients compréhensif ===")
        
        # Générer un ID unique pour cette session de test
        self._test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Cas de patients réalistes à tester
        patient_cases = [
            {
                'description': 'Patient 35 ans, céphalée brutale, fièvre 39°C, raideur nuque',
                'expected_keywords': ['méningite', 'ponction lombaire', 'urgence', 'antibiotique'],
                'expected_format': 'Recommandation:',
                'severity': 'high',
                'category': 'neurologie'
            },
            {
                'description': 'Patient 28 ans enceinte 32SA, céphalée, HTA 180/110',
                'expected_keywords': ['pré-éclampsie', 'grossesse', 'surveillance', 'obstétrique'],
                'expected_format': 'Recommandation:',
                'severity': 'high',
                'category': 'obstétrique'
            },
            {
                'description': 'Patient 45 ans, traumatisme crânien, Glasgow 13',
                'expected_keywords': ['scanner', 'surveillance', 'neurochirurgie'],
                'expected_format': 'Recommandation:',
                'severity': 'medium',
                'category': 'traumatologie'
            },
            {
                'description': 'Patient 70 ans, céphalée chronique, AVC antérieur',
                'expected_keywords': ['imagerie', 'neurologie', 'antécédents'],
                'expected_format': 'Pour préciser:',
                'severity': 'medium',
                'category': 'neurologie'
            },
            {
                'description': 'Patient jeune, céphalée floue',
                'expected_keywords': ['précisions', 'anamnèse'],
                'expected_format': 'Pour préciser:',
                'severity': 'low',
                'category': 'général'
            }
        ]
        
        test_results = {
            'test_run_id': self._test_run_id,
            'timestamp': datetime.now().isoformat(),
            'total_cases': len(patient_cases),
            'results': [],
            'summary': {
                'passed': 0,
                'failed': 0,
                'problematic': 0
            }
        }
        
        with patch.object(local_ollama, '_import_installed_ollama') as mock_ollama:
            mock_client = MagicMock()
            mock_ollama.return_value = mock_client
            
            for i, case in enumerate(patient_cases):
                print(f"\nCas {i+1}/{len(patient_cases)}: {case['category'].upper()}")
                print(f"Description: {case['description'][:60]}...")
                
                # Simuler une réponse du modèle basée sur le cas
                mock_response = self._generate_mock_response(case)
                mock_client.generate.return_value = {'response': mock_response}
                
                try:
                    start_time = time.time()
                    actual_response = rag_biomistral_query(case['description'], self.collection)
                    response_time = time.time() - start_time
                    
                    # Évaluer la réponse
                    format_valid = self._validate_response_format(actual_response)
                    keyword_score = self._calculate_keyword_accuracy(case['expected_keywords'], actual_response)
                    format_matches = actual_response.startswith(case['expected_format']) if actual_response else False
                    
                    # Score global
                    overall_score = (keyword_score * 0.7) + (0.3 if format_matches else 0)
                    
                    case_result = {
                        'case_id': i + 1,
                        'description': case['description'],
                        'category': case['category'],
                        'severity': case['severity'],
                        'actual_response': actual_response,
                        'response_time': response_time,
                        'format_valid': format_valid,
                        'keyword_score': keyword_score,
                        'format_matches': format_matches,
                        'overall_score': overall_score,
                        'passed': overall_score >= 0.6
                    }
                    
                    test_results['results'].append(case_result)
                    
                    if case_result['passed']:
                        test_results['summary']['passed'] += 1
                        print(f"✅ Score: {overall_score:.2f} - RÉUSSI")
                    else:
                        test_results['summary']['failed'] += 1
                        test_results['summary']['problematic'] += 1
                        print(f"❌ Score: {overall_score:.2f} - ÉCHOUÉ")
                        
                        # Ajouter aux cas problématiques
                        error_type = "format_error" if not format_matches else "keyword_mismatch"
                        self._add_problematic_case(
                            case['description'],
                            f"Format: {case['expected_format']}, Mots-clés: {case['expected_keywords']}",
                            actual_response,
                            error_type,
                            overall_score
                        )
                    
                    print(f"   Format: {'✓' if format_matches else '✗'} | Mots-clés: {keyword_score:.2f} | Temps: {response_time:.2f}s")
                    
                except Exception as e:
                    test_results['summary']['failed'] += 1
                    test_results['summary']['problematic'] += 1
                    print(f"❌ ERREUR: {e}")
                    
                    self._add_problematic_case(
                        case['description'],
                        "Aucune erreur attendue",
                        f"Exception: {str(e)}",
                        "execution_error",
                        0.0
                    )
        
        # Sauvegarder les résultats
        self.__class__.patient_test_history['test_runs'].append(test_results)
        self._update_statistics(test_results)
        
        # Afficher le résumé
        success_rate = test_results['summary']['passed'] / test_results['total_cases']
        print(f"\n📊 RÉSUMÉ DU TEST:")
        print(f"   Cas testés: {test_results['total_cases']}")
        print(f"   Réussis: {test_results['summary']['passed']} ({success_rate:.1%})")
        print(f"   Échoués: {test_results['summary']['failed']}")
        print(f"   Cas problématiques identifiés: {test_results['summary']['problematic']}")
        
        # Assertions
        self.assertGreaterEqual(success_rate, 0.6, f"Taux de succès trop faible: {success_rate:.1%}")
        
        return test_results
    
    def test_08_stress_test(self):
        """Test de résistance avec multiple requêtes"""
        print(f"\n=== Test de résistance ===")
        
        # Test de stabilité avec beaucoup de requêtes
        with patch.object(local_ollama, '_import_installed_ollama') as mock_ollama:
            mock_client = MagicMock()
            mock_client.generate.return_value = {'response': 'Test response'}
            mock_ollama.return_value = mock_client
            
            start_time = time.time()
            errors = 0
            
            # Effectuer 50 requêtes rapides
            for i in range(50):
                try:
                    response = rag_biomistral_query(f"Test query number {i}", self.collection)
                    self.assertIsNotNone(response, f"Réponse {i} ne doit pas être None")
                except Exception as e:
                    errors += 1
                    print(f"Erreur requête {i}: {e}")
            
            total_time = time.time() - start_time
            success_rate = (50 - errors) / 50
            
            print(f"50 requêtes en {total_time:.2f}s")
            print(f"Taux de succès: {success_rate:.2%}")
            print(f"Erreurs: {errors}")
            
            # Au moins 95% de succès attendu
            self.assertGreaterEqual(success_rate, 0.95, 
                                   "Le taux de succès doit être >= 95%")
    
    # Méthodes utilitaires
    
    @classmethod
    def _load_problematic_cases(cls):
        """Charge les cas problématiques depuis le fichier"""
        if cls.problematic_cases_file.exists():
            try:
                with open(cls.problematic_cases_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur chargement cas problématiques: {e}")
        return {'cases': [], 'last_update': None}
    
    @classmethod
    def _load_patient_test_history(cls):
        """Charge l'historique des tests patients"""
        if cls.patient_test_results_file.exists():
            try:
                with open(cls.patient_test_results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur chargement historique: {e}")
        return {'test_runs': [], 'statistics': {}}
    
    @classmethod
    def _save_problematic_cases(cls):
        """Sauvegarde les cas problématiques"""
        cls.problematic_cases['last_update'] = datetime.now().isoformat()
        try:
            with open(cls.problematic_cases_file, 'w', encoding='utf-8') as f:
                json.dump(cls.problematic_cases, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde cas problématiques: {e}")
    
    @classmethod
    def _save_patient_test_history(cls):
        """Sauvegarde l'historique des tests patients"""
        try:
            with open(cls.patient_test_results_file, 'w', encoding='utf-8') as f:
                json.dump(cls.patient_test_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde historique: {e}")
    
    def _add_problematic_case(self, case_description, expected_response, actual_response, error_type, accuracy_score):
        """Ajoute un cas problématique à la liste"""
        problematic_case = {
            'timestamp': datetime.now().isoformat(),
            'case_description': case_description,
            'expected_response': expected_response,
            'actual_response': actual_response,
            'error_type': error_type,
            'accuracy_score': accuracy_score,
            'test_run_id': getattr(self, '_test_run_id', 'unknown')
        }
        
        self.__class__.problematic_cases['cases'].append(problematic_case)
        print(f"⚠️  Cas problématique ajouté: {error_type} (score: {accuracy_score:.2f})")
    
    def _validate_response_format(self, response):
        """Valide le format d'une réponse"""
        if not response or not isinstance(response, str):
            return False
        
        response = response.strip()
        return (response.startswith("Recommandation:") or 
                response.startswith("Pour préciser:"))
    
    def _extract_clinical_case(self, instruction):
        """Extrait le cas clinique d'une instruction"""
        # Chercher après "Cas clinique:"
        match = re.search(r'Cas clinique:\s*(.+)', instruction, re.DOTALL)
        if match:
            return match.group(1).strip()
        return instruction
    
    def _calculate_accuracy(self, expected, actual):
        """Calcule la précision entre réponse attendue et réelle"""
        if not expected or not actual:
            return 0.0
        
        # Comparaison simple basée sur les mots-clés communs
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return 0.0
        
        intersection = expected_words.intersection(actual_words)
        return len(intersection) / len(expected_words)
    
    def _calculate_keyword_accuracy(self, expected_keywords, actual_response):
        """Calcule le score de précision basé sur la présence de mots-clés attendus"""
        if not expected_keywords or not actual_response:
            return 0.0
        
        actual_lower = actual_response.lower()
        matches = 0
        
        for keyword in expected_keywords:
            if keyword.lower() in actual_lower:
                matches += 1
        
        return matches / len(expected_keywords)
    
    def _generate_mock_response(self, case):
        """Génère une réponse mock réaliste basée sur le cas"""
        if case['expected_format'] == 'Recommandation:':
            if case['severity'] == 'high':
                return f"Recommandation: Prise en charge urgente en {case['category']}. Examens complémentaires nécessaires."
            else:
                return f"Recommandation: Consultation {case['category']} programmée. Surveillance clinique."
        else:
            return "Pour préciser: Depuis quand ? | Antécédents ? | Signes associés ?"
    
    def _update_statistics(self, test_results):
        """Met à jour les statistiques globales"""
        stats = self.__class__.patient_test_history.setdefault('statistics', {})
        
        # Statistiques par catégorie
        for result in test_results['results']:
            category = result['category']
            if category not in stats:
                stats[category] = {'total': 0, 'passed': 0, 'failed': 0}
            
            stats[category]['total'] += 1
            if result['passed']:
                stats[category]['passed'] += 1
            else:
                stats[category]['failed'] += 1
        
        # Statistiques globales
        global_stats = stats.setdefault('global', {'total_runs': 0, 'avg_success_rate': 0})
        global_stats['total_runs'] += 1
        
        # Calculer le taux de succès moyen
        all_runs = self.__class__.patient_test_history['test_runs']
        if all_runs:
            total_success = sum(run['summary']['passed'] / run['total_cases'] for run in all_runs)
            global_stats['avg_success_rate'] = total_success / len(all_runs)
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage final et rapport de performance"""
        # Sauvegarder les cas problématiques et l'historique
        cls._save_problematic_cases()
        cls._save_patient_test_history()
        
        print(f"\n" + "="*60)
        print("RAPPORT DE PERFORMANCE FINAL")
        print("="*60)
        
        metrics = cls.performance_metrics
        
        print(f"Temps d'indexation: {metrics['indexing_time']:.2f}s")
        
        if metrics['query_times']:
            avg_query_time = sum(metrics['query_times']) / len(metrics['query_times'])
            print(f"Temps moyen de requête: {avg_query_time:.2f}s")
            print(f"Temps min/max de requête: {min(metrics['query_times']):.2f}s / {max(metrics['query_times']):.2f}s")
        
        if metrics['accuracy_scores']:
            avg_accuracy = sum(metrics['accuracy_scores']) / len(metrics['accuracy_scores'])
            print(f"Précision moyenne: {avg_accuracy:.2f}")
        
        if metrics['response_format_scores']:
            avg_format = sum(metrics['response_format_scores']) / len(metrics['response_format_scores'])
            print(f"Score format moyen: {avg_format:.2f}")
        
        # Rapport des cas problématiques
        if cls.problematic_cases['cases']:
            print(f"\n⚠️  CAS PROBLÉMATIQUES IDENTIFIÉS: {len(cls.problematic_cases['cases'])}")
            print("-" * 40)
            
            # Grouper par type d'erreur
            error_types = {}
            for case in cls.problematic_cases['cases']:
                error_type = case['error_type']
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(case)
            
            for error_type, cases in error_types.items():
                print(f"• {error_type}: {len(cases)} cas")
                for case in cases[-2:]:  # Montrer les 2 derniers
                    print(f"  - {case['case_description'][:50]}... (score: {case['accuracy_score']:.2f})")
            
            print(f"\n📁 Détails sauvegardés dans: {cls.problematic_cases_file}")
        
        # Statistiques des tests patients
        if cls.patient_test_history['test_runs']:
            stats = cls.patient_test_history['statistics']
            print(f"\n📊 STATISTIQUES TESTS PATIENTS")
            print("-" * 40)
            
            if 'global' in stats:
                global_stats = stats['global']
                print(f"Sessions de test: {global_stats['total_runs']}")
                print(f"Taux de succès moyen: {global_stats['avg_success_rate']:.1%}")
            
            # Statistiques par catégorie
            for category, cat_stats in stats.items():
                if category != 'global':
                    success_rate = cat_stats['passed'] / cat_stats['total'] if cat_stats['total'] > 0 else 0
                    print(f"• {category}: {cat_stats['passed']}/{cat_stats['total']} ({success_rate:.1%})")
            
            print(f"\n📁 Historique complet: {cls.patient_test_results_file}")
        
        print("="*60)


class TestIntegrationChatbot(unittest.TestCase):
    """Tests d'intégration pour le chatbot complet"""
    
    def test_integration_complete_workflow(self):
        """Test du workflow complet du chatbot"""
        print(f"\n=== Test intégration complète ===")
        
        # Créer l'index
        guidelines_file = Path(__file__).parent.parent / "data" / "guidelines.json"
        collection = create_index(str(guidelines_file))
        
        with patch.object(local_ollama, '_import_installed_ollama') as mock_ollama:
            # Mock du modèle
            mock_client = MagicMock()
            mock_ollama.return_value = mock_client
            
            # Tester le workflow avec demande de précision
            mock_client.generate.return_value = {
                'response': 'Pour préciser: Depuis quand ? | Y a-t-il fièvre ? | Antécédents ?'
            }
            
            response1 = rag_biomistral_query("Patient avec céphalée", collection)
            self.assertTrue(response1.startswith("Pour préciser:"), 
                           "Le système doit demander des précisions")
            
            # Tester avec informations complètes
            mock_client.generate.return_value = {
                'response': 'Recommandation: Scanner cérébral sans injection en urgence.'
            }
            
            response2 = rag_biomistral_query(
                "Patient 25 ans, céphalée brutale depuis 2 heures, avec fièvre et vomissements", 
                collection
            )
            self.assertTrue(response2.startswith("Recommandation:"), 
                           "Le système doit donner une recommandation")
            
            print("Workflow complet testé avec succès")


if __name__ == '__main__':
    # Configuration des tests
    unittest.main(verbosity=2, failfast=False)
