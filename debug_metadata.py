#!/usr/bin/env python3
"""
Debug métadonnées pour colique néphrétique
"""

import sys
sys.path.append('/Users/alexpeirano/Desktop/commande_entreprise')

from ollama import get_collection

def debug_metadata():
    """Vérifier les métadonnées de colique néphrétique"""
    
    collection = get_collection()
    
    # Recherche spécifique pour colique néphrétique
    results = collection.query(
        query_texts=["colique néphrétique douleur lombaire calcul"],
        n_results=5,
        include=['documents', 'metadatas', 'distances']
    )
    
    print("=== MÉTADONNÉES COLIQUE NÉPHRÉTIQUE ===")
    for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        print(f"\n{i+1}. Distance: {dist:.4f}")
        print(f"   Métadonnées: {meta}")
        print(f"   Document extrait: {doc[:100]}...")
        
        # Vérifier si c'est bien la colique néphrétique
        if 'néphrétique' in doc.lower() or 'nephretique' in doc.lower():
            print("   ✅ TROUVÉ: Colique néphrétique")

if __name__ == "__main__":
    debug_metadata()
