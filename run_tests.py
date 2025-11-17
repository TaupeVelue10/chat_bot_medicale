"""
Script d'exécution des tests de performance pour le chatbot médical
Auteur: Noam
Date: 15 novembre 2025
"""

import sys
import subprocess
from pathlib import Path
import argparse

def run_tests(test_pattern="*", verbose=True):
    """Exécute les tests de performance"""
    
    # Chemin vers le fichier de tests
    test_file = Path(__file__).parent / "v_llm" / "tests" / "test_noam.py"
    venv_python = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"
    
    if not test_file.exists():
        print(f"❌ Fichier de test introuvable: {test_file}")
        return False
    
    if not venv_python.exists():
        print(f"❌ Python de l'environnement virtuel introuvable: {venv_python}")
        return False
    
    print("🧪 Lancement des tests de performance du chatbot médical...")
    print("=" * 60)
    
    # Commande pour exécuter les tests
    cmd = [str(venv_python), str(test_file)]
    
    if verbose:
        cmd.append("-v")
    
    try:
        # Exécuter les tests
        result = subprocess.run(cmd, 
                              cwd=Path(__file__).parent / "v_llm",
                              capture_output=False, 
                              text=True)
        
        if result.returncode == 0:
            print("\n✅ Tous les tests ont réussi !")
            return True
        else:
            print(f"\n❌ Certains tests ont échoué (code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des tests: {e}")
        return False

def generate_report():
    """Génère un rapport de performance détaillé"""
    print("📊 Génération du rapport de performance...")
    
    # Ici on pourrait ajouter du code pour générer un rapport HTML/PDF
    # Pour l'instant, on indique juste où trouver les résultats
    print("Les métriques de performance sont affichées dans la sortie des tests.")
    print("Consultez la section 'RAPPORT DE PERFORMANCE FINAL' en fin d'exécution.")

def main():
    parser = argparse.ArgumentParser(description="Tests de performance du chatbot médical")
    parser.add_argument("--pattern", "-p", default="*", 
                       help="Pattern des tests à exécuter")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Mode verbeux")
    parser.add_argument("--report", "-r", action="store_true", 
                       help="Générer un rapport de performance")
    
    args = parser.parse_args()
    
    print("🏥 Tests de Performance - Chatbot Médical")
    print("Auteur: Noam")
    print("=" * 50)
    
    # Exécuter les tests
    success = run_tests(args.pattern, args.verbose)
    
    # Générer le rapport si demandé
    if args.report:
        generate_report()
    
    # Code de sortie
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()