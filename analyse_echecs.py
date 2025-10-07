#!/usr/bin/env python3
"""
Analyse détaillée des cas en échec
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, smart_guideline_selection
from colorama import Fore, Style, init
init(autoreset=True)

def analyser_echecs():
    """Analyse détaillée des cas 1 et 10 qui ont échoué"""
    
    echecs = [
        {
            "id": 1,
            "description": "Homme 22 ans, céphalée brutale en coup de tonnerre, vomissements",
            "expected": "Scanner cérébral urgent",
            "probleme": "Système a recommandé IRM au lieu de scanner"
        },
        {
            "id": 10, 
            "description": "Homme 28 ans, colique lombaire typique sans fièvre",
            "expected": "Scanner abdomino-pelvien sans injection",
            "probleme": "Système a recommandé IRM cérébrale (SEP) au lieu de scanner abdominal"
        }
    ]
    
    print(f"{Fore.RED}{'='*80}")
    print(f"🔍 ANALYSE DES ÉCHECS")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    collection = get_collection()
    
    for echec in echecs:
        print(f"\n{Fore.YELLOW}=== CAS {echec['id']} - ÉCHEC ==={Style.RESET_ALL}")
        print(f"📝 Patient: {echec['description']}")
        print(f"🎯 Attendu: {echec['expected']}")
        print(f"⚠️  Problème: {echec['probleme']}")
        
        # Test avec le système actuel
        result = smart_guideline_selection(echec['description'], collection)
        print(f"🤖 Système actuel: {result[:120]}...")
        
        # Analyse des mots-clés manquants
        print(f"\n🔍 ANALYSE:")
        
        if echec['id'] == 1:
            print(f"   • 'Coup de tonnerre' devrait déclencher 'scanner cérébral urgent'")
            print(f"   • Système n'a pas reconnu l'urgence hémorragique")
            print(f"   • Amélioration: Renforcer détection 'coup de tonnerre' → scanner")
            
        elif echec['id'] == 10:
            print(f"   • 'Colique lombaire' devrait déclencher 'colique néphrétique'")  
            print(f"   • Système confond avec troubles neurologiques")
            print(f"   • Amélioration: Renforcer détection 'colique lombaire' → néphrétique")

def recommandations():
    """Recommandations d'amélioration"""
    
    print(f"\n{Fore.GREEN}{'='*80}")
    print(f"💡 RECOMMANDATIONS D'AMÉLIORATION")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    print(f"\n🎯 ACTIONS PRIORITAIRES:")
    print(f"1. Renforcer détection 'coup de tonnerre' → scanner cérébral urgent")
    print(f"2. Améliorer reconnaissance 'colique lombaire' → néphrétique")
    
    print(f"\n📈 IMPACT ESTIMÉ:")
    print(f"   Précision actuelle: 86.7%")
    print(f"   Précision cible: 93.3% (+2 cas)")
    
    print(f"\n✅ POINTS FORTS IDENTIFIÉS:")
    print(f"   • Excellent sur cas pédiatriques (100%)")
    print(f"   • Parfait sur cas de grossesse")
    print(f"   • Très bon sur lombalgies communes")
    print(f"   • Excellent sur urgences neurologiques (déficits)")

if __name__ == "__main__":
    analyser_echecs()
    recommandations()
