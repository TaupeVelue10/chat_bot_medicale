from indexage import create_index
from ollama import get_collection, rag_query_interactive

def chat_interactif(collection):
    """Mode chat interactif avec le médecin - conversation continue"""
    print("Assistant médical d'imagerie")
    print("Tapez 'quit', 'exit' ou 'q' pour quitter\n")
    
    # Contexte de conversation pour maintenir l'historique
    conversation_history = []
    
    while True:
        if not conversation_history:
            question = input("Décrivez votre cas clinique : ")
        else:
            question = input("Complément d'information : ")
        
        if question.lower() in ['quit', 'exit', 'q', 'quitter']:
            print("Au revoir.")
            break
            
        if question.strip():
            # Ajouter la nouvelle information à l'historique
            conversation_history.append(question)
            
            # Construire le contexte complet de manière structurée
            if len(conversation_history) == 1:
                current_input = conversation_history[0]
            else:
                current_input = f"Cas initial : {conversation_history[0]}\n"
                current_input += "Informations complémentaires : " + " | ".join(conversation_history[1:])
            
            reponse, needs_more_info = rag_query_interactive(current_input, collection)
            print(f"{reponse}\n")
            
            # Si une réponse complète a été donnée, réinitialiser pour un nouveau cas
            if not needs_more_info:
                print("Vous pouvez poser une nouvelle question.")
                conversation_history = []
            
            print("-" * 40)

def main():
    """Fonction principale - évite les problèmes de cache et d'état"""
    # Étape 1 : Indexer guidelines (création ou mise à jour)
    create_index("guidelines.json")
    
    # Étape 2 : Charger la collection
    collection = get_collection()
    
    # Lancement direct du mode interactif
    chat_interactif(collection)

# Point d'entrée unique
if __name__ == "__main__":
    main()

