import chromadb

def get_collection(db_path="rag_db", collection_name="imagerie"):
    """Récupère la collection ChromaDB"""
    chroma_client = chromadb.PersistentClient(path=db_path)
    return chroma_client.get_collection(collection_name)

def analyze_and_generate_questions(user_input):
    """Analyse les informations manquantes et génère directement les questions appropriées"""
    text = user_input.lower()
    
    # Vérifications critiques
    has_age = any(word in text for word in ['ans', 'âge', 'age', 'années'])
    
    # Si pas d'âge, c'est critique
    if not has_age:
        return "Quel âge a le patient ?"
    
    # Si le texte est très court (< 5 mots), demander plus de détails
    if len(text.split()) < 5:
        return "Pouvez-vous décrire plus précisément les symptômes, leur localisation et leur évolution ?"
    
    # Analyse contextuelle pour questions de clarification intelligentes
    
    # Céphalées : demander caractéristiques
    if 'céphalée' in text or 'mal de tête' in text:
        if not any(word in text for word in ['brutal', 'progressif', 'pulsatile', 'tension', 'vomissement', 'fièvre']):
            return "Pouvez-vous préciser les caractéristiques de ces céphalées ?\n- Sont-elles brutales (en coup de tonnerre) ou progressives ?\n- Y a-t-il des signes associés : fièvre, vomissements, troubles visuels, déficit neurologique ?"
    
    # Douleurs abdominales : localisation précise
    if 'abdominale' in text or 'ventre' in text:
        if not any(word in text for word in ['fid', 'fosse iliaque', 'épigastre', 'hypochondre', 'lombaire', 'sous-costale']):
            return "Pouvez-vous préciser la localisation de la douleur abdominale ?\n- Fosse iliaque droite (FID) ?\n- Épigastre, hypochondre droit, lombaire ?\n- Y a-t-il de la fièvre ou des signes associés ?"
    
    # Troubles neurologiques : préciser les signes
    if any(word in text for word in ['trouble', 'faiblesse', 'paralysie', 'engourdissement']):
        if not any(word in text for word in ['moteur', 'sensitif', 'marche', 'parole', 'vision', 'cognitif']):
            return "Pouvez-vous préciser les troubles neurologiques ?\n- Troubles moteurs (faiblesse, paralysie) ?\n- Troubles sensitifs (engourdissements, paresthésies) ?\n- Troubles de la marche, de l'équilibre, cognitifs ?"
    
    # Si tout semble complet, retourner None (pas de questions)
    return None

def enhance_medical_query(user_input):
    """Enrichit la requête utilisateur avec des synonymes médicaux pour améliorer le matching RAG"""
    text = user_input.lower()
    enhanced = user_input
    
    # NORMALISATION DU GENRE : patient -> homme, patiente -> femme
    if 'patient ' in text and 'patiente' not in text:
        enhanced = enhanced.replace('patient ', 'homme ')
        enhanced = enhanced.replace('Patient ', 'Homme ')
    elif 'patiente' in text:
        enhanced = enhanced.replace('patiente', 'femme')
        enhanced = enhanced.replace('Patiente', 'Femme')
    
    # Synonymes médicaux essentiels
    medical_synonyms = {
        # CÉPHALÉES & NEUROLOGIE
        'céphalées': ' mal de tête douleur crânienne migraine',
        'coup de tonnerre': ' céphalée brutale hémorragie méningée scanner urgent',
        'déficit moteur': ' paralysie faiblesse AVC hémiplégie scanner cérébral urgent',
        'vomissements matinaux': ' HTIC enfant hypertension intracrânienne IRM cérébrale urgente',
        'troubles visuels': ' vision floue diplopie sclérose plaques SEP IRM cérébrale',
        'photophobie': ' peur lumière méningite scanner cérébral urgent',
        'raideur de nuque': ' raideur nucale méningite scanner urgence',
        
        # ABDOMEN & DIGESTIF
        'fosse iliaque droite': ' FID appendicite McBurney échographie scanner abdominal',
        'fid': ' fosse iliaque droite appendicite échographie scanner abdominal',
        'appendicite': ' FID fosse iliaque droite McBurney fièvre échographie scanner',
        'douleur abdominale': ' mal ventre FID épigastre échographie scanner',
        'hématurie': ' sang urines lithiase calcul rénal colique néphrétique scanner',
        'colique néphrétique': ' douleur lombaire lithiase calcul rénal hématurie scanner abdomino-pelvien',
        'lombaire brutale': ' colique néphrétique calcul rénal lithiase scanner urgence',
        
        # MARCHE & MOTRICITÉ
        'troubles de la marche': ' démarche instable ataxie SEP sclérose plaques IRM',
        'marche instable': ' ataxie déséquilibre sclérose plaques SEP IRM cérébrale médullaire',
        'paresthésies': ' fourmillements engourdissements SEP sclérose plaques IRM',
        'troubles sensitifs': ' engourdissements fourmillements paresthésies SEP IRM',
        
        # PÉDIATRIE
        'enfant': ' pédiatrique nourrisson bébé',
        'vomissements enfant': ' HTIC pression intracrânienne IRM cérébrale urgente pédiatrie',
        'céphalées enfant': ' mal tête HTIC pression intracrânienne IRM urgente',
        
        # EXCLUSIONS MÉDICALES
        'femme enceinte': ' grossesse contre-indication scanner IRM échographie',
        'grossesse': ' femme enceinte contre-indication scanner IRM échographie',
        'claustrophobie': ' angoisse IRM contre-indication scanner alternative',
        'insuffisance rénale': ' contre-indication produit contraste créatinine scanner',
        'allergie iode': ' contre-indication produit contraste scanner IRM alternative',
    }
    
    # Application des synonymes
    for term, synonyms in medical_synonyms.items():
        if term in text:
            enhanced += synonyms
    
    return enhanced

def calculate_contextual_score(user_input, guideline_text, metadata, vector_distance):
    """Calcule un score contextuel intelligent combinant distance vectorielle et facteurs cliniques"""
    text = user_input.lower()
    guideline = guideline_text.lower()
    
    # Score de base inversement proportionnel à la distance
    base_score = max(0, 1.0 - vector_distance)
    
    # Facteurs de bonification/pénalisation
    score_multiplier = 1.0
    
    # FACTEURS D'URGENCE (bonification majeure)
    urgency_keywords = ['brutal', 'aigu', 'soudain', 'coup de tonnerre', 'hémorragie', 'AVC', 'coma']
    if any(keyword in text for keyword in urgency_keywords):
        if 'urgent' in guideline or 'scanner' in guideline:
            score_multiplier *= 2.0  # Bonification majeure pour urgences
    
    # FACTEURS PÉDIATRIQUES (bonification)
    if any(age in text for age in ['enfant', 'ans', 'années']):
        age_match = False
        for word in text.split():
            if word.isdigit() and int(word) <= 18:
                age_match = True
                break
        if age_match and 'enfant' in guideline:
            score_multiplier *= 1.5
    
    # EXCLUSIONS CRITIQUES (pénalisation majeure)
    exclusions = {
        'grossesse': ['femme enceinte', 'grossesse', 'enceinte'],
        'claustrophobie': ['claustrophobie', 'angoisse', 'peur'],
        'insuffisance_renale': ['insuffisance rénale', 'créatinine', 'dialyse']
    }
    
    for exclusion_type, keywords in exclusions.items():
        if any(keyword in text for keyword in keywords):
            if any(contra in guideline for contra in ['contre-indication', 'éviter', 'alternative']):
                score_multiplier *= 1.8  # Bonification pour gestion des contre-indications
            elif 'scanner' in guideline and exclusion_type in ['grossesse', 'insuffisance_renale']:
                score_multiplier *= 0.3  # Pénalisation pour recommandations inappropriées
    
    # CORRESPONDANCE ANATOMIQUE (bonification forte)
    anatomical_matches = {
        'céphalée': ['cérébral', 'crâne', 'tête', 'neurologique'],
        'abdomen': ['abdominal', 'ventre', 'digestif', 'FID'],
        'lombaire': ['dos', 'rachis', 'colonne', 'vertébral'],
        'thorax': ['poumon', 'cardiaque', 'thoracique', 'respiratoire']
    }
    
    for symptom, anatomy_terms in anatomical_matches.items():
        if symptom in text:
            if any(term in guideline for term in anatomy_terms):
                score_multiplier *= 1.4
    
    # FACTEURS TEMPORELS
    temporal_keywords = ['chronique', 'persistant', 'récurrent', '6 semaines']
    if any(keyword in text for keyword in temporal_keywords):
        if any(temp in guideline for temp in ['chronique', 'persistant', '6 semaines']):
            score_multiplier *= 1.3
    
    # Score final
    final_score = base_score * score_multiplier
    
    # Normalisation entre 0 et 1
    return min(final_score, 1.0)

def classify_recommendation_by_score(guideline_text, metadata, user_input, contextual_score):
    """Classification intelligente basée sur le score contextuel et les mots-clés"""
    text = user_input.lower()
    guideline = guideline_text.lower()
    
    # Classification par score ET mots-clés
    if contextual_score >= 0.8:
        # Score très élevé = forte correspondance
        if any(urgent in guideline for urgent in ['urgent', 'immédiat', 'sans délai']):
            return "URGENTE"
        else:
            return "INDIQUÉE"
    
    elif contextual_score >= 0.5:
        # Score moyen = indication possible
        return "INDIQUÉE"
    
    elif contextual_score >= 0.3:
        # Score faible = évaluation nécessaire
        return "ÉVALUATION"
    
    else:
        # Score très faible = pas d'indication claire
        if any(exclusion in guideline for exclusion in ['pas d\'imagerie', 'aucune indication', 'contre-indication']):
            return "AUCUNE"
        else:
            return "AUTRE"

def adapt_guideline_to_context(guideline_text, user_input):
    """Adapte la guideline au contexte spécifique du patient"""
    text = user_input.lower()
    adapted = guideline_text
    
    # Ajout d'informations contextuelles pertinentes
    if 'enfant' in text or any(word in text for word in ['ans']) and any(str(i) + ' ans' in text for i in range(0, 18)):
        if 'pédiatrique' not in adapted:
            adapted += " (Contexte pédiatrique : attention aux doses de rayonnement)"
    
    if 'femme' in text and ('enceinte' in text or 'grossesse' in text):
        if 'grossesse' not in adapted:
            adapted += " (Grossesse : privilégier l'échographie, éviter les rayonnements)"
    
    if 'urgent' in text or 'aigu' in text:
        if 'urgent' not in adapted:
            adapted += " (Contexte d'urgence : prioriser l'imagerie rapide)"
    
    return adapted

def should_ask_clarification(user_input, is_first_interaction=True):
    """Détermine si des questions de clarification sont nécessaires"""
    if not is_first_interaction:
        return False  # Pas de questions supplémentaires si ce n'est pas la première interaction
    
    text = user_input.lower()
    
    # Si l'entrée est très courte ou vague
    if len(text.split()) < 6:
        return True
    
    # Si des informations critiques manquent pour certains symptômes
    if 'céphalée' in text or 'mal de tête' in text:
        if not any(word in text for word in ['brutal', 'progressif', 'chronique', 'fièvre', 'vomissement']):
            return True
    
    if 'douleur' in text and 'abdomen' in text:
        if not any(word in text for word in ['fid', 'épigastre', 'hypochondre', 'fièvre']):
            return True
    
    return False

def generate_imaging_recommendation_rag(user_input, collection):
    """Génère une recommandation basée sur sélection intelligente avec scoring contextuel"""
    
    # Utilisation de query avec scoring contextuel intelligent
    user_query = enhance_medical_query(user_input)
    
    # Récupération des guidelines avec scoring contextuel
    results = collection.query(
        query_texts=[user_query],
        n_results=5,
        include=['documents', 'metadatas', 'distances']
    )
    
    if not results['documents'][0]:
        return "ÉVALUATION CLINIQUE : Aucune guideline trouvée - Consultation spécialisée recommandée"
    
    # Calcul des scores contextuels pour chaque résultat
    scored_results = []
    for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        contextual_score = calculate_contextual_score(user_input, doc, meta, dist)
        scored_results.append((contextual_score, doc, meta, dist))
    
    # Tri par score contextuel (descendant)
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    # Sélection de la meilleure guideline selon le score contextuel
    best_score, best_doc, best_meta, best_dist = scored_results[0]
    
    # Classification de la recommandation
    recommendation_type = classify_recommendation_by_score(best_doc, best_meta, user_input, best_score)
    
    # Adaptation contextuelle
    adapted_guideline = adapt_guideline_to_context(best_doc, user_input)
    
    # Construction de la réponse finale
    return f"{recommendation_type} : {adapted_guideline}"

def rag_query_interactive(user_input, collection, is_first_interaction=True):
    """Version interactive qui pose des questions de clarification naturelles"""
    
    # Étape 1 : Vérifier les informations critiques manquantes
    critical_question = analyze_and_generate_questions(user_input)
    if critical_question:
        return critical_question, True  # True = a besoin de plus d'infos
    
    # Étape 2 : Questions de clarification générale pour première interaction
    if should_ask_clarification(user_input, is_first_interaction):
        return generate_contextual_follow_up_question(user_input), True
    
    # Étape 3 : Génération de la recommandation finale
    recommendation = generate_imaging_recommendation_rag(user_input, collection)
    return f"RECOMMANDATION D'IMAGERIE :\n\n{recommendation}", False  # False = réponse complète

def generate_contextual_follow_up_question(user_input):
    """Génère une question de suivi contextuelle pour affiner le diagnostic"""
    text = user_input.lower()
    
    # Questions contextuelles selon le domaine
    if any(word in text for word in ['céphalée', 'mal de tête', 'crâne']):
        return "Pour mieux vous orienter, pouvez-vous préciser :\n- Ces céphalées sont-elles brutales (en coup de tonnerre) ou progressives ?\n- Y a-t-il des signes associés : fièvre, vomissements, troubles de la vision, déficit neurologique ?"
    
    elif any(word in text for word in ['abdomen', 'ventre', 'douleur', 'mal']):
        return "Pour préciser l'indication d'imagerie, pouvez-vous me dire :\n- Où se situe exactement la douleur (fosse iliaque droite, épigastre, etc.) ?\n- Y a-t-il de la fièvre, des nausées, des vomissements ?"
    
    elif any(word in text for word in ['trouble', 'faiblesse', 'neurologique']):
        return "Pour orienter l'imagerie neurologique :\n- S'agit-il de troubles moteurs (faiblesse, paralysie) ou sensitifs (engourdissements) ?\n- Y a-t-il des troubles de la marche, de l'équilibre, de la mémoire ?"
    
    else:
        return "Pouvez-vous me donner quelques précisions supplémentaires sur :\n- L'évolution des symptômes (brutal, progressif) ?\n- Les signes associées (fièvre, nausées, troubles neurologiques) ?\n- Le contexte (antécédents, traitements en cours) ?"
