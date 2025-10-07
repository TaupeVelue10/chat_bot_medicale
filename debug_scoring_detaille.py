#!/usr/bin/env python3
"""
Debug approfondi du scoring lombalgie
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import calculate_contextual_score

def debug_scoring_lombalgie():
    """Debug détaillé du scoring lombalgie"""
    
    text = "Homme 50 ans, douleur lombaire simple sans signe neurologique"
    guideline = "Lombalgie commune : pas d'imagerie avant 6 semaines sauf red flags (déficit neurologique, syndrome de la queue de cheval, fièvre, cancer, traumatisme). IRM lombaire si radiculalgie persistante >6 semaines."
    metadata = {'motif': 'lombalgie', 'source': 'HAS / SOFMMOO, 2023'}
    distance = 0.0679
    
    print("=== DEBUG DÉTAILLÉ SCORING LOMBALGIE ===")
    print(f"Text: {text}")
    print(f"Motif: {metadata['motif']}")
    print(f"Distance: {distance}")
    
    # Test étape par étape
    base_score = 1.0 - distance
    print(f"\n1. Score de base (1 - distance): {base_score}")
    
    # Vérifier les filtres qui pourraient mettre à 0
    text_lower = text.lower()
    guideline_lower = guideline.lower()
    motif = metadata.get('motif', '').lower()
    
    print(f"\n2. Vérifications des filtres:")
    
    # Filtre grossesse
    if 'grossesse' in motif or 'enceinte' in guideline_lower:
        print("   Filtre grossesse: ACTIVÉ")
        if 'enceinte' in text_lower or 'grossesse' in text_lower:
            print("   → Pas de pénalité (grossesse mentionnée)")
        else:
            print("   → PÉNALITÉ grossesse appliquée")
    else:
        print("   Filtre grossesse: Non applicable")
    
    # Filtre pédiatrique
    if 'pediatrie' in motif or 'enfant' in guideline_lower:
        print("   Filtre pédiatrique: ACTIVÉ")
        import re
        age_match = re.search(r'(\d+)\s*ans?', text_lower)
        if age_match:
            age = int(age_match.group(1))
            print(f"   → Âge détecté: {age} ans")
            if age > 16:
                print("   → PÉNALITÉ pédiatrique (adulte)")
        else:
            print("   → Pas d'âge détecté")
    else:
        print("   Filtre pédiatrique: Non applicable")
    
    # Test le scoring complet
    score_final = calculate_contextual_score(text, guideline, metadata, distance)
    print(f"\n3. Score final calculé: {score_final}")
    
    # Test pathology_boosts
    pathology_boosts = {
        'lombalgie': ['chronique', '6 semaines', 'commune', 'radiculalgie', 'lombaire simple', 'lombaire commune', 'sans signe neurologique']
    }
    
    print(f"\n4. Vérification pathology_boosts lombalgie:")
    if 'lombalgie' in motif:
        keywords = pathology_boosts['lombalgie']
        matches = [keyword for keyword in keywords if keyword in text_lower]
        print(f"   Keywords: {keywords}")
        print(f"   Matches trouvés: {matches}")
        if matches:
            print(f"   → Boost attendu: +0.5")
        else:
            print(f"   → Pas de boost")

if __name__ == "__main__":
    debug_scoring_lombalgie()
