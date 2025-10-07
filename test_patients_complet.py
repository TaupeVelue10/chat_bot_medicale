#!/usr/bin/env python3
"""
Test complet du système RAG avec 15 cas patients variés
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, smart_guideline_selection
from colorama import Fore, Style, init
init(autoreset=True)

def test_patients_complet():
    """Test du système avec 15 cas patients variés"""
    
    patients_tests = [
        {"description": "Homme 22 ans, céphalée brutale en coup de tonnerre, vomissements", "expected": "Scanner cérébral urgent"},
        {"description": "Femme 45 ans, migraine connue, pas de signe de gravité", "expected": "Pas d'imagerie"},
        {"description": "Enfant 8 ans, vomissements matinaux et céphalées persistantes", "expected": "IRM cérébrale urgente"},
        {"description": "Homme 35 ans, douleur fosse iliaque droite, fièvre modérée", "expected": "Échographie abdomino-pelvienne"},
        {"description": "Femme enceinte 30 ans, douleurs abdominales diffuses", "expected": "Échographie abdominale et pelvienne"},
        {"description": "Homme 50 ans, douleur lombaire simple sans signe neurologique", "expected": "Pas d'imagerie avant 6 semaines"},
        {"description": "Homme 60 ans, céphalées + troubles visuels + œdème papillaire", "expected": "IRM cérébrale avec ARM veineuse"},
        {"description": "Femme 70 ans, fièvre prolongée inexpliquée", "expected": "Scanner thoraco-abdomino-pelvien avec injection"},
        {"description": "Enfant 5 ans, douleurs abdominales intenses avec sang dans les selles", "expected": "Échographie diagnostique et thérapeutique"},
        {"description": "Homme 28 ans, colique lombaire typique sans fièvre", "expected": "Scanner abdomino-pelvien sans injection"},
        {"description": "Homme 34 ans, dyspnée aiguë, suspicion embolie pulmonaire", "expected": "Angio-scanner thoracique"},
        {"description": "Femme 40 ans, trouble de la marche, chutes répétées sans déficit", "expected": "Pas d'imagerie systématique"},
        {"description": "Homme 55 ans, déficit moteur soudain hémicorps droit", "expected": "Scanner cérébral sans injection"},
        {"description": "Femme 25 ans, première crise convulsive avec confusion post-critique", "expected": "Scanner cérébral urgent puis IRM programmée"},
        {"description": "Homme 40 ans, suspicion sclérose en plaques", "expected": "IRM cérébrale et médullaire avec gadolinium"},
    ]
    
    print(f"{Fore.CYAN}{'='*100}")
    print(f"🏥 TEST COMPLET SYSTÈME RAG - 15 CAS PATIENTS")
    print(f"{'='*100}{Style.RESET_ALL}")
    
    collection = get_collection()
    resultats = []
    
    for i, patient in enumerate(patients_tests, 1):
        print(f"\n{Fore.YELLOW}=== CAS {i:2d}/15 ==={Style.RESET_ALL}")
        print(f"📝 Patient: {patient['description']}")
        print(f"🎯 Attendu: {patient['expected']}")
        
        try:
            # Obtenir la recommandation du système
            result = smart_guideline_selection(patient['description'], collection)
            
            if result:
                print(f"🤖 Système: {result[:100]}...")
                
                # Analyse simplifiée pour déterminer si c'est correct
                success = analyser_adequation(patient['expected'], result)
                
                if success:
                    print(f"✅ {Fore.GREEN}SUCCÈS{Style.RESET_ALL}")
                    resultats.append(True)
                else:
                    print(f"❌ {Fore.RED}ÉCHEC{Style.RESET_ALL}")
                    resultats.append(False)
            else:
                print(f"❌ {Fore.RED}AUCUNE RECOMMANDATION{Style.RESET_ALL}")
                resultats.append(False)
                
        except Exception as e:
            print(f"❌ {Fore.RED}ERREUR: {str(e)}{Style.RESET_ALL}")
            resultats.append(False)
    
    # Rapport final
    succes = sum(resultats)
    total = len(resultats)
    precision = (succes / total) * 100
    
    print(f"\n{Fore.MAGENTA}{'='*100}")
    print(f"📊 RAPPORT FINAL")
    print(f"{'='*100}{Style.RESET_ALL}")
    
    print(f"\n📈 PERFORMANCE GLOBALE:")
    print(f"   Succès: {succes}/{total}")
    print(f"   Précision: {precision:.1f}%")
    
    if precision >= 90:
        print(f"   🏆 {Fore.GREEN}EXCELLENT - Système prêt pour production{Style.RESET_ALL}")
    elif precision >= 80:
        print(f"   ✅ {Fore.YELLOW}TRÈS BON - Quelques ajustements mineurs{Style.RESET_ALL}")
    elif precision >= 70:
        print(f"   ⚠️  {Fore.CYAN}CORRECT - Améliorations recommandées{Style.RESET_ALL}")
    else:
        print(f"   ❌ {Fore.RED}INSUFFISANT - Optimisations nécessaires{Style.RESET_ALL}")
    
    # Détail des échecs
    echecs = [i+1 for i, r in enumerate(resultats) if not r]
    if echecs:
        print(f"\n🔍 CAS EN ÉCHEC: {echecs}")
        
    return precision

def analyser_adequation(expected, result):
    """Analyse si la recommandation du système correspond à l'attendu"""
    expected_lower = expected.lower()
    result_lower = result.lower()
    
    # Cas "pas d'imagerie"
    if "pas d'imagerie" in expected_lower:
        return "pas d'imagerie" in result_lower or "aucune" in result_lower
    
    # Scanner cérébral
    if "scanner cérébral" in expected_lower:
        return "scanner" in result_lower and ("cérébral" in result_lower or "crâne" in result_lower)
    
    # IRM cérébrale
    if "irm cérébrale" in expected_lower:
        return "irm" in result_lower and ("cérébral" in result_lower or "cérébrale" in result_lower)
    
    # Échographie
    if "échographie" in expected_lower:
        return "échographie" in result_lower
    
    # Scanner abdomino-pelvien
    if "scanner abdomino-pelvien" in expected_lower or "scanner thoraco-abdomino-pelvien" in expected_lower:
        return "scanner" in result_lower and ("abdomin" in result_lower or "pelvien" in result_lower)
    
    # Angio-scanner
    if "angio-scanner" in expected_lower:
        return "scanner" in result_lower and ("thorac" in result_lower or "pulmonaire" in result_lower or "angio" in result_lower)
    
    # ARM (angiographie par résonance magnétique)
    if "arm" in expected_lower:
        return "irm" in result_lower or "arm" in result_lower
    
    # Cas spéciaux - recherche de mots-clés pertinents
    key_matches = 0
    expected_words = expected_lower.split()
    
    for word in expected_words:
        if len(word) > 3 and word in result_lower:  # Mots significatifs seulement
            key_matches += 1
    
    # Si au moins 30% des mots-clés correspondent
    return key_matches >= len(expected_words) * 0.3

if __name__ == "__main__":
    try:
        precision = test_patients_complet()
        print(f"\n🎯 Test terminé avec {precision:.1f}% de précision")
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
