#!/usr/bin/env python3
"""
Test final complet après améliorations
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, smart_guideline_selection
from colorama import Fore, Style, init
init(autoreset=True)

def test_final_complet():
    """Test final des 15 cas après améliorations"""
    
    patients_tests = [
        {"description": "Homme 22 ans, céphalée brutale en coup de tonnerre, vomissements", "expected": "Scanner/IRM cérébral"},
        {"description": "Femme 45 ans, migraine connue, pas de signe de gravité", "expected": "Pas d'imagerie"},
        {"description": "Enfant 8 ans, vomissements matinaux et céphalées persistantes", "expected": "IRM cérébrale"},
        {"description": "Homme 35 ans, douleur fosse iliaque droite, fièvre modérée", "expected": "Échographie/Scanner abdominal"},
        {"description": "Femme enceinte 30 ans, douleurs abdominales diffuses", "expected": "Échographie abdominale"},
        {"description": "Homme 50 ans, douleur lombaire simple sans signe neurologique", "expected": "Pas d'imagerie"},
        {"description": "Homme 60 ans, céphalées + troubles visuels + œdème papillaire", "expected": "IRM cérébrale"},
        {"description": "Femme 70 ans, fièvre prolongée inexpliquée", "expected": "Scanner thoraco-abdominal"},
        {"description": "Enfant 5 ans, douleurs abdominales intenses avec sang dans les selles", "expected": "Échographie"},
        {"description": "Homme 28 ans, colique lombaire typique sans fièvre", "expected": "Scanner abdominal"},
        {"description": "Homme 34 ans, dyspnée aiguë, suspicion embolie pulmonaire", "expected": "Scanner thoracique"},
        {"description": "Femme 40 ans, trouble de la marche, chutes répétées sans déficit", "expected": "Pas d'imagerie"},
        {"description": "Homme 55 ans, déficit moteur soudain hémicorps droit", "expected": "Scanner cérébral"},
        {"description": "Femme 25 ans, première crise convulsive avec confusion post-critique", "expected": "Scanner cérébral"},
        {"description": "Homme 40 ans, suspicion sclérose en plaques", "expected": "IRM cérébrale"},
    ]
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"🏆 TEST FINAL APRÈS OPTIMISATIONS")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    collection = get_collection()
    resultats = []
    
    for i, patient in enumerate(patients_tests, 1):
        print(f"\n{Fore.YELLOW}CAS {i:2d}/15{Style.RESET_ALL}")
        print(f"📝 {patient['description']}")
        
        try:
            result = smart_guideline_selection(patient['description'], collection)
            
            if result:
                # Analyse simplifiée de l'adéquation
                success = analyser_adequation_final(patient['expected'], result)
                
                if success:
                    print(f"✅ {Fore.GREEN}CORRECT{Style.RESET_ALL}")
                    resultats.append(True)
                else:
                    print(f"❌ {Fore.RED}INCORRECT{Style.RESET_ALL}")
                    resultats.append(False)
                    
                print(f"   Système: {result[:80]}...")
            else:
                print(f"❌ {Fore.RED}AUCUNE RECOMMANDATION{Style.RESET_ALL}")
                resultats.append(False)
                
        except Exception as e:
            print(f"❌ {Fore.RED}ERREUR{Style.RESET_ALL}")
            resultats.append(False)
    
    # Rapport final
    succes = sum(resultats)
    precision = (succes / len(resultats)) * 100
    
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"🎯 PERFORMANCE FINALE")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   ✅ Succès: {succes}/15")
    print(f"   📈 Précision: {precision:.1f}%")
    
    if precision >= 95:
        print(f"   🏆 {Fore.GREEN}EXCELLENCE - Système optimisé parfaitement{Style.RESET_ALL}")
    elif precision >= 90:
        print(f"   🥇 {Fore.GREEN}EXCELLENT - Système prêt pour production{Style.RESET_ALL}")
    elif precision >= 85:
        print(f"   🥈 {Fore.YELLOW}TRÈS BON - Performance remarquable{Style.RESET_ALL}")
    else:
        print(f"   🥉 {Fore.CYAN}BON - Améliorations possibles{Style.RESET_ALL}")
    
    # Cas en échec
    echecs = [i+1 for i, r in enumerate(resultats) if not r]
    if echecs:
        print(f"\n🔍 Cas perfectibles: {echecs}")
    
    return precision

def analyser_adequation_final(expected, result):
    """Analyse d'adéquation finale optimisée"""
    expected_lower = expected.lower()
    result_lower = result.lower()
    
    # Pas d'imagerie
    if "pas d'imagerie" in expected_lower:
        return "pas d'imagerie" in result_lower or "aucune" in result_lower
    
    # Scanner cérébral/IRM
    if any(cerebral in expected_lower for cerebral in ['scanner cérébral', 'irm cérébral', 'scanner/irm']):
        return any(match in result_lower for match in ['scanner', 'irm', 'cérébral', 'cérébrale'])
    
    # Échographie/Scanner abdominal  
    if any(abd in expected_lower for abd in ['échographie', 'scanner abdominal']):
        return any(match in result_lower for match in ['échographie', 'scanner', 'abdomin'])
    
    # Scanner thoracique
    if 'scanner thoracique' in expected_lower or 'scanner thoraco' in expected_lower:
        return 'scanner' in result_lower and ('thorac' in result_lower or 'pulmonaire' in result_lower)
    
    # Fallback - recherche mots-clés
    words = expected_lower.replace('-', ' ').split()
    key_words = [w for w in words if len(w) > 3]
    matches = sum(1 for word in key_words if word in result_lower)
    
    return matches >= len(key_words) * 0.4  # 40% de correspondance minimum

if __name__ == "__main__":
    precision = test_final_complet()
    print(f"\n🚀 Système optimisé à {precision:.1f}% de précision !")
