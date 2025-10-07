#!/usr/bin/env python3
"""
Suite de tests complète pour le système RAG de recommandations d'imagerie médicale
Tests automatisés avec validation de précision clinique
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama import generate_imaging_recommendation_rag, get_collection
import json
from colorama import init, Fore, Style, Back
init(autoreset=True)

class ImagingRAGTester:
    def __init__(self):
        """Initialise le testeur avec la base de données des guidelines"""
        print(f"{Fore.CYAN}🔧 Initialisation du système de test RAG...{Style.RESET_ALL}")
        self.collection = get_collection()
        self.test_cases = self._load_test_cases()
        self.results = []
        
    def _load_test_cases(self):
        """Charge les cas de test étendus"""
        return [
            # === URGENCES NEUROLOGIQUES ===
            {
                "id": "neuro_001",
                "category": "Urgence neurologique",
                "query": "Enfant 8 ans, vomissements matinaux répétés depuis 1 semaine avec céphalées et troubles visuels",
                "expected": "URGENTE",
                "pathology": "HTIC pédiatrique",
                "expected_imaging": "Scanner cérébral"
            },
            {
                "id": "neuro_002", 
                "category": "Urgence neurologique",
                "query": "Patient 34 ans, céphalées fébriles brutales avec photophobie et raideur de nuque",
                "expected": "URGENTE",
                "pathology": "Méningite/Hémorragie méningée",
                "expected_imaging": "Scanner + Ponction lombaire"
            },
            {
                "id": "neuro_003",
                "category": "Urgence neurologique", 
                "query": "Homme 45 ans, traumatisme crânien avec perte de connaissance 10 minutes et vomissements",
                "expected": "URGENTE",
                "pathology": "Traumatisme crânien grave",
                "expected_imaging": "Scanner cérébral"
            },
            
            # === IMAGERIE INDIQUÉE ===
            {
                "id": "abdo_001",
                "category": "Abdomen aigu",
                "query": "Femme 28 ans, douleur fosse iliaque droite depuis 12h avec fièvre 38.5°C et nausées",
                "expected": "INDIQUÉE", 
                "pathology": "Appendicite",
                "expected_imaging": "Scanner abdominal"
            },
            {
                "id": "uro_001",
                "category": "Urologie",
                "query": "Homme 45 ans, douleur lombaire brutale irradiant vers l'aine avec hématurie microscopique",
                "expected": "INDIQUÉE",
                "pathology": "Colique néphrétique", 
                "expected_imaging": "Scanner sans injection"
            },
            {
                "id": "neuro_004",
                "category": "Neurologie",
                "query": "Femme 30 ans, troubles de la marche progressifs avec paresthésies des membres et fatigue",
                "expected": "INDIQUÉE",
                "pathology": "Sclérose en plaques",
                "expected_imaging": "IRM cérébrale et médullaire"
            },
            {
                "id": "abdo_002",
                "category": "Abdomen",
                "query": "Femme enceinte 28 SA, douleurs abdominales avec fièvre et leucocytose",
                "expected": "INDIQUÉE",
                "pathology": "Appendicite grossesse",
                "expected_imaging": "Échographie puis IRM"
            },
            
            # === AUCUNE IMAGERIE ===
            {
                "id": "ortho_001", 
                "category": "Orthopédie",
                "query": "Homme 35 ans, lombalgie commune depuis 4 semaines sans amélioration, bon état général, pas de déficit",
                "expected": "AUCUNE",
                "pathology": "Lombalgie mécanique",
                "expected_imaging": "Pas d'imagerie avant 6 semaines"
            },
            {
                "id": "neuro_005",
                "category": "Neurologie",
                "query": "Femme 25 ans, céphalées récurrentes migraineuses, pas de fièvre, examen neurologique normal",
                "expected": "AUCUNE", 
                "pathology": "Céphalée primaire",
                "expected_imaging": "Pas d'imagerie systématique"
            },
            
            # === CAS COMPLEXES ===
            {
                "id": "complex_001",
                "category": "Cas complexe",
                "query": "Enfant 12 ans, douleurs abdominales avec vomissements, pas de fièvre, douleur péri-ombilicale",
                "expected": "INDIQUÉE",
                "pathology": "Douleur abdominale pédiatrique",
                "expected_imaging": "Échographie abdominale"
            },
            {
                "id": "complex_002", 
                "category": "Cas complexe",
                "query": "Femme 40 ans, céphalées progressives depuis 2 mois avec troubles visuels et vertiges",
                "expected": "INDIQUÉE",
                "pathology": "Processus expansif intracrânien",
                "expected_imaging": "IRM cérébrale"
            }
        ]
    
    def run_single_test(self, test_case):
        """Execute un cas de test individuel"""
        print(f"\n{Fore.YELLOW}🧪 Test {test_case['id']}: {test_case['category']}{Style.RESET_ALL}")
        print(f"📝 Requête: {test_case['query'][:80]}...")
        print(f"🎯 Attendu: {test_case['expected']} ({test_case['pathology']})")
        
        try:
            # Génération de la recommandation
            result = generate_imaging_recommendation_rag(test_case['query'], self.collection)
            
            # Classification du résultat
            if result.startswith('URGENTE'):
                actual = 'URGENTE'
            elif result.startswith('INDIQUÉE'):
                actual = 'INDIQUÉE'  
            elif result.startswith('AUCUNE'):
                actual = 'AUCUNE'
            elif result.startswith('PONCTION'):
                actual = 'PONCTION'
            else:
                actual = 'AUTRE'
            
            # Vérification
            is_correct = actual == test_case['expected']
            
            # Affichage du résultat
            status_color = Fore.GREEN if is_correct else Fore.RED
            status_icon = "✅" if is_correct else "❌"
            
            print(f"📊 Obtenu: {status_color}{actual}{Style.RESET_ALL}")
            print(f"🔍 Résultat: {status_icon} {status_color}{'CORRECT' if is_correct else 'INCORRECT'}{Style.RESET_ALL}")
            
            if not is_correct:
                print(f"💡 Recommandation complète: {result[:100]}...")
            
            # Enregistrement du résultat
            test_result = {
                'id': test_case['id'],
                'category': test_case['category'],
                'query': test_case['query'],
                'expected': test_case['expected'],
                'actual': actual,
                'correct': is_correct,
                'full_result': result,
                'pathology': test_case['pathology']
            }
            
            return test_result
            
        except Exception as e:
            print(f"❌ {Fore.RED}ERREUR: {str(e)}{Style.RESET_ALL}")
            return {
                'id': test_case['id'],
                'category': test_case['category'], 
                'expected': test_case['expected'],
                'actual': 'ERROR',
                'correct': False,
                'error': str(e)
            }
    
    def run_all_tests(self):
        """Execute tous les tests"""
        print(f"\n{Back.BLUE}{Fore.WHITE} 🚀 DÉBUT DES TESTS RAG - RECOMMANDATIONS D'IMAGERIE {Style.RESET_ALL}")
        print(f"{Fore.CYAN}Nombre de cas de test: {len(self.test_cases)}{Style.RESET_ALL}")
        
        self.results = []
        
        for test_case in self.test_cases:
            result = self.run_single_test(test_case)
            self.results.append(result)
        
        self._generate_report()
    
    def _generate_report(self):
        """Génère le rapport final des tests"""
        total_tests = len(self.results)
        correct_tests = sum(1 for r in self.results if r['correct'])
        precision = (correct_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n{Back.GREEN}{Fore.WHITE} 📊 RAPPORT FINAL DES TESTS {Style.RESET_ALL}")
        print(f"🎯 Précision globale: {Fore.GREEN}{precision:.1f}%{Style.RESET_ALL} ({correct_tests}/{total_tests})")
        
        # Analyse par catégorie
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'correct': 0}
            categories[cat]['total'] += 1
            if result['correct']:
                categories[cat]['correct'] += 1
        
        print(f"\n📈 {Fore.CYAN}Précision par catégorie:{Style.RESET_ALL}")
        for cat, stats in categories.items():
            cat_precision = (stats['correct'] / stats['total']) * 100
            color = Fore.GREEN if cat_precision >= 90 else Fore.YELLOW if cat_precision >= 70 else Fore.RED
            print(f"   • {cat}: {color}{cat_precision:.1f}%{Style.RESET_ALL} ({stats['correct']}/{stats['total']})")
        
        # Tests échoués
        failed_tests = [r for r in self.results if not r['correct']]
        if failed_tests:
            print(f"\n❌ {Fore.RED}Tests échoués:{Style.RESET_ALL}")
            for test in failed_tests:
                print(f"   • {test['id']}: {test['expected']} → {test['actual']}")

def run_performance_test():
    """Test de performance avec mesure de temps"""
    import time
    
    print(f"\n{Back.MAGENTA}{Fore.WHITE} ⚡ TEST DE PERFORMANCE {Style.RESET_ALL}")
    
    tester = ImagingRAGTester()
    test_queries = [
        "Enfant 8 ans avec céphalées et vomissements matinaux",
        "Homme 45 ans, douleur lombaire brutale avec hématurie", 
        "Femme 28 ans, douleur FID avec fièvre",
        "Patient céphalées fébriles avec raideur nucale",
        "Lombalgie commune depuis 4 semaines sans déficit"
    ]
    
    times = []
    for query in test_queries:
        start_time = time.time()
        result = generate_imaging_recommendation_rag(query, tester.collection)
        end_time = time.time()
        
        execution_time = end_time - start_time
        times.append(execution_time)
        print(f"⏱️  {execution_time:.3f}s - {query[:50]}...")
    
    avg_time = sum(times) / len(times)
    print(f"\n📊 Temps moyen de réponse: {Fore.GREEN}{avg_time:.3f}s{Style.RESET_ALL}")
    print(f"⚡ Temps min: {min(times):.3f}s | Temps max: {max(times):.3f}s")

def main():
    """Fonction principale d'exécution des tests"""
    print(f"{Back.CYAN}{Fore.WHITE} 🧪 SYSTÈME DE TESTS RAG - IMAGERIE MÉDICALE {Style.RESET_ALL}")
    
    try:
        # Tests de précision 
        tester = ImagingRAGTester()
        tester.run_all_tests()
        
        # Tests de performance
        run_performance_test()
        
        print(f"\n{Fore.GREEN}✅ Tests terminés avec succès !{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"\n❌ {Fore.RED}Erreur lors des tests: {str(e)}{Style.RESET_ALL}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
