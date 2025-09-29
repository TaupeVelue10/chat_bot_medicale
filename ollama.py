import requests
import chromadb

def get_collection(db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_collection(collection_name)

def query_ollama(prompt, model="mistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

def analyze_missing_info(user_input, model="mistral"):
    """Analyse progressive : vérifie étape par étape"""
    text = user_input.lower()
    
    # Vérifications progressives
    has_age = any(word in text for word in ['ans', 'âge', 'age', 'années'])
    has_symptom_duration = any(word in text for word in ['depuis', 'jour', 'semaine', 'mois'])
    has_red_flags_mentioned = any(word in text for word in ['déficit', 'neurologique', 'fièvre', 'brutale', 'coup de tonnerre', 'pas de', 'sans', 'aucun'])
    has_symptom_type = any(word in text for word in ['céphalée', 'mal de tête', 'maux de tête', 'douleur'])
    
    # Critères pour avoir suffisamment d'informations
    # Il faut : âge + (signes d'alarme mentionnés OU durée)
    if has_age and has_red_flags_mentioned and has_symptom_duration:
        return "COMPLET"
    elif has_age and has_red_flags_mentioned:
        return "COMPLET"
    elif has_age and has_symptom_duration and len(text.split()) > 10:
        return "COMPLET"
    
    # Priorité des informations manquantes
    if not has_age:
        return "MANQUANT: âge"
    elif has_symptom_type and not has_red_flags_mentioned:
        return "MANQUANT: signes d'alarme"
    elif has_symptom_type and not has_symptom_duration:
        return "MANQUANT: durée"
    else:
        return "COMPLET"

def generate_clarifying_questions(missing_info, user_input):
    """Génère une question ciblée selon ce qui manque"""
    text = user_input.lower()
    
    # Questions progressives selon la priorité
    if 'âge' in missing_info.lower():
        return "Quel âge a le patient ?"
    elif 'signes d\'alarme' in missing_info.lower() or 'alarme' in missing_info.lower():
        return "Y a-t-il des signes d'alarme : céphalée brutale, déficit neurologique, fièvre ?"
    elif 'durée' in missing_info.lower():
        return "Depuis combien de temps ces symptômes évoluent-ils ?"
    elif any(word in text for word in ['céphalée', 'mal de tête', 'maux de tête']):
        return "Y a-t-il des signes d'alarme (céphalée brutale, déficit neurologique, fièvre) ?"
    else:
        return "Pouvez-vous préciser les signes cliniques ?"

def rag_query_interactive(user_input, collection):
    """Version interactive qui retourne aussi si plus d'infos sont nécessaires"""
    # Étape 1 : Analyser si des informations importantes manquent
    analysis = analyze_missing_info(user_input)
    
    # Vérifier si des informations manquent
    if "COMPLET" not in analysis.upper():
        # Extraire les informations manquantes
        if "MANQUANT:" in analysis:
            missing_info = analysis.split("MANQUANT:", 1)[1].strip()
        elif "MANQUANT " in analysis:
            missing_info = analysis.split("MANQUANT ", 1)[1].strip()
        else:
            missing_info = "informations cliniques"
            
        questions = generate_clarifying_questions(missing_info, user_input)
        
        return questions.strip(), True  # True = a besoin de plus d'infos
    
    # Étape 2 : Si les informations sont complètes, procéder à la requête RAG normale
    results = collection.query(
        query_texts=[user_input],
        n_results=3
    )

    docs = results["documents"][0]
    metas = results.get("metadatas", [[]])[0]  # safe fallback

    context = "\n".join(
        f"- {doc} (source: {meta.get('source', 'inconnue')}, motif: {meta.get('motif', 'inconnu')})"
        if isinstance(meta, dict) else f"- {doc}"
        for doc, meta in zip(docs, metas)
    )

    prompt = f"""
    Tu es un assistant médical expert en recommandations d'imagerie.
    
    Cas clinique complet : {user_input}
    
    Recommandations officielles pertinentes :
    {context}
    
    INSTRUCTIONS :
    1. Analyse le cas clinique en fonction des guidelines
    2. Fournis une recommandation claire et justifiée
    3. Indique l'examen d'imagerie approprié (ou absence d'indication)
    4. Mentionne les critères de décision utilisés
    5. Sois concis et pratique
    
    Format ta réponse de manière structurée et professionnelle.
    """

    response = query_ollama(prompt)
    return f"RECOMMANDATION D'IMAGERIE :\n\n{response}", False  # False = réponse complète

def rag_query(user_input, collection):
    """Version simple pour compatibilité"""
    response, _ = rag_query_interactive(user_input, collection)
    return response
