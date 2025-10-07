#!/usr/bin/env python3
"""
Test complet du système pour colique néphrétique
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import smart_guideline_selection, get_collection, calculate_contextual_score, enhance_medical_query

def test_complete_scoring():
    """Test complet du scoring pour comprendre le problème"""
    
    text = "Homme 45 ans, douleur lombaire brutale irradiant vers l'aine avec hématurie microscopique"
    collection = get_collection()
    
    print("=== TEST COMPLET DU SYSTÈME ===")
    print(f"Query originale: {text}")
    
    # Test enrichissement
    enhanced = enhance_medical_query(text)
    print(f"\nQuery enrichie: {enhanced}")
    
    # Test recherche vectorielle
    results = collection.query(
        query_texts=[enhanced],
        n_results=20,
        include=['documents', 'metadatas', 'distances']
    )
    
    print(f"\n=== TOP 20 CANDIDATES AVEC SCORES ===")
    candidates = []
    for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        score = calculate_contextual_score(text, doc, meta, dist)
        candidates.append({
            'rank': i+1,
            'motif': meta.get('motif', 'unknown'),
            'score': score,
            'distance': dist,
            'doc': doc[:80] + "..."
        })
    
    # Trier par score contextuel 
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    for i, candidate in enumerate(candidates[:10]):
        marker = " [SÉLECTIONNÉ]" if i == 0 else ""
        print(f"{i+1:2d}. Score: {candidate['score']:.4f} | Dist: {candidate['distance']:.4f} | {candidate['motif']}{marker}")
        print(f"    {candidate['doc']}")
        
    print(f"\n=== RÉSULTAT FINAL ===")
    result = smart_guideline_selection(text, collection)
    print(f"Guideline sélectionnée: {result[:100]}...")

if __name__ == "__main__":
    test_complete_scoring()
