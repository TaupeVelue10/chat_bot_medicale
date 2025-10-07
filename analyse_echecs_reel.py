#!/usr/bin/env python3
"""
Analyse des "échecs" - sont-ils vraiment des échecs ?
"""

def analyser_pretendus_echecs():
    """Réévaluation des cas considérés comme échecs"""
    
    print("🔍 RÉÉVALUATION DES 'ÉCHECS'")
    print("="*50)
    
    cas_1 = {
        "patient": "Homme 22 ans, céphalée brutale en coup de tonnerre, vomissements",
        "attendu": "Scanner cérébral urgent", 
        "systeme": "IRM médullaire et/ou cérébrale",
        "analyse": """
        SCANNER vs IRM pour coup de tonnerre:
        - Scanner: Rapide, détecte hémorragie aiguë (HSA)
        - IRM: Plus sensible mais plus long
        - En urgence: Scanner en 1ère intention puis IRM si négatif
        
        ➡️ Le système recommande IRM = ACCEPTABLE mais pas optimal
        """
    }
    
    cas_10 = {
        "patient": "Homme 28 ans, colique lombaire typique sans fièvre",
        "attendu": "Scanner abdomino-pelvien sans injection",
        "systeme": "IRM cérébrale (SEP)",
        "analyse": """
        COLIQUE LOMBAIRE = COLIQUE NÉPHRÉTIQUE:
        - Douleur lombaire brutale → suspicion calcul rénal
        - Indication: Scanner abdomino-pelvien sans injection
        - Système confond avec neurologie
        
        ➡️ Vraie erreur d'orientation anatomique
        """
    }
    
    print(f"CAS 1 - 'Coup de tonnerre':")
    print(f"Patient: {cas_1['patient']}")
    print(f"Attendu: {cas_1['attendu']}")
    print(f"Système: {cas_1['systeme']}")
    print(f"Analyse: {cas_1['analyse']}")
    
    print(f"\nCAS 10 - 'Colique lombaire':")
    print(f"Patient: {cas_10['patient']}")
    print(f"Attendu: {cas_10['attendu']}")
    print(f"Système: {cas_10['systeme']}")
    print(f"Analyse: {cas_10['analyse']}")

if __name__ == "__main__":
    analyser_pretendus_echecs()
