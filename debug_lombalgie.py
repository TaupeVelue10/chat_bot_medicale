#!/usr/bin/env python3
"""
Debug pourquoi lombalgie n'est pas sélectionnée
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection, enhance_medical_query, calculate_contextual_score

def debug_lombalgie():
    """Debug lombalgie vs appendicite"""
    
    text = "Homme 50 ans, douleur lombaire simple sans signe neurologique"
    collection = get_collection()
    
    print("=== DEBUG LOMBALGIE ===")
    print(f"Query: {text}")
    
    # Enrichissement
    enhanced = enhance_medical_query(text)
    print(f"Enrichi: {enhanced}")
    
    # Recherche vectorielle
    results = collection.query(
        query_texts=[enhanced],
        n_results=10,
        include=['documents', 'metadatas', 'distances']
    )
    
    print(f"\n=== TOP 10 AVEC SCORES ===")
    for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        score = calculate_contextual_score(text, doc, meta, dist)
        motif = meta.get('motif', 'unknown')
        
        marker = " [LOMBALGIE]" if motif == 'lombalgie' else ""
        marker += " [APPENDICITE]" if motif == 'douleur_abdominale' else ""
        
        print(f"{i+1:2d}. Score: {score:.4f} | Dist: {dist:.4f} | {motif}{marker}")
        if motif in ['lombalgie', 'douleur_abdominale']:
            print(f"    Doc: {doc[:80]}...")

if __name__ == "__main__":
    debug_lombalgie()
