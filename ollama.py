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
    """Analyse la question pour identifier les informations manquantes importantes"""
    analysis_prompt = f"""
    Analyse cette question médicale et identifie les informations importantes qui pourraient manquer pour donner une recommandation d'imagerie appropriée.

    Question : {user_input}

    Évalue si ces informations essentielles sont présentes ou manquantes :
    - Âge du patient (important pour les céphalées >50 ans, contexte gériatrique)
    - Signes d'alarme ou "red flags" (céphalée brutale, déficit neurologique, fièvre, etc.)
    - Durée/évolution des symptômes
    - Antécédents médicaux pertinents (cancer, immunodépression, VIH)
    - Contexte (grossesse, post-partum, traumatisme)
    - Examen clinique (signes focaux, état de conscience)

    Réponds UNIQUEMENT par :
    - "COMPLET" si les informations essentielles sont présentes
    - "MANQUANT: [liste des informations importantes manquantes]" si des éléments cruciaux manquent

    Exemple : "MANQUANT: âge du patient, présence de signes d'alarme"
    """
    
    response = query_ollama(analysis_prompt, model)
    return response.strip()

def generate_clarifying_questions(missing_info, user_input):
    """Génère des questions de clarification basées sur les informations manquantes"""
    questions_prompt = f"""
    Génère 2-3 questions de clarification précises et médicalement pertinentes pour obtenir les informations manquantes suivantes : {missing_info}

    Question originale : {user_input}

    Format les questions de manière claire et directe, une par ligne, en commençant par "- ".
    Concentre-toi sur les éléments les plus critiques pour la décision d'imagerie.
    """
    
    return query_ollama(questions_prompt)

def rag_query_interactive(user_input, collection):
    """Version interactive qui retourne aussi si plus d'infos sont nécessaires"""
    # Étape 1 : Analyser si des informations importantes manquent
    analysis = analyze_missing_info(user_input)
    
    # Vérifier plusieurs formats possibles de réponse (robuste)
    if any(keyword in analysis.upper() for keyword in ["MANQUANT", "MANQUE", "MISSING", "INSUFFISANT"]):
        # Extraire les informations manquantes
        if "MANQUANT:" in analysis:
            missing_info = analysis.split("MANQUANT:", 1)[1].strip()
        elif "MANQUANT " in analysis:
            missing_info = analysis.split("MANQUANT ", 1)[1].strip()
        else:
            missing_info = analysis
            
        questions = generate_clarifying_questions(missing_info, user_input)
        
        response = f"""Pour vous donner une recommandation précise, j'aurais besoin de quelques informations supplémentaires :

{questions}

Ces détails m'aideront à appliquer les bonnes guidelines d'imagerie."""
        
        return response, True  # True = a besoin de plus d'infos
    
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


