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
    """Analyse le texte pour déterminer quelles informations manquantes"""
    text = user_input.lower()
    
        # Identifier le type de pathologie (manque une)
    is_headache = any(word in text for word in ['céphalée', 'mal de tête', 'maux de tête', 'céphalées', 'migraine', 'céphalique'])
    is_abdominal = any(word in text for word in ['abdomen', 'ventre', 'abdominal', 'douleur abdominale', 'mal de ventre', 'maux de ventre', 'abdominale'])
    is_walking = any(word in text for word in ['marche', 'chute', 'trouble de la marche', 'équilibre', 'instabilité', 'troubles de la marche', 'chutes', 'démarche', 'mobilité'])
    
    # Identifier les troubles thoraciques
    is_thoracic = any(word in text for word in ['thorax', 'thoracique', 'chest', 'poitrine', 'douleur thoracique', 'oppression', 'dyspnée', 'essoufflement', 'toux'])
    
    # Déterminer la pathologie principale (priorité selon l'ordre de spécificité)
    main_pathology = None
    if is_walking:
        main_pathology = "walking"
    elif is_headache:
        main_pathology = "headache"  
    elif is_abdominal:
        main_pathology = "abdominal"
    elif is_thoracic:
        main_pathology = "thoracic"    # Vérifications générales
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
        
        # Détecter signes neurologiques spécifiques qui nécessitent une évaluation complète
        has_specific_neuro = any(phrase in text for phrase in [
            'vision double', 'diplopie', 'troubles visuels', 'déficit moteur', 'paralysie'
        ])
        
        if not has_age:
            return "MANQUANT: âge"
        elif not headache_red_flags and not has_negations:
            return "MANQUANT: signes d'alarme céphalées"
        elif headache_red_flags and has_specific_neuro:
            # Si on a à la fois des signes d'alarme ET des signes neuro spécifiques = COMPLET
            return "COMPLET"
        elif headache_red_flags and not has_specific_neuro and not has_negations:
            # CAS SPÉCIAL : Si fièvre seule (méningite simple), c'est suffisant
            if 'fièvre' in text and not any(word in text for word in ['brutale', 'coup de tonnerre']):
                return "COMPLET"  # Méningite simple = fièvre + céphalées suffit
            # Sinon, chercher des signes neuro spécifiques
            return "MANQUANT: signes neurologiques spécifiques"
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
        
        # Détecter les signes d'urgence abdominale qui ne nécessitent pas de durée
        urgent_abdominal = any(word in text for word in [
            'défense', 'contracture', 'anévrisme', 'aorte', 'aaa', 'biliaire', 'vésicule'
        ])
        
        if not has_age:
            return "MANQUANT: âge"
        elif not abdominal_signs and not has_negations:
            return "MANQUANT: signes cliniques abdominaux"
        elif urgent_abdominal:
            return "COMPLET"  # Cas urgents abdominaux = pas besoin de durée
        elif not has_duration:
            return "MANQUANT: durée"
        else:
            return "COMPLET"
    
    # TROUBLES DE LA MARCHE 
    elif main_pathology == "walking":
        # Signes de marche présents (y compris signes neurologiques)
        walking_signs = any(word in text for word in [
            'timed up', 'go', 'secondes', 'focaux', 'signes focaux', 
            'lésion', 'traumatisme', 'chutes répétées', 'hémiparésie', 'hemiparesie',
            'paralysie', 'déficit', 'neurologique', 'cognitif', 'cognitifs', 
            'sphinctérien', 'sphinctériens', 'irradiant', 'irradiation', 'jambe', 'jambes',
            'fièvre', 'hanche', 'genou', 'brutal', 'brutale', 'examen normal', 'neurologique normal'
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
    
    # SYMPTÔMES THORACIQUES 
    elif main_pathology == "thoracic":
        # Signes thoraciques spécifiques
        thoracic_signs = any(word in text for word in [
            'dyspnée', 'oppression', 'serrement', 'irradiation', 'épaule', 
            'bras', 'mâchoire', 'effort', 'repos', 'depuis', 'brutal', 'progressif'
        ])
        # Négations pour signes thoraciques
        has_negations = any(phrase in text for phrase in [
            'pas de', 'sans', 'aucun', 'absence de', 'non', 'négatif'
        ])
        
        if not has_age:
            return "MANQUANT: âge"
        elif not thoracic_signs and not has_negations and not has_duration:
            return "MANQUANT: caractéristiques thoraciques"
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
    is_thoracic = any(word in text for word in ['thorax', 'thoracique', 'poitrine', 'douleur thoracique', 'oppression', 'dyspnée', 'essoufflement', 'toux'])
    
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
    
    # SYMPTÔMES THORACIQUES - Questions spécifiques
    elif 'caractéristiques thoraciques' in missing_info.lower():
        return "Y a-t-il dyspnée, oppression, irradiation vers l'épaule/bras/mâchoire, déclenchement à l'effort ?"
    
    # SIGNES NEUROLOGIQUES SPÉCIFIQUES - Questions spécifiques
    elif 'signes neurologiques spécifiques' in missing_info.lower():
        return "Y a-t-il des signes neurologiques spécifiques : vision double, déficit moteur, troubles de la parole, paralysie ?"
    
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
    elif is_thoracic:
        return "Les symptômes thoraciques sont-ils accompagnés de dyspnée, oppression, ou irradiation ?"
    else:
        return "Pouvez-vous préciser la localisation et l'évolution des symptômes ?"

def generate_imaging_recommendation_rag(user_input, guidelines):
    """Génère une recommandation basée sur la recherche RAG avec fallback simple"""
    
    # Recherche dans les guidelines via RAG
    best_guideline = None
    best_score = 0
    
    # Analyser les guidelines récupérées pour trouver la plus pertinente
    for guideline in guidelines:
        score = calculate_relevance_score(user_input.lower(), guideline.lower())
        if score > best_score:
            best_score = score
            best_guideline = guideline
    
    # PRIORITE AU RAG - Si on trouve une guideline très pertinente (score > 8), l'utiliser
    if best_score > 8 and best_guideline:
        return f"RECOMMANDATION (RAG) : {extract_recommendation_from_guideline(best_guideline)}"
    
    # Fallback seulement pour les cas vraiment urgents sans correspondance RAG
    text = user_input.lower()
    
    # CAS URGENTS - Logique de sécurité minimale (seuil plus élevé)
    if any(phrase in text for phrase in ['hémiparésie', 'hemiparesie', 'déficit neurologique']) and 'marche' in text:
        return "IMAGERIE URGENTE : Scanner cérébral - Suspicion AVC"
    elif 'céphalée' in text and 'brutale' in text and best_score == 0:
        return "IMAGERIE URGENTE : Scanner cérébral - Céphalée brutale"
    elif ('céphalée' in text or 'céphalées' in text) and 'fièvre' in text and 'vision double' not in text and best_score < 10:
        return "PONCTION LOMBAIRE INDIQUÉE : Céphalées + fièvre = suspicion méningite (fallback de sécurité)"
    elif 'défense' in text and 'abdomen' in text and best_score == 0:
        return "IMAGERIE URGENTE : Scanner abdominal - Suspicion péritonite"
    
    # Si on a une guideline même avec un score faible, l'utiliser
    if best_guideline:
        return f"RECOMMANDATION (RAG) : {extract_recommendation_from_guideline(best_guideline)}"
    
    # Dernier recours
    return "ÉVALUATION CLINIQUE : Consultation spécialisée recommandée - Cas complexe"

def calculate_relevance_score(user_text, guideline_text):
    """Calcule un score de pertinence avancé entre le texte utilisateur et une guideline"""
    # Normaliser les textes pour une meilleure comparaison
    user_text_clean = user_text.lower().replace('\n', ' ').replace('|', ' ')
    guideline_text_clean = guideline_text.lower()
    

    
    user_words = set(user_text_clean.split())
    guideline_words = set(guideline_text_clean.split())
    
    score = 0
    
    # PATTERNS SPÉCIFIQUES - Très haute priorité (scores élevés)
    
    # === CÉPHALÉES COMPLEXES ===
    has_headache = any(word in user_text_clean for word in ['céphalée', 'céphalées'])
    has_fever = 'fièvre' in user_text_clean and 'pas de fièvre' not in user_text_clean
    has_visual_signs = any(phrase in user_text_clean for phrase in ['vision double', 'diplopie', 'troubles visuels'])
    has_brutal = any(word in user_text_clean for word in ['brutal', 'brutale', 'coup de tonnerre'])
    has_no_fever = 'pas de fièvre' in user_text_clean
    is_chronic = any(word in user_text_clean for word in ['chronique', 'depuis', 'mois', 'quotidienne'])
    has_no_neuro = any(phrase in user_text_clean for phrase in ['sans signe neurologique', 'examen neurologique normal'])
    
    if has_headache:
        # Thrombose veineuse : céphalées + fièvre + vision double
        if has_fever and has_visual_signs and 'thrombose' in guideline_text_clean:
            score += 15
        # Hémorragie méningée : céphalées brutales + pas de fièvre
        elif has_brutal and has_no_fever and 'hémorragie méningée' in guideline_text_clean:
            score += 15
        # Hémorragie méningée : céphalées brutales (sans mention fièvre)
        elif has_brutal and not has_fever and 'hémorragie' in guideline_text_clean:
            score += 12
        # Méningite adulte : céphalées + fièvre + pas enfant
        elif has_fever and not has_visual_signs and 'adulte' in guideline_text_clean and 'méningite' in guideline_text_clean:
            # Vérifier que ce n'est pas un enfant
            age_numbers = [int(word) for word in user_text_clean.split() if word.isdigit()]
            if age_numbers and age_numbers[0] >= 18:
                score += 15
        # Méningite enfant : céphalées + fièvre + enfant
        elif has_fever and not has_visual_signs and 'enfant' in guideline_text_clean and 'méningite' in guideline_text_clean:
            # Vérifier que c'est bien un enfant ou pas d'âge spécifié
            age_numbers = [int(word) for word in user_text_clean.split() if word.isdigit()]
            if not age_numbers or (age_numbers and age_numbers[0] < 18):
                score += 15
        # Méningite générale : céphalées + fièvre (sans vision double)
        elif has_fever and not has_visual_signs and 'méningite' in guideline_text_clean and 'suspicion méningite' in guideline_text_clean:
            score += 10
        # Céphalées chroniques sans signe d'alarme
        elif is_chronic and has_no_neuro and 'pas d\'imagerie' in guideline_text_clean and 'chronique' in guideline_text_clean:
            score += 12
    
    # === TROUBLES DE LA MARCHE ===
    has_walking_trouble = any(phrase in user_text_clean for phrase in ['trouble de la marche', 'trouble marche'])
    has_hemiparesis = any(word in user_text_clean for word in ['hémiparésie', 'hemiparesie'])
    has_cognitive = any(word in user_text_clean for word in ['cognitif', 'cognitifs'])
    has_sphincter = any(word in user_text_clean for word in ['sphinctérien', 'sphinctériens'])
    has_leg_pain = any(word in user_text_clean for word in ['jambe', 'jambes', 'irradiation'])
    has_child = 'enfant' in user_text_clean
    has_hip_pain = 'hanche' in user_text_clean
    
    if has_walking_trouble:
        # AVC : trouble marche + hémiparésie
        if has_hemiparesis and any(word in guideline_text_clean for word in ['avc', 'hémiparésie']):
            score += 15
        # Triade HPN : trouble marche + cognitif + sphinctérien
        elif has_cognitive and has_sphincter and 'hydrocéphalie' in guideline_text_clean:
            score += 15
        # Canal lombaire : trouble marche + douleurs jambes
        elif has_leg_pain and 'canal lombaire' in guideline_text_clean:
            score += 12
        # Arthrite septique enfant : enfant + fièvre + hanche
        elif has_child and has_fever and has_hip_pain and 'arthrite septique' in guideline_text_clean:
            score += 15
        # Pas d'imagerie si examen normal
        elif has_no_neuro and 'pas d\'imagerie' in guideline_text_clean:
            score += 10
    
    # === PATHOLOGIES THORACIQUES ===
    has_chest_pain = any(phrase in user_text_clean for phrase in ['douleur thoracique', 'thoracique'])
    has_dyspnea = any(word in user_text_clean for word in ['dyspnée', 'essoufflement'])
    has_radiation = any(word in user_text_clean for word in ['irradiation', 'épaule', 'bras'])
    
    if has_chest_pain:
        if has_dyspnea and 'embolie' in guideline_text_clean:
            score += 12
        elif has_radiation and 'coronaire' in guideline_text_clean:
            score += 12
    
    # === PATHOLOGIES ABDOMINALES ===
    has_abdominal = any(word in user_text_clean for word in ['abdomen', 'abdominal', 'douleur abdominale', 'ventre', 'maux de ventre', 'mal de ventre', 'abdominale'])
    has_defense = 'défense' in user_text_clean
    has_aaa_signs = any(word in user_text_clean for word in ['anévrisme', 'aorte', 'aaa'])
    has_biliary_signs = any(word in user_text_clean for word in ['biliaire', 'vésicule', 'cholécystite'])
    has_appendicitis = 'appendicite' in user_text_clean
    

    
    if has_abdominal:
        # Défense abdominale = péritonite
        if has_defense and 'péritonite' in guideline_text_clean:
            score += 15
        # AAA spécifique
        elif has_aaa_signs and any(word in guideline_text_clean for word in ['aaa', 'anévrisme', 'aorte']):
            score += 15
        # Pathologie biliaire spécifique
        elif has_biliary_signs and 'biliaire' in guideline_text_clean:
            score += 15
        # Appendicite spécifique
        elif has_appendicitis and 'appendicite' in guideline_text_clean:
            score += 15
        # Douleur abdominale + fièvre
        elif has_fever and 'fièvre' in guideline_text_clean and has_abdominal:
            score += 12
    
    # SCORE BASÉ SUR LES MOTS COMMUNS (priorité moindre)
    common_words = user_words.intersection(guideline_words)
    score += len(common_words) * 0.3
    
    # BONUS pour correspondances exactes d'âge
    age_match = False
    if 'enfant' in user_text_clean and 'enfant' in guideline_text_clean:
        score += 2
        age_match = True
    elif any(word in user_text_clean for word in ['75', '68', '70', '80']) and 'personne âgée' in guideline_text_clean:
        score += 2
        age_match = True
    elif any(word in user_text_clean for word in ['20', '25', '30', '35']) and 'jeune' in guideline_text_clean:
        score += 2
        age_match = True
    
    # PÉNALITÉS pour éviter les faux positifs
    if has_fever and 'pas de fièvre' in guideline_text_clean:
        score -= 8
    if has_no_fever and 'fièvre' in guideline_text_clean and 'méningite' in guideline_text_clean:
        score -= 8
    
    return max(0, score)  # Score minimum de 0

def extract_recommendation_from_guideline(guideline_text):
    """Extrait la recommandation principale d'une guideline"""
    # Rechercher les patterns de recommandation
    if 'pas d\'imagerie' in guideline_text.lower() or 'aucune imagerie' in guideline_text.lower():
        return "AUCUNE IMAGERIE : " + guideline_text
    elif 'scanner' in guideline_text.lower() and 'urgence' in guideline_text.lower():
        return "IMAGERIE URGENTE : " + guideline_text
    elif 'ponction lombaire' in guideline_text.lower():
        return "PONCTION LOMBAIRE : " + guideline_text
    elif 'irm' in guideline_text.lower():
        return "IMAGERIE INDIQUÉE : " + guideline_text
    elif 'scanner' in guideline_text.lower():
        return "IMAGERIE INDIQUÉE : " + guideline_text
    elif 'échographie' in guideline_text.lower():
        return "IMAGERIE INDIQUÉE : " + guideline_text
    else:
        return "ÉVALUATION CLINIQUE : " + guideline_text

# Garder l'ancienne fonction comme fallback
def generate_imaging_recommendation(user_input, guidelines):
    """Version hybride qui utilise d'abord RAG puis fallback"""
    return generate_imaging_recommendation_rag(user_input, guidelines)

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
        n_results=10  # Augmenter pour récupérer plus de guidelines
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
