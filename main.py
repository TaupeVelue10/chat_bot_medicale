from indexage import create_index
from ollama import get_collection, rag_query_interactive

def chat_interactif(collection):
    """Mode chat interactif avec le médecin - conversation continue"""
    print("Assistant médical d'imagerie")
    print("Tapez 'quit', 'exit' ou 'q' pour quitter\n")
    
    # Contexte de conversation pour maintenir l'historique
    conversation_context = ""
    
    while True:
        if not conversation_context:
            question = input("Décrivez votre cas clinique : ")
        else:
            question = input("Votre réponse : ")
        
        if question.lower() in ['quit', 'exit', 'q', 'quitter']:
            print("Au revoir.")
            break
            
        if question.strip():
            # Ajouter la nouvelle question au contexte
            if conversation_context:
                conversation_context += f"\n\nInformation supplémentaire : {question}"
                current_input = conversation_context
            else:
                current_input = question
                conversation_context = question
            
            reponse, needs_more_info = rag_query_interactive(current_input, collection)
            print(f"{reponse}\n")
            
            # Si une réponse complète a été donnée, réinitialiser le contexte
            if not needs_more_info:
                print("Recommandation fournie. Vous pouvez poser une nouvelle question.")
                conversation_context = ""
            
            print("-" * 60)

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

