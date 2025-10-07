from indexage import create_index
from ollama import get_collection, rag_query_interactive

def chat_interactif(collection):
    """Interface de chat interactive pour l'assistant médical"""
    print("🏥 Assistant médical d'imagerie - Système RAG optimisé")
    print("🚀 Mode : BlueBERT + scoring contextuel intelligent")
    print("Tapez 'quit', 'exit' ou 'q' pour quitter\n")
    
    conversation_context = ""
    additional_info = []  # Liste pour accumuler toutes les informations complémentaires
    is_first_turn = True
    
    while True:
        # Demander une entrée utilisateur
        if is_first_turn:
            user_input = input("Décrivez votre cas clinique : ")
        else:
            user_input = input("Informations complémentaires : ")
        
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
            is_first_interaction = False
        else:
            current_input = user_input
            conversation_context = user_input
            is_first_interaction = True
        
        # Obtenir la réponse du système RAG
        reponse, needs_more_info = rag_query_interactive(current_input, collection, is_first_interaction)
        
        print("\n" + "-"*50)
        if needs_more_info:
            print("Questions de clarification :")
            print(reponse)
            is_first_turn = False
            # Continuer la conversation sans réinitialiser le contexte
        else:
            print(reponse)
            print("\nVous pouvez poser une nouvelle question.")
            # Réinitialiser le contexte pour une nouvelle consultation
            conversation_context = ""
            additional_info = []
            is_first_turn = True
        print("-"*50 + "\n")

def main():
    # Étape 1 : Indexer guidelines si nécessaire (création ou mise à jour)
    create_index("guidelines.json")
    
    # Étape 2 : Charger la collection
    collection = get_collection()
    
    # Étape 3 : Démarrer le chat interactif
    chat_interactif(collection)

if __name__ == "__main__":
    main()

