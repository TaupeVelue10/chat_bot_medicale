#!/usr/bin/env python3
"""
Test script automatisé pour valider le modèle client v2
"""

import subprocess
import sys

def test_case(description, input_text, expected_keywords):
    """Execute un test et vérifie si les mots-clés attendus sont présents"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"Input: {input_text}")
    print('-'*70)
    
    try:
        result = subprocess.run(
            ['ollama', 'run', 'biomistral-clinical'],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        print(f"Output: {output}")
        
        # Vérifier les mots-clés
        success = all(keyword.lower() in output.lower() for keyword in expected_keywords)
        
        if success:
            print(f"✅ RÉUSSI - Tous les mots-clés trouvés: {expected_keywords}")
        else:
            print(f"❌ ÉCHEC - Mots-clés manquants")
            missing = [kw for kw in expected_keywords if kw.lower() not in output.lower()]
            print(f"   Manquants: {missing}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT (>30s)")
        return False
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False


def main():
    print("🧪 VALIDATION MODÈLE CLIENT V2.0 - CÉPHALÉES")
    print("="*70)
    
    tests = [
        {
            "description": "Cas simple → Questions Groupe 1",
            "input": "Patiente 34 ans, céphalées",
            "expected": ["groupe 1", "fièvre", "brutale", "déficit"]
        },
        {
            "description": "Urgence (fièvre) → Triage immédiat",
            "input": "Patient 45 ans, céphalées depuis 2 jours avec fièvre à 39°C",
            "expected": ["urgence", "adresser"]
        },
        {
            "description": "Urgence (brutal) → Triage immédiat",
            "input": "Patiente 28 ans, céphalées brutales et intenses depuis 2 heures",
            "expected": ["urgence"]
        },
        {
            "description": "Contexte oncologique → Scanner injection",
            "input": "Patiente 55 ans avec antécédent de cancer du sein, céphalées progressives",
            "expected": ["scanner", "injection", "oncologique"]
        },
        {
            "description": "Cas complet sans urgence → Recommandation IRM",
            "input": "Patient 40 ans, céphalées progressives depuis 1 mois, pas de fièvre, pas de déficit, pas d'antécédent",
            "expected": ["recommandation", "irm"]
        },
    ]
    
    results = []
    for test in tests:
        success = test_case(
            test["description"],
            test["input"],
            test["expected"]
        )
        results.append(success)
    
    # Résumé
    print(f"\n{'='*70}")
    print("📊 RÉSUMÉ DES TESTS")
    print('='*70)
    passed = sum(results)
    total = len(results)
    print(f"Réussis: {passed}/{total} ({passed*100//total}%)")
    
    if passed == total:
        print("✅ TOUS LES TESTS RÉUSSIS !")
        return 0
    else:
        print(f"❌ {total - passed} test(s) échoué(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
