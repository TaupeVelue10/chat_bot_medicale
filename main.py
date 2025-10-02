from indexage import create_index
from ollama import get_collection, rag_query_interactive

def chat_interactif(collection):
    """Interface de chat interactive pour l'assistant médical"""
    print("Assistant médical d'imagerie")
    print("Tapez 'quit', 'exit' ou 'q' pour quitter\n")
    
    conversation_context = ""
    additional_info = []  # Liste pour accumuler toutes les informations complémentaires
    
    while True:
        # Demander une entrée utilisateur
        user_input = input("Décrivez votre cas clinique : ")
        
        # Vérifier si l'utilisateur veut quitter
        if user_input.lower().strip() in ['quit', 'exit', 'q']:
            print("Au revoir.")
            break
        
        # Construire le contexte de conversation
        if conversation_context:
            # Ajouter la nouvelle information à la liste
            additional_info.append(user_input)
            # Construire le contexte complet avec TOUTES les informations
            all_additional = ", ".join(additional_info)
            current_input = f"Cas initial : {conversation_context}\nInformations complémentaires : {all_additional}"
        else:
            current_input = user_input
            conversation_context = user_input
        
        # Obtenir la réponse du système RAG
        reponse, needs_more_info = rag_query_interactive(current_input, collection)
        
        print("----------------------------------------")
        if needs_more_info:
            print("Complément d'information :", reponse)
            # Continuer la conversation sans réinitialiser le contexte
        else:
            print(reponse)
            print("Vous pouvez poser une nouvelle question.")
            # Réinitialiser le contexte pour une nouvelle consultation
            conversation_context = ""
            additional_info = []
        print("----------------------------------------")

def main():
    # Étape 1 : Indexer guidelines si nécessaire (création ou mise à jour)
    create_index("guidelines.json")
    
    # Étape 2 : Charger la collection
    collection = get_collection()
    
    # Étape 3 : Démarrer le chat interactif
    chat_interactif(collection)

if __name__ == "__main__":
    main()

