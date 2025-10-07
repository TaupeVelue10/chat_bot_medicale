#!/usr/bin/env python3
"""
Test final après correction du problème lombalgie/appendicite
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, smart_guideline_selection
from colorama import Fore, Style, init
init(autoreset=True)

def test_post_correction():
    """Test après correction du problème lombalgie"""
    
    cas_critiques = [
        {
            "id": "Lombalgie corrigée",
            "patient": "Homme 50 ans, douleur lombaire simple sans signe neurologique",
            "expected": "Lombalgie",
            "probleme_avant": "Sélectionnait appendicite (FID)"
        },
        {
            "id": "Appendicite préservée", 
            "patient": "Homme 35 ans, douleur fosse iliaque droite, fièvre modérée",
            "expected": "Appendicite",
            "probleme_avant": "Risque de régression"
        },
        {
            "id": "Colique néphrétique",
            "patient": "Homme 28 ans, colique lombaire typique sans fièvre", 
            "expected": "Colique néphrétique ou abdominal",
            "probleme_avant": "Confondait avec neurologie"
        },
        {
            "id": "Neurologie préservée",
            "patient": "Homme 22 ans, céphalée brutale en coup de tonnerre, vomissements",
            "expected": "Neurologique",
            "probleme_avant": "Risque de régression"
        }
    ]
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"🔧 TEST POST-CORRECTION - LOMBALGIE vs APPENDICITE")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    collection = get_collection()
    resultats = []
    
    for cas in cas_critiques:
        print(f"\n{Fore.YELLOW}=== {cas['id']} ==={Style.RESET_ALL}")
        print(f"📝 Patient: {cas['patient']}")
        print(f"🎯 Attendu: {cas['expected']}")
        print(f"⚠️  Avant: {cas['probleme_avant']}")
        
        result = smart_guideline_selection(cas['patient'], collection)
        print(f"🤖 Maintenant: {result[:80]}...")
        
        # Analyse
        success = analyser_correction(cas['expected'], result)
        
        if success:
            print(f"✅ {Fore.GREEN}CORRECT{Style.RESET_ALL}")
            resultats.append(True)
        else:
            print(f"❌ {Fore.RED}PROBLÈME{Style.RESET_ALL}")
            resultats.append(False)
    
    # Rapport
    succes = sum(resultats)
    precision = (succes / len(resultats)) * 100
    
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"📊 RÉSULTATS POST-CORRECTION")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    print(f"\n📈 PERFORMANCE:")
    print(f"   ✅ Succès: {succes}/{len(resultats)}")
    print(f"   📊 Précision: {precision:.1f}%")
    
    if precision == 100:
        print(f"   🏆 {Fore.GREEN}PARFAIT - Correction réussie sans régression{Style.RESET_ALL}")
    elif precision >= 75:
        print(f"   ✅ {Fore.YELLOW}BON - Correction réussie avec améliorations{Style.RESET_ALL}")
    else:
        print(f"   ⚠️  {Fore.RED}PROBLÈME - Régressions détectées{Style.RESET_ALL}")
    
    return precision

def analyser_correction(expected, result):
    """Analyse si la correction est réussie"""
    expected_lower = expected.lower()
    result_lower = result.lower()
    
    if 'lombalgie' in expected_lower:
        return 'lombalgie' in result_lower and 'pas d\'imagerie' in result_lower
    elif 'appendicite' in expected_lower:
        return any(terme in result_lower for terme in ['appendicite', 'fid', 'fosse iliaque'])
    elif 'colique' in expected_lower or 'abdominal' in expected_lower:
        return any(terme in result_lower for terme in ['abdomin', 'néphrétique', 'scanner', 'échographie'])
    elif 'neurologique' in expected_lower:
        return any(terme in result_lower for terme in ['cérébral', 'irm', 'scanner', 'neurologique'])
    
    return False

if __name__ == "__main__":
    precision = test_post_correction()
    print(f"\n🎯 Test post-correction: {precision:.1f}% de réussite")
