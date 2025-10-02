import requests
import chromadb

def get_collection(db_path="rag_db", collection_name="imagerie"):
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_collection(collection_name)

# interroge biomistral a partir de ollama
def query_ollama(prompt, model="biomistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

# fonction qui permet de déterminer les informations manquantes
def analyze_missing_info(user_input, model="mistral"):
    """Analyse progressive spécifique par pathologie"""
    text = user_input.lower()
    
        # Identifier le type de pathologie (manque une)
    is_headache = any(word in text for word in ['céphalée', 'mal de tête', 'maux de tête', 'céphalées', 'migraine', 'céphalique'])
    is_abdominal = any(word in text for word in ['abdomen', 'ventre', 'abdominal', 'douleur abdominale', 'mal de ventre', 'maux de ventre', 'abdominale'])
    is_walking = any(word in text for word in ['marche', 'chute', 'trouble de la marche', 'équilibre', 'instabilité', 'troubles de la marche', 'chutes', 'démarche', 'mobilité'])
    
    # Identifier les symptômes neurologiques généraux
    is_neurological = any(word in text for word in ['parésthésie', 'parésthésies', 'engourdissement', 'fourmillement', 'picotement', 'déficit moteur', 'faiblesse', 'paralysie', 'hémiplégie', 'trouble sensitif'])
    
    # Déterminer la pathologie principale (priorité selon l'ordre de spécificité)
    main_pathology = None
    if is_walking:
        main_pathology = "walking"
    elif is_headache:
        main_pathology = "headache"  
    elif is_abdominal:
        main_pathology = "abdominal"
    elif is_neurological:
        main_pathology = "neurological"    # Vérifications générales
    has_age = any(word in text for word in ['ans', 'âge', 'age', 'années'])
    has_duration = any(word in text for word in ['depuis', 'jour', 'semaine', 'mois']) # probléme si c'est en année ça ne reconnait pas
    
    # CÉPHALÉES 
    if main_pathology == "headache":
        # Détecter les redflags présents OU explicitement absents
        headache_red_flags = any(word in text for word in [
            'brutale', 'coup de tonnerre', 'déficit', 'neurologique', 'fièvre', 
            'immunodépression', 'cancer', 'vih', 'grossesse', 'post-partum', 
            'changement', 'pattern'
        ])
        # Détecter les négations 
        has_negations = any(phrase in text for phrase in [
            'pas de', 'sans', 'aucun', 'absence de', 'non', 'négatif', "absence d' "
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
    
    # DOULEURS ABDOMINALES 
    elif main_pathology == "abdominal":
        # Signes abdominaux présents
        abdominal_signs = any(word in text for word in [
            'anévrisme', 'aorte', 'biliaire', 'vésicule', 
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
    
    # TROUBLES DE LA MARCHE 
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
    
    # SYMPTÔMES NEUROLOGIQUES 
    elif main_pathology == "neurological":
        # Signes neurologiques focaux ou systémiques
        neuro_signs = any(word in text for word in [
            'focal', 'focaux', 'déficit moteur', 'déficit sensitif', 'unilatéral', 
            'bilatéral', 'membre', 'face', 'depuis', 'brutal', 'progressif'
        ])
        # Négations pour signes neurologiques
        has_negations = any(phrase in text for phrase in [
            'pas de', 'sans', 'aucun', 'absence de', 'non', 'négatif'
        ])
        
        if not has_age:
            return "MANQUANT: âge"
        elif not neuro_signs and not has_negations and not has_duration:
            return "MANQUANT: caractéristiques neurologiques"
        else:
            return "COMPLET"
    
    # CAS GÉNÉRAL (pathologie non identifiée clairement)
    else:
        # Si on a au moins 5 mots et un âge, considérer comme suffisant
        if has_age and len(text.split()) >= 5:
            return "COMPLET"
        elif not has_age:
            return "MANQUANT: âge"
        else:
            return "MANQUANT: description clinique"

def generate_clarifying_questions(missing_info, user_input):
    """Génère une question ciblée selon la pathologie et ce qui manque"""
    text = user_input.lower()
    
    # Identifier le type de pathologie
    is_headache = any(word in text for word in ['céphalée', 'mal de tête', 'maux de tête', 'céphalées'])
    is_abdominal = any(word in text for word in ['abdomen', 'ventre', 'abdominal', 'douleur abdominale', 'mal de ventre', 'maux de ventre'])
    is_walking = any(word in text for word in ['marche', 'chute', 'trouble de la marche', 'équilibre'])
    is_neurological = any(word in text for word in ['parésthésie', 'parésthésies', 'engourdissement', 'fourmillement', 'déficit', 'neurologique'])
    
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
    
    # SYMPTÔMES NEUROLOGIQUES - Questions spécifiques
    elif 'caractéristiques neurologiques' in missing_info.lower():
        return "Les symptômes sont-ils focaux/unilatéraux, depuis quand, évolution brutale ou progressive ?"
    
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
    elif is_neurological:
        return "Les symptômes neurologiques sont-ils focaux, depuis quand évoluent-ils ?"
    else:
        return "Pouvez-vous préciser la localisation et l'évolution des symptômes ?"

def generate_imaging_recommendation(user_input, guidelines):
    """Génère une recommandation d'imagerie basée sur des règles simples"""
    text = user_input.lower()
    
    # Extraire l'âge
    age_numbers = [int(word) for word in user_input.split() if word.isdigit()]
    age = age_numbers[0] if age_numbers else 0
    
    # PRIORITÉ ABSOLUE : Signes d'alarme majeurs (même s'il y a des négations ailleurs)
    has_neuro_deficit = any(phrase in text for phrase in ['déficit neurologique', 'déficit neurologique', 'deficit neurologique']) and 'pas de déficit' not in text
    has_fever = 'fièvre' in text and 'pas de fièvre' not in text
    has_brutal = any(word in text for word in ['brutale', 'coup de tonnerre'])
    
    # Si signes d'alarme majeurs présents → IMAGERIE URGENTE
    if has_neuro_deficit or has_brutal or has_fever:
        return "IMAGERIE INDIQUÉE : Scanner cérébral - Signes d'alarme majeurs (déficit neurologique/céphalée brutale/fièvre)"
    
    # Négations explicites
    no_red_flags = any(phrase in text for phrase in [
        'pas de fièvre', 'pas de déficit', 'sans fièvre', 'sans déficit', 
        'aucun signe', 'pas de signe'
    ])
    
    # Détection des autres signes d'alarme
    other_red_flags = any(word in text for word in [
        'immunodépression', 'cancer', 'vih', 'grossesse', 'post-partum', 'changement'
    ])
    
    # CÉPHALÉES
    if any(word in text for word in ['céphalée', 'céphalées', 'mal de tête', 'maux de tête']):
        if other_red_flags:
            return "IMAGERIE INDIQUÉE : Scanner cérébral - Présence de signes d'alarme (immunodépression/cancer/grossesse)"
        elif age > 50:
            return "IMAGERIE INDIQUÉE : IRM cérébrale - Patient >50 ans selon guidelines HAS/SFETD"
        elif no_red_flags:
            return "AUCUNE IMAGERIE : Céphalée primaire sans signe d'alarme selon HAS/SFETD"
        else:
            return "IMAGERIE INDIQUÉE : IRM cérébrale - Évaluation nécessaire selon guidelines"
    
    # DOULEURS ABDOMINALES  
    elif any(word in text for word in ['abdomen', 'ventre', 'abdominal']):
        # Signes de gravité abdominale urgents (vérifier négations)
        has_defense = any(word in text for word in ['défense', 'defense', 'contracture', 'péritonéal']) and not any(phrase in text for phrase in ['pas de défense', 'sans défense', 'pas de contracture'])
        has_aaa_signs = any(word in text for word in ['anévrisme', 'aaa', 'aorte'])
        has_biliary_signs = any(word in text for word in ['biliaire', 'vésicule', 'cholécystite'])
        
        if has_defense:
            return "IMAGERIE INDIQUÉE : Scanner abdominal - Défense abdominale (suspicion péritonite)"
        elif has_aaa_signs:
            return "IMAGERIE INDIQUÉE : Échographie puis scanner si doute - Suspicion AAA selon HAS"
        elif has_biliary_signs:
            return "IMAGERIE INDIQUÉE : Échographie abdominale - Pathologie biliaire selon HAS"
        elif 'fièvre' in text:
            return "IMAGERIE INDIQUÉE : Scanner abdominal - Douleur abdominale fébrile"
        else:
            return "IMAGERIE INDIQUÉE : Échographie abdominale - Évaluation douleur abdominale"
    
    # TROUBLES DE LA MARCHE
    elif any(word in text for word in ['marche', 'chute', 'équilibre']):
        if any(word in text for word in ['focaux', 'signes focaux', 'lésion']):
            return "IMAGERIE INDIQUÉE : IRM selon signes focaux - Guidelines HAS troubles marche"
        else:
            return "AUCUNE IMAGERIE : Pas d'imagerie systématique pour troubles marche selon HAS"
    
    # CAS GÉNÉRAL
    else:
        return "ÉVALUATION CLINIQUE : Imagerie selon guidelines spécifiques à la pathologie"

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
    
    # Étape 2 : Générer une recommandation basée sur des règles simples
    results = collection.query(
        query_texts=[user_input],
        n_results=3
    )

    docs = results["documents"][0]
    metas = results.get("metadatas", [[]])[0]

    # Utiliser la logique déterministe au lieu d'Ollama
    recommendation = generate_imaging_recommendation(user_input, docs)
    
    return f"RECOMMANDATION D'IMAGERIE :\n\n{recommendation}", False  # False = réponse complète

def rag_query(user_input, collection):
    """Version simple pour compatibilité"""
    response, _ = rag_query_interactive(user_input, collection)
    return response
