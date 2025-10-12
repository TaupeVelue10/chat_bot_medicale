#!/usr/bin/env python3
"""
Module RAG médical optimisé avec architecture refactorisée
Système d'aide à la décision pour l'imagerie médicale
"""

import chromadb
import json

# Variables globales
MODEL_NAME = "bionlp/bluebert_pubmed_mimic_uncased_L-12_H-768_A-12"
CHROMA_PATH = "rag_db"

def get_collection():
    """Récupération de la collection ChromaDB"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Try to create a SentenceTransformer-based embedding function. If unavailable,
    # fall back to returning a collection without an embedding function so the
    # rest of the code can run (searches and scoring based on stored documents may
    # be limited without embeddings).
    try:
        from chromadb.utils import embedding_functions
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=MODEL_NAME
        )
        collection = client.get_collection(name="imagerie", embedding_function=embedding_fn)
    except Exception as e:
        print("[WARN] sentence_transformers not available or embedding init failed in get_collection:", e)
        print("[WARN] Returning collection without embedding function. To enable embeddings, run: pip install sentence_transformers")
        # If collection exists with a saved embedding config that can't be built,
        # try to delete & recreate it without embedding to allow usage.
        try:
            client.delete_collection("imagerie")
        except Exception:
            pass
        collection = client.get_or_create_collection("imagerie")
    return collection

# ========================================
# 1. DÉTECTION INTELLIGENTE DES INFORMATIONS MANQUANTES
# ========================================

class InformationAnalyzer:
    """Classe centralisée pour analyser les informations manquantes"""
    
    @staticmethod
    def analyze_completeness(user_input):
        """
        Analyse globale de la complétude des informations
        Retourne: (status, missing_category, details)
        """
        text = user_input.lower()
        
        # 1. Vérifications critiques obligatoires
        critical_missing = InformationAnalyzer._check_critical_info(text)
        if critical_missing:
            return "CRITICAL_MISSING", critical_missing, "Informations essentielles manquantes"
        
        # 2. Informations importantes pour précision diagnostique
        clarification_needed = InformationAnalyzer._check_clarification_needed(text)
        if clarification_needed:
            return "NEEDS_CLARIFICATION", clarification_needed, "Précisions utiles pour affiner"
        
        # 3. Questions contextuelles pour première interaction
        contextual_questions = InformationAnalyzer._check_contextual_questions(text)
        if contextual_questions:
            return "CONTEXTUAL_QUESTIONS", contextual_questions, "Questions d'approfondissement"
        
        return "COMPLETE", None, "Informations suffisantes"
    
    @staticmethod
    def _check_critical_info(text):
        """Vérification des informations critiques obligatoires"""
        # Âge obligatoire
        has_age = any(word in text for word in ['ans', 'âge', 'age', 'années'])
        if not has_age:
            return "age"
        
        # Description minimale (plus de 4 mots)
        if len(text.split()) < 5:
            return "description"
        
        return None
    
    @staticmethod
    def _check_clarification_needed(text):
        """Vérification si des clarifications spécifiques sont nécessaires"""
        # Céphalées sans caractéristiques
        if any(word in text for word in ['céphalée', 'mal de tête']):
            if not any(word in text for word in ['brutal', 'progressif', 'pulsatile', 'tension', 'vomissement', 'fièvre', 'coup de tonnerre']):
                return "cephalees"
        # Douleurs abdominales sans localisation
        if any(word in text for word in ['abdominale', 'ventre', 'douleur']):
            if not any(word in text for word in ['fid', 'fosse iliaque', 'épigastre', 'hypochondre', 'lombaire', 'sous-costale']):
                return "abdomen"
        
        # Troubles neurologiques sans précision
        if any(word in text for word in ['trouble', 'faiblesse', 'paralysie', 'engourdissement']):
            if not any(word in text for word in ['moteur', 'sensitif', 'marche', 'parole', 'vision', 'cognitif']):
                return "neurologique"
        
        return None
    
    @staticmethod
    def _check_contextual_questions(text):
        """Identification du domaine pour questions contextuelles seulement si nécessaire"""
        # Pour les céphalées, ne pas poser de questions si c'est déjà précis
        if any(word in text for word in ['céphalée', 'mal de tête', 'crâne', 'migraine']):
            # Si c'est déjà précis (migraine habituelle, pas de signe d'alarme), pas de questions
            if any(precise in text for precise in ['habituelle', 'migraine', 'pas de signe', 'primaire']):
                return None
            return "cephalees"
        elif any(word in text for word in ['abdomen', 'ventre', 'douleur']):
            return "abdomen"
        elif any(word in text for word in ['trouble', 'faiblesse', 'neurologique']):
            return "neurologique"
        elif any(word in text for word in ['enfant', 'pédiatrique']) or any(word in text for word in ['8 ans', '10 ans', '12 ans']):
            return "pediatrie"
        
        return "general"

# ========================================
# 2. GÉNÉRATEUR UNIFIÉ DE QUESTIONS
# ========================================

class QuestionGenerator:
    """Classe centralisée pour générer toutes les questions de clarification"""
    
    @staticmethod
    def generate_questions(status, category, user_input):
        """
        Génération intelligente de questions selon le statut et la catégorie
        Évite les redondances en analysant le texte d'entrée
        """
        text = user_input.lower()
        
        if status == "CRITICAL_MISSING":
            return QuestionGenerator._generate_critical_questions(category)
        elif status == "NEEDS_CLARIFICATION":
            return QuestionGenerator._generate_clarification_questions(category, text)
        elif status == "CONTEXTUAL_QUESTIONS":
            return QuestionGenerator._generate_contextual_questions(category, text)
        
        return "Aucune question nécessaire."
    
    @staticmethod
    def _generate_critical_questions(category):
        """Questions pour informations critiques manquantes"""
        if category == "age":
            return "Quel âge a le patient ?"
        elif category == "description":
            return "Pouvez-vous décrire plus précisément les symptômes, leur localisation et leur évolution ?"
        return "Informations supplémentaires nécessaires."
    
    @staticmethod
    def _generate_clarification_questions(category, text):
        """Questions de clarification spécifiques par domaine"""
        if category == "cephalees":
            return "Pouvez-vous préciser les caractéristiques de ces céphalées ?\n- Sont-elles brutales (en coup de tonnerre) ou progressives ?\n- Y a-t-il des signes associés : fièvre, vomissements, troubles visuels, déficit neurologique ?"
        
        elif category == "abdomen":
            return "Pouvez-vous préciser la localisation de la douleur abdominale ?\n- Fosse iliaque droite (FID) ?\n- Épigastre, hypochondre droit, lombaire ?\n- Y a-t-il de la fièvre ou des signes associés ?"
        
        elif category == "neurologique":
            return QuestionGenerator._generate_neurological_questions(text)
        
        return "Pouvez-vous donner plus de détails ?"
    
    @staticmethod
    def _generate_neurological_questions(text):
        """Questions neurologiques évitant les redondances"""
        questions = []
        
        # Troubles moteurs
        if not any(motor in text for motor in ['moteur', 'faiblesse', 'paralysie', 'hémiplégie', 'hémiparésie', 'faible']):
            questions.append("Troubles moteurs (faiblesse, paralysie) ?")
        
        # Troubles sensitifs  
        if not any(sensit in text for sensit in ['sensitif', 'engourdissement', 'fourmillement', 'paresthésie', 'perte de sensibilité']):
            questions.append("Troubles sensitifs (engourdissements, paresthésies) ?")
        
        # Troubles spécifiques non mentionnés
        missing_troubles = []
        if 'marche' not in text and 'démarche' not in text:
            missing_troubles.append("marche")
        if 'équilibre' not in text and 'instabilité' not in text:
            missing_troubles.append("équilibre") 
        if 'cognitif' not in text and 'mémoire' not in text:
            missing_troubles.append("cognitifs")
        
        # Construction grammaticalement correcte
        if missing_troubles:
            trouble_questions = []
            for trouble in missing_troubles:
                if trouble == "marche":
                    trouble_questions.append("de la marche")
                elif trouble == "équilibre":
                    trouble_questions.append("de l'équilibre")
                elif trouble == "cognitifs":
                    trouble_questions.append("cognitifs")
            
            if len(trouble_questions) == 1:
                questions.append(f"Troubles {trouble_questions[0]} ?")
            elif len(trouble_questions) == 2:
                questions.append(f"Troubles {trouble_questions[0]} et {trouble_questions[1]} ?")
            else:
                questions.append(f"Troubles {', '.join(trouble_questions[:-1])} et {trouble_questions[-1]} ?")
        
        if questions:
            return "Pouvez-vous préciser les troubles neurologiques ?\n- " + "\n- ".join(questions)
        else:
            return "Merci pour ces précisions. Depuis quand ces symptômes sont-ils présents et comment évoluent-ils ?"
    
    @staticmethod
    def _generate_contextual_questions(category, text):
        """Questions contextuelles par domaine médical"""
        if category == "cephalees":
            # Questions intelligentes évitant les redondances
            questions = []
            if not any(brutal in text for brutal in ['brutal', 'coup de tonnerre', 'soudain']):
                if not any(prog in text for prog in ['progressif', 'chronique', 'habituel']):
                    questions.append("Ces céphalées sont-elles brutales (en coup de tonnerre) ou progressives ?")
            
            if not any(signe in text for signe in ['fièvre', 'vomissement', 'trouble', 'déficit']):
                questions.append("Y a-t-il des signes associés : fièvre, vomissements, troubles de la vision, déficit neurologique ?")
            
            if questions:
                return "Pour mieux vous orienter, pouvez-vous préciser :\n- " + "\n- ".join(questions)
        
        elif category == "abdomen":
            return "Pour préciser l'indication d'imagerie, pouvez-vous me dire :\n- Où se situe exactement la douleur (fosse iliaque droite, épigastre, etc.) ?\n- Y a-t-il de la fièvre, des nausées, des vomissements ?"
        
        elif category == "neurologique":
            return QuestionGenerator._generate_neurological_questions(text)
        
        elif category == "pediatrie":
            return "Pour un enfant, pouvez-vous préciser :\n- Y a-t-il des vomissements, des troubles du comportement ?\n- L'enfant se plaint-il de troubles visuels ou de maux de tête matinaux ?"
        
        else:
            return "Pouvez-vous me donner quelques précisions supplémentaires sur :\n- L'évolution des symptômes (brutal, progressif) ?\n- Les signes associés (fièvre, nausées, troubles neurologiques) ?\n- Le contexte (antécédents, traitements en cours) ?"

# ========================================
# 3. BOOST UNIFIÉ PAR PATHOLOGIE
# ========================================

class PathologyBooster:
    """Classe centralisée pour tous les boosts pathologiques"""
    
    @staticmethod
    def enhance_query(user_input):
        """Enrichissement intelligent de la requête avec synonymes médicaux"""
        enhanced = user_input
        
        # Synonymes médicaux spécialisés
        medical_synonyms = {
            # ABDOMEN & DIGESTIF
            'nausées': ' nausées vomissements digestif gastrique',
            'vomissements': ' vomissements nausées digestif gastrique',
            'douleur irradiant': ' colique néphrétique calcul rénal scanner abdomino-pelvien sans injection',
            'douleur irradiant aine': ' colique néphrétique calcul rénal lithiase scanner abdomino-pelvien',
            'sous-costale droite': ' biliaire vésicule cholécystite hépatique échographie',
            'fid': ' fosse iliaque droite appendicite échographie scanner',
            'douleur fid': ' appendicite échographie scanner abdomino-pelvien',
            'fièvre modérée': ' appendicite infection échographie',
            'diarrhée': ' gastro-entérite pas imagerie bon état général',
            'diffuses': ' gastro-entérite simple pas imagerie',
            
            # LOMBALGIE
            'lombaire simple': ' lombalgie commune chronique pas imagerie 6 semaines',
            'lombaire commune': ' lombalgie chronique pas imagerie avant 6 semaines',
            'douleur lombaire simple': ' lombalgie commune pas imagerie avant 6 semaines',
            
            # NEUROLOGIE & MARCHE
            'chutes': ' troubles marche pas imagerie examen clinique',
            'plusieurs chutes': ' troubles marche répétées pas imagerie',
            'tug': ' test marche équilibre pas imagerie',
            'troubles urinaires': ' hydrocéphalie pression normale HPN IRM',
            'lenteur cognitive': ' hydrocéphalie cognitive HPN IRM cérébrale',
            'troubles cognitifs': ' hydrocéphalie HPN IRM cérébrale',
            
            # CÉPHALÉES AIGUES
            'coup de tonnerre': ' céphalée brutale hémorragie sous-arachnoïdienne HSA scanner cérébral urgent',
            'céphalée brutale': ' coup de tonnerre hémorragie sous-arachnoïdienne scanner urgent',
            'céphalée subite': ' coup de tonnerre hémorragie sous-arachnoïdienne HSA scanner',
        }
        
        # Application des synonymes
        for term, synonyms in medical_synonyms.items():
            if term in user_input.lower():
                enhanced += synonyms
        
        return enhanced
    
    @staticmethod
    def calculate_pathology_score(user_input, guideline, metadata, base_distance):
        """Calcul unifié du score contextuel avec tous les boosts pathologiques"""
        text = user_input.lower()
        motif = metadata.get('motif', '').lower()
        base_score = 2.0 - base_distance  # Score de base inversé
        
        # 1. Filtres d'exclusion critiques
        base_score = PathologyBooster._apply_exclusion_filters(base_score, text, motif, guideline)
        
        # 2. Boosts spécifiques par pathologie
        base_score = PathologyBooster._apply_pathology_boosts(base_score, text, motif, guideline)
        
        # 3. Correspondance anatomique
        base_score = PathologyBooster._apply_anatomical_matching(base_score, text, motif, guideline)
        
        return max(0, base_score)  # Score minimum de 0
    
    @staticmethod
    def _apply_exclusion_filters(score, text, motif, guideline):
        """Application des filtres d'exclusion (grossesse, pédiatrie)"""
        # Filtre grossesse
        if 'grossesse' in motif or 'enceinte' in guideline:
            if any(female in text for female in ['femme', 'patiente']):
                if any(pregnant in text for pregnant in ['enceinte', 'grossesse', 'gestante']):
                    score += 0.8  # Boost pour vraie grossesse
                else:
                    score -= 1.0  # Pénalité si femme mais pas enceinte
            else:
                score -= 2.0  # Pénalité forte si pas femme du tout
        
        # Filtre pédiatrique
        if 'pediatrie' in motif or 'enfant' in guideline:
            import re
            age_match = re.search(r'(\d+)\s*ans?', text)
            if age_match:
                age = int(age_match.group(1))
                if age > 16:
                    score -= 1.8  # Pénalité énorme pour adulte
                else:
                    score += 0.3  # Bonus pour vrai enfant
            elif 'enfant' in text:
                score += 0.3
            elif any(adult_term in text for adult_term in ['adulte', 'homme', 'femme', 'patient', 'patiente']):
                score -= 1.5
        
        return score
    
    @staticmethod
    def _apply_pathology_boosts(score, text, motif, guideline):
        """Application des boosts spécifiques par pathologie"""
        pathology_boosts = {
            'appendicite': ['fid', 'fosse iliaque droite', 'mcburney', 'appendic'],
            'hpn': ['hpn', 'hypertension intracranienne', 'troubles cognitifs progressifs', 'hydrocéphalie'],
            'sep': ['sclérose plaques', 'sep', 'paresthésies progressives', 'troubles marche paresthésies', 'remissions rechutes'],
            'colique_nephretique': ['lombaire brutale', 'calcul', 'lithiase', 'hématurie', 'colique néphrétique', 'douleur irradiant aine', 'colique lombaire', 'colique typique', 'rein', 'rénal'],
            'lombalgie': ['chronique', '6 semaines', 'commune', 'radiculalgie', 'lombaire simple', 'lombaire commune', 'sans signe neurologique'],
            'biliaire': ['sous-costale droite', 'vésicule', 'cholécystite', 'voies biliaires', 'cholédoque'],
            'htic': ['vomissements', 'céphalées enfant', 'htic', 'pression'],
            'fievre_prolongee': ['fièvre prolongée', 'inexpliquée', 'persistante', 'chronique'],
            'cephalees': ['coup de tonnerre', 'céphalée brutale', 'red flags', 'scanner urgent', 'migraine', 'céphalée', 'mal de tête', 'céphalée primaire']
        }
        
        for pathology, keywords in pathology_boosts.items():
            if pathology in motif or pathology in guideline:
                if pathology == 'cephalees' and 'coup de tonnerre' in text and 'céphalée' in guideline:
                    score += 1.5  # Boost très fort pour coup de tonnerre
                elif pathology == 'colique_nephretique' and any(keyword in text for keyword in keywords):
                    score += 1.0  # Boost fort pour colique néphrétique
                elif pathology == 'biliaire' and any(nephro in text for nephro in ['lombaire', 'aine', 'hématurie', 'calcul', 'lithiase']):
                    score -= 1.0  # Pénalité si contexte néphrétique
                elif any(keyword in text for keyword in keywords):
                    score += 0.5
        
        return score
    
    @staticmethod
    def _apply_anatomical_matching(score, text, motif, guideline):
        """Application de la correspondance anatomique"""
        anatomical_regions = {
            'abdomen': {
                'keywords': ['abdomen', 'abdominale', 'abdominales', 'ventre', 'fid', 'fosse iliaque', 'épigastre', 'colique', 'néphrétique'],
                'compatible': ['abdominal', 'digestif', 'échographie', 'scanner abdomino', 'appendicite', 'biliaire', 'néphrétique', 'calcul', 'lithiase'],
                'incompatible': ['cérébral', 'crâne', 'irm cérébrale', 'ponction lombaire', 'hpn', 'troubles marche', 'paresthésies']
            },
            'lombalgie': {
                'keywords': ['lombaire', 'lombaire simple', 'lombaire commune'],
                'compatible': ['lombalgie', 'radiculalgie', 'irm lombaire', 'déficit neurologique'],
                'incompatible': ['appendicite', 'scanner abdomino', 'échographie abdominale']
            },
            'neurologique': {
                'keywords': ['céphalée', 'céphalées', 'mal de tête', 'neurologique', 'troubles cognitifs', 'déficit moteur'],
                'compatible': ['cérébral', 'crâne', 'irm cérébrale', 'neurologique', 'scanner cérébral', 'troubles marche', 'paresthésies'],
                'incompatible': ['abdominal', 'digestif', 'échographie abdominale', 'scanner abdomino', 'colique', 'néphrétique']
            }
        }
        
        detected_region = None
        for region, data in anatomical_regions.items():
            if any(keyword in text for keyword in data['keywords']):
                detected_region = region
                break
        
        if detected_region:
            region_data = anatomical_regions[detected_region]
            if any(compatible in guideline for compatible in region_data['compatible']):
                score += 0.3
            elif any(incompatible in guideline for incompatible in region_data['incompatible']):
                score -= 1.5  # Pénalité forte pour incompatibilité anatomique
        
        return score

# ========================================
# 4. SYSTÈME RAG UNIFIÉ
# ========================================

class RAGSystem:
    """Système RAG unifié pour les recommandations d'imagerie"""
    
    def __init__(self, collection):
        self.collection = collection
        self.analyzer = InformationAnalyzer()
        self.question_generator = QuestionGenerator()
        self.booster = PathologyBooster()
    
    def process_query(self, user_input, is_first_interaction=True):
        """
        Traitement unifié d'une requête utilisateur
        Retourne: (response, needs_more_info)
        """
        # 1. Analyse de la complétude
        status, category, details = self.analyzer.analyze_completeness(user_input)
        
        # 2. Génération de questions si nécessaire
        if status in ["CRITICAL_MISSING", "NEEDS_CLARIFICATION"] or (status == "CONTEXTUAL_QUESTIONS" and is_first_interaction):
            questions = self.question_generator.generate_questions(status, category, user_input)
            return questions, True
        
        # 3. Génération de la recommandation finale
        recommendation = self.generate_recommendation(user_input)
        return f"RECOMMANDATION D'IMAGERIE :\n\n{recommendation}", False
    
    def generate_recommendation(self, user_input):
        """Génération de la recommandation d'imagerie avec RAG optimisé"""
        # Enrichissement de la requête
        enhanced_query = self.booster.enhance_query(user_input)
        
        # Récupération des candidates
        results = self.collection.query(
            query_texts=[enhanced_query],
            n_results=20,
            include=['documents', 'metadatas', 'distances']
        )
        
        if not results['documents'][0]:
            return "Aucune guideline trouvée pour ce cas."
        
        # Scoring contextuel unifié
        scored_guidelines = []
        for doc, metadata, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            score = self.booster.calculate_pathology_score(user_input, doc, metadata, distance)
            scored_guidelines.append((score, doc, metadata))
        
        # Sélection de la meilleure
        scored_guidelines.sort(key=lambda x: x[0], reverse=True)
        best_score, best_guideline, best_metadata = scored_guidelines[0]
        
        return best_guideline

# ========================================
# 5. INTERFACES PUBLIQUES (COMPATIBILITÉ)
# ========================================

def smart_guideline_selection(user_input, collection, n_results=20):
    """Interface de compatibilité pour la sélection de guideline"""
    rag_system = RAGSystem(collection)
    return rag_system.generate_recommendation(user_input)

def rag_query_interactive(user_input, collection, is_first_interaction=True):
    """Interface de compatibilité pour les requêtes interactives"""
    rag_system = RAGSystem(collection)
    return rag_system.process_query(user_input, is_first_interaction)

def calculate_contextual_score(user_input, guideline, metadata, distance):
    """Interface de compatibilité pour le calcul de score"""
    booster = PathologyBooster()
    return booster.calculate_pathology_score(user_input, guideline, metadata, distance)
