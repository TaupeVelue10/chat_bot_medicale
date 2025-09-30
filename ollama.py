import requests
import chromadb

def get_collection(db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_collection(collection_name)

def query_ollama(prompt, model="biomistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

def analyze_missing_info(user_input, model="mistral"):
    """Analyse progressive spécifique par pathologie"""
    text = user_input.lower()
    
    # Identifier le type de pathologie (recherche étendue pour capturer toutes les mentions)
    is_headache = any(word in text for word in ['céphalée', 'mal de tête', 'maux de tête', 'céphalées', 'migraine', 'céphalique'])
    is_abdominal = any(word in text for word in ['abdomen', 'ventre', 'abdominal', 'douleur abdominale', 'mal de ventre', 'maux de ventre', 'abdominale'])
    is_walking = any(word in text for word in ['marche', 'chute', 'trouble de la marche', 'équilibre', 'instabilité', 'troubles de la marche', 'chutes', 'démarche', 'mobilité'])
    
    # Déterminer la pathologie principale (priorité selon l'ordre de spécificité)
    main_pathology = None
    if is_walking:
        main_pathology = "walking"
    elif is_headache:
        main_pathology = "headache"  
    elif is_abdominal:
        main_pathology = "abdominal"
    
    # Vérifications générales
    has_age = any(word in text for word in ['ans', 'âge', 'age', 'années'])
    has_duration = any(word in text for word in ['depuis', 'jour', 'semaine', 'mois'])
    
    # CÉPHALÉES - Informations critiques spécifiques
    if main_pathology == "headache":
        # Détecter les signes d'alarme présents OU explicitement absents
        headache_red_flags = any(word in text for word in [
            'brutale', 'coup de tonnerre', 'déficit', 'neurologique', 'fièvre', 
            'immunodépression', 'cancer', 'vih', 'grossesse', 'post-partum', 
            'changement', 'pattern'
        ])
        # Détecter les négations (informations données mais négatives)
        has_negations = any(phrase in text for phrase in [
            'pas de', 'sans', 'aucun', 'absence de', 'non', 'négatif'
        ])
        
        # Détecter âge >50 ans (critère important pour céphalées)
        age_numbers = [word for word in text.split() if word.isdigit()]
        age_over_50 = any(int(num) >= 50 for num in age_numbers if num.isdigit())
        
        if not has_age:
            return "MANQUANT: âge"
        elif not headache_red_flags and not has_negations:
            return "MANQUANT: signes d'alarme céphalées"
        elif age_over_50 and not has_duration:
            return "MANQUANT: durée"
        else:
            return "COMPLET"
    
    # DOULEURS ABDOMINALES - Informations critiques spécifiques
    elif main_pathology == "abdominal":
        # Signes abdominaux présents
        abdominal_signs = any(word in text for word in [
            'anévrisme', 'aaa', 'aorte', 'biliaire', 'vésicule', 
            'fièvre', 'défense', 'contracture', 'signes péritonéaux'
        ])
        # Négations pour signes abdominaux
        has_negations = any(phrase in text for phrase in [
            'pas de', 'sans', 'aucun', 'absence de', 'non', 'négatif'
        ])
        
        if not has_age:
            return "MANQUANT: âge"
        elif not abdominal_signs and not has_negations:
            return "MANQUANT: signes cliniques abdominaux"
        elif not has_duration:
            return "MANQUANT: durée"
        else:
            return "COMPLET"
    
    # TROUBLES DE LA MARCHE - Informations critiques spécifiques
    elif main_pathology == "walking":
        # Signes de marche présents
        walking_signs = any(word in text for word in [
            'timed up', 'go', 'secondes', 'focaux', 'signes focaux', 
            'lésion', 'traumatisme', 'chutes répétées'
        ])
        # Négations pour troubles de marche
        has_negations = any(phrase in text for phrase in [
            'pas de', 'sans', 'aucun', 'absence de', 'non', 'négatif'
        ])
        
        if not has_age:
            return "MANQUANT: âge"
        elif not walking_signs and not has_negations:
            return "MANQUANT: évaluation fonctionnelle"
        else:
            return "COMPLET"
    
    # CAS GÉNÉRAL (pathologie non identifiée clairement)
    else:
        # Signes généraux présents
        general_signs = any(word in text for word in [
            'déficit', 'neurologique', 'fièvre', 'brutale', 'signes focaux'
        ])
        # Négations générales
        has_negations = any(phrase in text for phrase in [
            'pas de', 'sans', 'aucun', 'absence de', 'non', 'négatif'
        ])
        
        if not has_age:
            return "MANQUANT: âge"
        elif not general_signs and not has_negations:
            return "MANQUANT: signes cliniques"
        else:
            return "COMPLET"

def generate_clarifying_questions(missing_info, user_input):
    """Génère une question ciblée selon la pathologie et ce qui manque"""
    text = user_input.lower()
    
    # Identifier le type de pathologie
    is_headache = any(word in text for word in ['céphalée', 'mal de tête', 'maux de tête', 'céphalées'])
    is_abdominal = any(word in text for word in ['abdomen', 'ventre', 'abdominal', 'douleur abdominale', 'mal de ventre', 'maux de ventre'])
    is_walking = any(word in text for word in ['marche', 'chute', 'trouble de la marche', 'équilibre'])
    
    # Questions selon ce qui manque
    if 'âge' in missing_info.lower():
        return "Quel âge a le patient ?"
    
    # CÉPHALÉES - Questions spécifiques
    elif 'signes d\'alarme céphalées' in missing_info.lower():
        return "Y a-t-il des signes d'alarme : céphalée brutale en coup de tonnerre, déficit neurologique, fièvre, immunodépression, cancer ?"
    
    # DOULEURS ABDOMINALES - Questions spécifiques  
    elif 'signes cliniques abdominaux' in missing_info.lower():
        return "Y a-t-il des signes de gravité : suspicion d'anévrisme aorte abdominale, signes biliaires, défense abdominale ?"
    
    # TROUBLES DE LA MARCHE - Questions spécifiques
    elif 'évaluation fonctionnelle' in missing_info.lower():
        return "Y a-t-il des signes focaux, un test Timed Up & Go >20 secondes, ou des chutes répétées ?"
    
    # Questions génériques selon durée
    elif 'durée' in missing_info.lower():
        if is_headache:
            return "Depuis combien de temps ces céphalées évoluent-elles ?"
        elif is_abdominal:
            return "Depuis combien de temps ces douleurs abdominales évoluent-elles ?"
        else:
            return "Depuis combien de temps ces symptômes évoluent-ils ?"
    
    # Questions génériques selon pathologie
    elif is_headache:
        return "Y a-t-il des signes d'alarme neurologiques ?"
    elif is_abdominal:
        return "Y a-t-il des signes de gravité abdominale ?"
    elif is_walking:
        return "Y a-t-il des signes focaux ou troubles de l'équilibre ?"
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
