#!/usr/bin/env python3
"""
Test exact du diagnostic pour reproduire le problème
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, enhance_medical_query, calculate_contextual_score

def test_exact_diagnostic():
    """Reproduire exactement les conditions du diagnostic"""
    
    text = "Homme 45 ans, douleur lombaire brutale irradiant vers l'aine avec hématurie microscopique"
    collection = get_collection()
    
    # Utiliser l'enrichissement exact
    enhanced_query = enhance_medical_query(text)
    
    # Recherche avec 20 résultats comme dans ollama.py
    results = collection.query(
        query_texts=[enhanced_query],
        n_results=20,  # Utilise n_results=20 comme maintenant dans ollama.py
        include=['documents', 'metadatas', 'distances']
    )
    
    print("=== REPRODUCTION DU DIAGNOSTIC ===")
    print(f"Query originale: {text}")
    print(f"Query enrichie: {enhanced_query}")
    
    print(f"\n=== TOP 10 AVEC SCORES (comme diagnostic) ===")
    candidates = []
    for i, (doc, meta, dist) in enumerate(zip(results['documents'][0][:10], results['metadatas'][0][:10], results['distances'][0][:10])):
        score = calculate_contextual_score(text, doc, meta, dist)
        motif = meta.get('motif', 'unknown')
        
        marker = " [ATTENDU]" if motif == 'colique_nephretique' else ""
        print(f"{i+1:2d}. Score: {score:.4f} | Dist: {dist:.4f} | {motif}{marker}")
        print(f"    {doc[:80]}...")
        
        candidates.append({
            'score': score,
            'motif': motif,
            'doc': doc,
            'meta': meta,
            'dist': dist
        })
    
    # Trouver le meilleur score
    best = max(candidates, key=lambda x: x['score'])
    print(f"\n=== MEILLEUR SCORE ===")
    print(f"Motif: {best['motif']}")
    print(f"Score: {best['score']:.4f}")
    
    # Test spécifique colique néphrétique s'il existe
    nephretique_candidates = [c for c in candidates if c['motif'] == 'colique_nephretique']
    if nephretique_candidates:
        neph = nephretique_candidates[0]
        print(f"\n=== COLIQUE NÉPHRÉTIQUE ===")
        print(f"Score: {neph['score']:.4f}")
        print(f"Distance: {neph['dist']:.4f}")
    else:
        print(f"\n❌ COLIQUE NÉPHRÉTIQUE non trouvé dans top 10")

if __name__ == "__main__":
    test_exact_diagnostic()
