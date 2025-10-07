#!/usr/bin/env python3
"""
Test des améliorations sur les cas problématiques
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, smart_guideline_selection
from colorama import Fore, Style, init
init(autoreset=True)

def test_ameliorations():
    """Test des cas problématiques après améliorations"""
    
    cas_tests = [
        {
            "id": "Cas 1",
            "patient": "Homme 22 ans, céphalée brutale en coup de tonnerre, vomissements",
            "expected": "Scanner cérébral ou IRM cérébrale",
            "type": "Neurologique"
        },
        {
            "id": "Cas 10", 
            "patient": "Homme 28 ans, colique lombaire typique sans fièvre",
            "expected": "Scanner abdomino-pelvien (colique néphrétique)",
            "type": "Abdominal"
        },
        {
            "id": "Cas variante",
            "patient": "Femme 35 ans, douleur irradiant vers l'aine avec hématurie",
            "expected": "Scanner abdomino-pelvien (colique néphrétique)",
            "type": "Abdominal"
        },
        {
            "id": "Cas différentiel",
            "patient": "Homme 45 ans, colique typique lombaire sans fièvre ni hématurie",
            "expected": "Scanner abdomino-pelvien (colique néphrétique)",
            "type": "Abdominal"
        }
    ]
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"🔧 TEST DES AMÉLIORATIONS")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    collection = get_collection()
    resultats = []
    
    for cas in cas_tests:
        print(f"\n{Fore.YELLOW}=== {cas['id']} ==={Style.RESET_ALL}")
        print(f"📝 Patient: {cas['patient']}")
        print(f"🎯 Attendu: {cas['expected']}")
        print(f"🏥 Type: {cas['type']}")
        
        try:
            result = smart_guideline_selection(cas['patient'], collection)
            print(f"🤖 Système: {result[:100]}...")
            
            # Analyse du résultat
            success = analyser_orientation(cas['type'], result)
            
            if success:
                print(f"✅ {Fore.GREEN}ORIENTATION CORRECTE{Style.RESET_ALL}")
                resultats.append(True)
            else:
                print(f"❌ {Fore.RED}ORIENTATION INCORRECTE{Style.RESET_ALL}")
                resultats.append(False)
                
        except Exception as e:
            print(f"❌ {Fore.RED}ERREUR: {str(e)}{Style.RESET_ALL}")
            resultats.append(False)
    
    # Rapport
    succes = sum(resultats)
    total = len(resultats)
    precision = (succes / total) * 100
    
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"📊 RÉSULTATS APRÈS AMÉLIORATIONS")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    print(f"\n📈 PERFORMANCE:")
    print(f"   Succès: {succes}/{total}")
    print(f"   Précision orientation: {precision:.1f}%")
    
    return precision

def analyser_orientation(type_attendu, result):
    """Analyse si l'orientation anatomique est correcte"""
    result_lower = result.lower()
    
    if type_attendu == "Neurologique":
        # Accepter scanner cérébral, IRM cérébrale, ou neurologique
        return any(neuro in result_lower for neuro in ['cérébral', 'cérébrale', 'irm', 'scanner', 'neurologique'])
    
    elif type_attendu == "Abdominal":
        # Doit être abdominal, pas neurologique
        if any(neuro in result_lower for neuro in ['cérébral', 'cérébrale', 'sclérose', 'sep', 'troubles marche']):
            return False  # Orientation neurologique = échec
        return any(abd in result_lower for abd in ['abdomin', 'néphrétique', 'scanner', 'échographie', 'appendic', 'biliaire'])
    
    return False

if __name__ == "__main__":
    try:
        precision = test_ameliorations()
        print(f"\n🎯 Test terminé - Orientation anatomique: {precision:.1f}%")
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
