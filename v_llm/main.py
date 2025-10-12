from pathlib import Path
from indexage import create_index
from ollama import rag_biomistral_query

def main():
    print("Assistant d'aide à la prescription d'imagerie")
    print("-------------------------------------------------------------\n")

    # Chargement du RAG
    guidelines_path = Path(__file__).parent / "guidelines.json"
    collection = create_index(str(guidelines_path))

    print("Décrivez le cas clinique du patient (ou tapez 'quit' pour quitter)\n")
    
    # Historique de la conversation pour accumuler les informations
    conversation_history = []

    while True:
        question = input("Médecin: ")
        if question.lower() in ["quit", "exit", "q"]:
            print("Fin de session.")
            break

        # Ajouter la question à l'historique
        conversation_history.append(question)
        
        # Construire le cas clinique complet avec tout l'historique
        full_case = " | ".join(conversation_history)
        
        response = rag_biomistral_query(full_case, collection)
        print(f"\nBioMistral : {response}\n")

if __name__ == "__main__":
    main()
