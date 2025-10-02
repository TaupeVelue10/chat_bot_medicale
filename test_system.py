#!/usr/bin/env python3

from indexage import create_index
from ollama import get_collection, rag_query_interactive

# Test simple pour vérifier que tout fonctionne
def test_system():
    print("Test du système...")
    
    # Indexer
    create_index("guidelines.json")
    
    # Charger collection
    collection = get_collection()
    
    # Test 1: Cas normal
    print("\n=== Test 1: Céphalées sans signes d'alarme ===")
    result1, needs_more1 = rag_query_interactive("patient 30 ans céphalées pas de déficit neurologique", collection)
    print("Résultat:", result1)
    print("Besoin plus d'infos:", needs_more1)
    
    # Test 2: Cas d'urgence
    print("\n=== Test 2: Déficit neurologique ===")
    result2, needs_more2 = rag_query_interactive("patient 25 ans céphalées déficit neurologique", collection)
    print("Résultat:", result2)
    print("Besoin plus d'infos:", needs_more2)
    
    # Test 3: Cas incomplet
    print("\n=== Test 3: Informations incomplètes ===")
    result3, needs_more3 = rag_query_interactive("patient maux de tête", collection)
    print("Résultat:", result3)
    print("Besoin plus d'infos:", needs_more3)
    
    print("\n=== Tests terminés ===")

if __name__ == "__main__":
    test_system()
