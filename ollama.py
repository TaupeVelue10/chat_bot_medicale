import chromadb

def get_collection(db_path="rag_db", collection_name="imagerie"):
    """Récupère la collection ChromaDB avec BlueBERT embeddings"""
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # S'assurer que la collection utilise BlueBERT
    from chromadb.utils import embedding_functions
    medical_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="bionlp/bluebert_pubmed_mimic_uncased_L-12_H-768_A-12"
    )
    
    try:
        # Essayer de récupérer la collection existante
        collection = chroma_client.get_collection(collection_name)
        return collection
    except:
        # Si elle n'existe pas, la créer avec BlueBERT
        return chroma_client.create_collection(collection_name, embedding_function=medical_ef)

def analyze_missing_info(user_input):
    """Analyse intelligente des informations manquantes pour poser des questions pertinentes"""
    text = user_input.lower()
    
    # Vérifications critiques
    has_age = any(word in text for word in ['ans', 'âge', 'age', 'années'])
    has_sex = any(word in text for word in ['homme', 'femme', 'garçon', 'fille', 'patient', 'patiente'])
    
    # Si pas d'âge, c'est critique
    if not has_age:
        return "MANQUANT: âge"
    
    # Si le texte est très court (< 5 mots), demander plus de détails
    if len(text.split()) < 5:
        return "MANQUANT: description clinique"
    
    # Analyse contextuelle pour questions de clarification intelligentes
    
    # Céphalées : demander caractéristiques
    if 'céphalée' in text or 'mal de tête' in text:
        if not any(word in text for word in ['brutal', 'progressif', 'pulsatile', 'tension', 'vomissement', 'fièvre']):
            return "CLARIFICATION: caractéristiques céphalées"
    
    # Douleurs abdominales : localisation précise
    if 'abdominale' in text or 'ventre' in text:
        if not any(word in text for word in ['fid', 'fosse iliaque', 'épigastre', 'hypochondre', 'lombaire', 'sous-costale']):
            return "CLARIFICATION: localisation abdominale"
    
    # Troubles neurologiques : préciser les signes
    if any(word in text for word in ['trouble', 'faiblesse', 'paralysie', 'engourdissement']):
        if not any(word in text for word in ['moteur', 'sensitif', 'marche', 'parole', 'vision', 'cognitif']):
            return "CLARIFICATION: signes neurologiques"
    
    # Si tout semble complet, laisser RAG décider
    return "COMPLET"

def generate_clarifying_questions(missing_info, user_input):
    """Génère des questions de clarification médicale intelligentes"""
    text = user_input.lower()
    
    if 'âge' in missing_info.lower():
        return "Quel âge a le patient ?"
    
    elif 'description' in missing_info.lower():
        return "Pouvez-vous décrire plus précisément les symptômes, leur localisation et leur évolution ?"
    
    elif 'caractéristiques céphalées' in missing_info.lower():
        return "Pouvez-vous préciser les caractéristiques de ces céphalées ?\n- Sont-elles brutales (en coup de tonnerre) ou progressives ?\n- Y a-t-il des signes associés : fièvre, vomissements, troubles visuels, déficit neurologique ?"
    
    elif 'localisation abdominale' in missing_info.lower():
        return "Pouvez-vous préciser la localisation de la douleur abdominale ?\n- Fosse iliaque droite (FID) ?\n- Épigastre, hypochondre droit, lombaire ?\n- Y a-t-il de la fièvre ou des signes associés ?"
    
    elif 'signes neurologiques' in missing_info.lower():
        return "Pouvez-vous préciser les troubles neurologiques ?\n- Troubles moteurs (faiblesse, paralysie) ?\n- Troubles sensitifs (engourdissements, paresthésies) ?\n- Troubles de la marche, de l'équilibre, cognitifs ?"
    
    else:
        return "Pouvez-vous donner plus de détails sur le cas clinique ?"

def enhance_medical_query(user_input):
    """Enrichit la requête utilisateur avec des synonymes médicaux pour améliorer le matching RAG"""
    text = user_input.lower()
    enhanced = user_input
    
    # Synonymes médicaux MASSIFS pour améliorer la similarité vectorielle
    medical_synonyms = {
        # CÉPHALÉES
        'coup de tonnerre': ' céphalée brutale hémorragie scanner urgent',
        'déficit moteur': ' paralysie AVC neurologique scanner cérébral urgent',
        'vomissements matinaux': ' HTIC enfant IRM cérébrale urgente',
        'baisse de vigilance': ' HTIC pression intracrânienne IRM',
        'persistants': ' chronique résistant traitement IRM cause secondaire',
        'traitement inefficace': ' céphalée chronique résistante IRM',
        
        # ABDOMEN
        'hématurie': ' sang urines lithiase calcul rénal néphrétique scanner',
        'lombaire': ' dos rein néphrétique colique scanner abdomino-pelvien',
        'lombaire brutale': ' colique néphrétique calcul rénal scanner sans injection urgence',
        'douleur lombaire brutale': ' colique néphrétique lithiase calcul rénal scanner abdomino-pelvien',
        'sous-costale droite': ' biliaire vésicule cholécystite hépatique échographie',
        'fid': ' fosse iliaque droite appendicite échographie scanner',
        'douleur fid': ' appendicite échographie scanner abdomino-pelvien',
        'fièvre modérée': ' appendicite infection échographie',
        'diarrhée': ' gastro-entérite pas imagerie bon état général',
        'diffuses': ' gastro-entérite simple pas imagerie',
        
        # MARCHE & NEUROLOGIE  
        'chutes': ' troubles marche pas imagerie examen clinique',
        'plusieurs chutes': ' troubles marche répétées pas imagerie',
        'tug': ' test marche équilibre pas imagerie',
        'troubles urinaires': ' hydrocéphalie pression normale HPN IRM',
        'lenteur cognitive': ' hydrocéphalie cognitive HPN IRM cérébrale',
        'troubles cognitifs': ' hydrocéphalie HPN IRM cérébrale',
        'marche instable': ' sclérose plaques SEP IRM cérébrale médullaire',
        'troubles de la marche': ' sclérose plaques SEP troubles marche IRM cérébrale médullaire',
        'paresthésies': ' sclérose plaques SEP troubles sensitifs IRM cérébrale médullaire',
        'troubles sensitifs': ' sclérose plaques SEP paresthésies IRM cérébrale médullaire',
        'engourdissements': ' sclérose plaques SEP paresthésies IRM cérébrale médullaire',
        'fourmillements': ' sclérose plaques SEP paresthésies IRM cérébrale médullaire',
        'troubles visuels': ' sclérose plaques SEP IRM cérébrale',
        'intermittents': ' sclérose plaques SEP IRM',
        'progressifs': ' troubles cognitifs HPN hydrocéphalie IRM cérébrale',
        
        # GÉNÉRAUX
        'déficit neurologique': ' paralysie faiblesse moteur AVC scanner',
        'fièvre': ' température hyperthermie infection',
        'brutal': ' soudain aigu coup de tonnerre hémorragie scanner',
        'oppression': ' serrement thoracique cardiaque coronaire',
        'dyspnée': ' essoufflement respiratoire embolie pulmonaire'
    }
    
    # Ajouter les synonymes si les termes sont détectés
    for term, synonyms in medical_synonyms.items():
        if term in text:
            enhanced += synonyms
    
    return enhanced

def smart_guideline_selection(user_input, collection, n_results=20):
    """Sélection intelligente de la meilleure guideline avec scoring contextuel"""
    enhanced_query = enhance_medical_query(user_input)
    
    # Récupérer plusieurs candidates
    results = collection.query(
        query_texts=[enhanced_query],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )
    
    if not results['documents'][0]:
        return None
        
    # Scoring intelligent contextuel résoud pb avec les guidelines vagues qui l'emportent sur les + précis
    candidates = []
    for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
        score = calculate_contextual_score(user_input, doc, meta, dist)
        candidates.append({
            'document': doc,
            'metadata': meta,
            'distance': dist,
            'contextual_score': score
        })
    
    # Trier par score contextuel (le plus élevé = le meilleur)
    candidates.sort(key=lambda x: x['contextual_score'], reverse=True)
    
    return candidates[0]['document']

def calculate_contextual_score(user_input, guideline_text, metadata, vector_distance):
    """Calcule un score contextuel intelligent basé sur plusieurs facteurs"""
    text = user_input.lower()
    guideline = guideline_text.lower()
    motif = metadata.get('motif', '').lower()
    
    # Score de base inversé de la distance vectorielle (plus proche = meilleur ,logique)
    base_score = 1.0 - vector_distance
    
    # FILTRES CONTEXTUELS CRITIQUES
    
    # 1. Filtre grossesse : pénaliser TRÈS FORTEMENT si pas de mention explicite de grossesse
    if 'grossesse' in motif or 'enceinte' in guideline:
        # Boost si contexte de grossesse EXPLICITE
        if any(word in text for word in ['enceinte', 'grossesse', 'gestation', 'SA', 'semaines']):
            base_score += 0.5
        # Pénalité ÉNORME si femme mentionnée mais pas de grossesse explicite
        elif any(word in text for word in ['femme', 'patiente']):
            base_score -= 1.8  # Pénalité énorme pour éviter faux positifs grossesse
        # Pénalité encore plus forte si pas femme du tout
        else:
            base_score -= 2.0
    
    # 2. Filtre pédiatrique : pénaliser TRÈS FORTEMENT si âge adulte (>16 ans)
    if 'pediatrie' in motif or 'enfant' in guideline:
        # Extraire l'âge avec regex pour être plus précis
        import re
        age_match = re.search(r'(\d+)\s*ans?', text)
        if age_match:
            age = int(age_match.group(1))
            if age > 16:  # Adulte
                base_score -= 1.8  # Pénalité ÉNORME pour éviter confusion adulte/enfant
            else:  # Réellement un enfant
                base_score += 0.3
        elif 'enfant' in text:
            base_score += 0.3
        elif any(adult_term in text for adult_term in ['adulte', 'homme', 'femme', 'patient', 'patiente']):
            base_score -= 1.5  # Pénalité très forte pour adultes avec guidelines pédiatriques
    
    # 3. Boost spécifique par pathologie détectée (TRÈS SPÉCIFIQUE pour éviter faux positifs)
    pathology_boosts = {
        'appendicite': ['fid', 'fosse iliaque droite', 'mcburney', 'appendic'],
        'hpn': ['hpn', 'hypertension intracranienne', 'troubles cognitifs progressifs', 'hydrocéphalie'],
        'sep': ['sclérose plaques', 'sep', 'paresthésies progressives', 'troubles marche paresthésies', 'remissions rechutes'],
        'colique': ['lombaire brutale', 'néphrétique', 'lithiase', 'calcul', 'brutale'],
        'colique_nephretique': ['lombaire brutale', 'calcul', 'lithiase', 'hématurie', 'colique néphrétique', 'douleur irradiant aine'],
        'lombalgie': ['chronique', '6 semaines', 'commune', 'radiculalgie'],
        'biliaire': ['sous-costale droite', 'vésicule', 'cholécystite', 'voies biliaires', 'cholédoque'],
        'htic': ['vomissements', 'céphalées enfant', 'htic', 'pression'],
        'fievre_prolongee': ['fièvre prolongée', 'inexpliquée', 'persistante', 'chronique']  # Très spécifique
    }
    
    for pathology, keywords in pathology_boosts.items():
        if pathology in motif or pathology in guideline:
            # Pour fièvre prolongée, exiger une correspondance très spécifique
            if pathology == 'fievre_prolongee':
                if any(keyword in text for keyword in keywords):
                    base_score += 0.3  # Boost modéré seulement si très spécifique
                elif 'fièvre' in text and not any(specific in text for specific in ['prolongée', 'inexpliquée', 'persistante']):
                    base_score -= 0.5  # Pénaliser si juste "fièvre" sans contexte prolongé
            # Boost spécial pour colique néphrétique si mots-clés très spécifiques
            elif pathology == 'colique_nephretique':
                if any(keyword in text for keyword in keywords):
                    base_score += 1.0  # Boost fort pour colique néphrétique authentique
                elif 'colique' in text and any(nephro in text for nephro in ['lombaire', 'rein', 'calcul', 'lithiase', 'hématurie']):
                    base_score += 0.8  # Boost pour combinaisons suggérant néphrétique
            # Réduire boost biliaire si pas de contexte anatomique spécifique
            elif pathology == 'biliaire':
                # PÉNALISER pathologie biliaire si contexte suggère plutôt néphrétique
                if any(nephro in text for nephro in ['lombaire', 'aine', 'hématurie', 'calcul', 'lithiase']):
                    base_score -= 1.0  # Pénalité forte si contexte néphrétique
                elif 'colique' in text and not any(bili_specific in text for bili_specific in ['sous-costale droite', 'vésicule', 'cholécystite']):
                    base_score += 0.2  # Boost réduit si juste "colique" sans contexte biliaire
                elif any(keyword in text for keyword in keywords):
                    base_score += 0.5
            elif any(keyword in text for keyword in keywords):
                base_score += 0.5
                
    # 4. CORRESPONDANCE ANATOMIQUE STRICTE (critique pour éviter erreurs grossières)
    anatomical_regions = {
        'abdomen': {
            'keywords': ['abdomen', 'abdominale', 'abdominales', 'ventre', 'fid', 'fosse iliaque', 'épigastre'],
            'compatible': ['abdominal', 'digestif', 'échographie', 'scanner abdomino', 'appendicite', 'biliaire'],
            'incompatible': ['cérébral', 'crâne', 'neurologique', 'irm cérébrale', 'ponction lombaire', 'hpn']
        },
        'neurologique': {
            'keywords': ['céphalée', 'céphalées', 'mal de tête', 'neurologique', 'troubles cognitifs'],
            'compatible': ['cérébral', 'crâne', 'irm cérébrale', 'neurologique', 'scanner cérébral'],
            'incompatible': ['abdominal', 'digestif', 'échographie abdominale', 'scanner abdomino']
        }
    }
    
    detected_region = None
    for region, data in anatomical_regions.items():
        if any(keyword in text for keyword in data['keywords']):
            detected_region = region
            break
    
    if detected_region:
        region_data = anatomical_regions[detected_region]
        # Bonification forte pour correspondance anatomique
        if any(term in guideline for term in region_data['compatible']):
            base_score += 0.8  # Bonus très fort pour cohérence anatomique
        # PÉNALISATION TRÈS FORTE pour incohérence anatomique  
        elif any(term in guideline for term in region_data['incompatible']):
            base_score -= 1.5  # Pénalité énorme pour éviter erreurs grossières
    
    # 5. Boost pour correspondance de symptômes spécifiques
    symptom_matches = 0
    if 'céphalées' in text and 'céphalées' in guideline:
        symptom_matches += 1
    if 'abdominale' in text and 'abdominale' in guideline:
        symptom_matches += 1
    if 'troubles' in text and 'troubles' in guideline:
        symptom_matches += 1
        
    base_score += symptom_matches * 0.2
    
    return max(0.0, base_score)  # Éviter scores négatifs

def generate_imaging_recommendation_rag(user_input, collection):
    """Génère une recommandation basée sur sélection intelligente des guidelines"""
    
    # Sélection intelligente de la meilleure guideline
    best_guideline = smart_guideline_selection(user_input, collection)
    
    if best_guideline:
        return f"RECOMMANDATION (RAG) : {extract_recommendation_from_guideline(best_guideline)}"
    
    # Fallback minimal seulement si aucune guideline trouvée
    return "ÉVALUATION CLINIQUE : Aucune guideline trouvée - Consultation spécialisée recommandée"

# Fonction calculate_relevance_score supprimée - on utilise uniquement ChromaDB scoring !

def extract_recommendation_from_guideline(guideline_text):
    """Extrait et formate la recommandation principale d'une guideline de façon claire"""
    text = guideline_text.lower()
    
    # Classification précise des recommandations basées sur le contenu de la guideline
    if 'pas d\'imagerie' in text or 'aucune imagerie' in text:
        return f"AUCUNE : {guideline_text}"
    elif 'urgence' in text or 'immédiat' in text or 'scanner cérébral sans injection immédiat' in text:  
        return f"URGENTE : {guideline_text}"
    elif 'ponction lombaire' in text:
        return f"URGENTE : {guideline_text}"  # Ponction lombaire = urgence
    elif any(word in text for word in ['irm', 'scanner', 'échographie', 'radiographie', 'angioscanner']):
        return f"INDIQUÉE : {guideline_text}"
    else:
        return f"AUTRE : {guideline_text}"

# Garder l'ancienne fonction comme fallback


def should_ask_clarification(user_input, is_first_interaction=True):
    """Détermine si on devrait poser des questions de clarification même avec info complètes"""
    text = user_input.lower()
    
    # Toujours demander clarification au premier tour pour rendre la conversation naturelle
    if is_first_interaction:
        # Sauf si le cas est très détaillé (>15 mots avec symptômes précis)
        if len(text.split()) > 15 and any(word in text for word in ['brutal', 'progressif', 'aigu', 'chronique', 'fièvre', 'vomissement']):
            return False
        return True
    
    return False

def rag_query_interactive(user_input, collection, is_first_interaction=True):
    """Version interactive qui pose des questions de clarification naturelles"""
    # Étape 1 : Analyser si des informations importantes manquent
    analysis = analyze_missing_info(user_input)
    
    # Vérifier si des informations manquent (critiques)
    if "MANQUANT:" in analysis.upper():
        # Extraire les informations manquantes
        missing_info = analysis.split("MANQUANT:", 1)[1].strip()
        questions = generate_clarifying_questions(missing_info, user_input)
        return questions.strip(), True  # True = a besoin de plus d'infos
    
    # Étape 2 : Questions de clarification pour améliorer la précision (même si complet)
    if "CLARIFICATION:" in analysis.upper():
        clarification_type = analysis.split("CLARIFICATION:", 1)[1].strip()
        questions = generate_clarifying_questions(clarification_type, user_input)
        return questions.strip(), True
    
    # Étape 3 : Poser une question générale de clarification si c'est la première interaction
    if should_ask_clarification(user_input, is_first_interaction):
        return generate_contextual_follow_up_question(user_input), True
    
    # Étape 4 : Génération de la recommandation finale
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
    
    elif any(word in text for word in ['enfant', 'pédiatrique']) or any(word in text for word in ['8 ans', '10 ans', '12 ans']):
        return "Pour un enfant, pouvez-vous préciser :\n- Y a-t-il des vomissements, des troubles du comportement ?\n- L'enfant se plaint-il de troubles visuels ou de maux de tête matinaux ?"
    
    else:
        return "Pouvez-vous me donner quelques précisions supplémentaires sur :\n- L'évolution des symptômes (brutal, progressif) ?\n- Les signes associés (fièvre, nausées, troubles neurologiques) ?\n- Le contexte (antécédents, traitements en cours) ?"


