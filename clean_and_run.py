#!/usr/bin/env python3
"""
Script de nettoyage et lancement propre de l'assistant médical
Utilise ce script si tu as des problèmes de cache ou d'état
"""

import os
import shutil
import subprocess
import sys

def clean_cache():
    """Nettoie tous les caches et fichiers temporaires"""
    # Supprimer le cache Python
    if os.path.exists("__pycache__"):
        shutil.rmtree("__pycache__")
    
    # Supprimer la base de données ChromaDB pour repartir à zéro
    if os.path.exists("rag_db"):
        shutil.rmtree("rag_db")

def main():
    # Nettoyer d'abord
    clean_cache()
    
    # Puis lancer le programme principal
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\nAu revoir !")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    main()
