#!/usr/bin/env python3
"""
Identifier le problème de guideline thoracique parlant de FID
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, smart_guideline_selection
from colorama import Fore, Style, init
init(autoreset=True)

def identifier_probleme():
    """Identifier quel cas thoracique déclenche une guideline abdominale"""
    
    cas_thoraciques = [
        "Homme 34 ans, dyspnée aiguë, suspicion embolie pulmonaire",
        "Femme 40 ans, dyspnée chronique, essoufflement effort",
        "Homme 25 ans, douleur thoracique aiguë",
        "Femme 35 ans, oppression thoracique"
    ]
    
    collection = get_collection()
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"🔍 RECHERCHE GUIDELINE THORACIQUE/ABDOMINALE PROBLÉMATIQUE")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    for i, cas in enumerate(cas_thoraciques, 1):
        print(f"\n{Fore.YELLOW}CAS {i}{Style.RESET_ALL}")
        print(f"Patient: {cas}")
        
        result = smart_guideline_selection(cas, collection)
        print(f"Guideline: {result[:120]}...")
        
        # Vérifier si guideline thoracique parle de FID/abdomen
        if any(terme in result.lower() for terme in ['fid', 'fosse iliaque', 'appendicite', 'mcburney']):
            print(f"🚨 {Fore.RED}PROBLÈME DÉTECTÉ: Guideline thoracique avec termes abdominaux{Style.RESET_ALL}")
        elif any(terme in result.lower() for terme in ['thoracique', 'pulmonaire', 'dyspnée']):
            print(f"✅ {Fore.GREEN}CORRECT: Guideline thoracique cohérente{Style.RESET_ALL}")
        else:
            print(f"⚠️  {Fore.YELLOW}À VÉRIFIER: Guideline inattendue{Style.RESET_ALL}")
    
    # Test cas mixtes qui pourraient créer confusion
    print(f"\n{Fore.CYAN}=== TESTS CAS MIXTES ==={Style.RESET_ALL}")
    
    cas_mixtes = [
        "Homme 50 ans, douleur lombaire simple sans signe neurologique",  # Le cas 6 qui était problématique
        "Femme 28 ans, douleur abdominale et dyspnée"
    ]
    
    for cas in cas_mixtes:
        print(f"\nCas mixte: {cas}")
        result = smart_guideline_selection(cas, collection)
        print(f"Guideline: {result[:120]}...")
        
        if 'fid' in result.lower() and 'thoracique' in cas.lower():
            print(f"🚨 {Fore.RED}PROBLÈME: Confusion thoracique/abdominale{Style.RESET_ALL}")

if __name__ == "__main__":
    identifier_probleme()
