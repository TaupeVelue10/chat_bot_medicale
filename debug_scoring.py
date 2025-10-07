#!/usr/bin/env python3
"""
Test spécifique pour débugger le scoring colique néphrétique vs biliaire
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import calculate_contextual_score

def debug_scoring():
    """Teste le scoring pour comprendre pourquoi la correction ne fonctionne pas"""
    
    # Test case problématique
    text = "Homme 45 ans, douleur lombaire brutale irradiant vers l'aine avec hématurie microscopique"
    
    # Test pathologie biliaire
    print("=== TEST PATHOLOGIE BILIAIRE ===")
    score_biliaire = calculate_contextual_score(
        text, 
        "Pathologie biliaire (colique hépatique, cholécystite) : échographie abdominale en première intention",
        {'motif': 'pathologie_biliaire'},
        0.1008
    )
    print(f"Score pathologie biliaire: {score_biliaire}")
    
    # Test colique néphrétique  
    print("\n=== TEST COLIQUE NÉPHRÉTIQUE ===")
    score_nephretique = calculate_contextual_score(
        text,
        "Colique néphrétique (douleur lombaire, nausées, syndrome obstructif) : scanner abdomino-pelvien",
        {'motif': 'colique_nephretique'},
        0.0998
    )
    print(f"Score colique néphrétique: {score_nephretique}")
    
    print(f"\nDifférence: {score_biliaire - score_nephretique}")
    
    # Test avec mots-clés spécifiques
    print("\n=== ANALYSE DÉTAILLÉE ===")
    
    # Vérification des mots-clés néphrétiques dans le texte
    nephro_keywords = ['lombaire', 'aine', 'hématurie', 'calcul', 'lithiase']
    print("Mots-clés néphrétiques détectés:")
    for keyword in nephro_keywords:
        if keyword in text.lower():
            print(f"  ✅ {keyword}")
        else:
            print(f"  ❌ {keyword}")
    
    # Vérification des mots-clés biliaires
    bili_keywords = ['sous-costale droite', 'vésicule', 'cholécystite']
    print("\nMots-clés biliaires spécifiques détectés:")
    for keyword in bili_keywords:
        if keyword in text.lower():
            print(f"  ✅ {keyword}")
        else:
            print(f"  ❌ {keyword}")
    
    # Test présence 'colique' dans le texte
    print(f"\nPrésence 'colique' dans texte: {'colique' in text.lower()}")
    print(f"Présence 'colique' dans guideline biliaire: {'colique' in 'Pathologie biliaire (colique hépatique, cholécystite)'}")

if __name__ == "__main__":
    debug_scoring()
