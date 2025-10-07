#!/usr/bin/env python3
"""
Tests diagnostiques pour identifier les points d'amélioration du scoring RAG
Analyse détaillée des erreurs pour fine-tuning du système
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ollama import get_collection, enhance_medical_query, calculate_contextual_score, generate_imaging_recommendation_rag
from colorama import Fore, Style, init
import json

init(autoreset=True)

class RAGScoringDiagnostic:
    def __init__(self):
        self.collection = get_collection()
        self.errors = []
        self.scoring_issues = []
        
    def analyze_case(self, query, expected_motif, expected_status, case_name):
        """Analyse complète d'un cas pour identifier les problèmes de scoring"""
        
        print(f"\n{Fore.CYAN}=== ANALYSE DIAGNOSTIQUE: {case_name} ==={Style.RESET_ALL}")
        print(f"Query: {query}")
        print(f"Attendu: motif='{expected_motif}', status='{expected_status}'")
        
        # 1. Enrichissement de la requête
        enhanced_query = enhance_medical_query(query)
        print(f"\n{Fore.YELLOW}1. ENRICHISSEMENT:{Style.RESET_ALL}")
        print(f"   Original: {query}")
        print(f"   Enrichi:  {enhanced_query}")
        if enhanced_query != query:
            added = enhanced_query[len(query):].strip()
            print(f"   Ajouté:   {Fore.GREEN}{added}{Style.RESET_ALL}")
        
        # 2. Récupération des candidates
        results = self.collection.query(
            query_texts=[enhanced_query],
            n_results=10,
            include=['documents', 'metadatas', 'distances']
        )
        
        print(f"\n{Fore.YELLOW}2. TOP 10 CANDIDATES AVEC SCORING:{Style.RESET_ALL}")
        
        candidates = []
        for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
            contextual_score = calculate_contextual_score(query, doc, meta, dist)
            motif = meta.get('motif', 'N/A')
            
            candidates.append({
                'rank': i+1,
                'motif': motif,
                'distance': dist,
                'contextual_score': contextual_score,
                'document': doc,
                'metadata': meta
            })
            
            # Identification du motif attendu
            is_expected = (motif == expected_motif)
            expected_marker = f"{Fore.GREEN}[ATTENDU]{Style.RESET_ALL}" if is_expected else ""
            
            print(f"   {i+1:2d}. Score: {contextual_score:.4f} | Dist: {dist:.4f} | {motif} {expected_marker}")
            print(f"       {doc[:80]}...")
        
        # 3. Analyse de la sélection
        candidates.sort(key=lambda x: x['contextual_score'], reverse=True)
        selected = candidates[0]
        
        print(f"\n{Fore.YELLOW}3. GUIDELINE SÉLECTIONNÉE:{Style.RESET_ALL}")
        print(f"   Motif: {selected['motif']}")
        print(f"   Score: {selected['contextual_score']:.4f}")
        print(f"   Distance: {selected['distance']:.4f}")
        print(f"   Contenu: {selected['document'][:100]}...")
        
        # 4. Vérification si la bonne guideline est présente
        expected_guideline = None
        expected_rank = None
        for i, candidate in enumerate(candidates):
            if candidate['motif'] == expected_motif:
                expected_guideline = candidate
                expected_rank = i + 1
                break
        
        print(f"\n{Fore.YELLOW}4. ANALYSE DE L'ERREUR:{Style.RESET_ALL}")
        if expected_guideline:
            print(f"   ✅ Guideline attendue TROUVÉE au rang {expected_rank}")
            print(f"   📊 Score attendu: {expected_guideline['contextual_score']:.4f}")
            print(f"   📊 Score sélectionné: {selected['contextual_score']:.4f}")
            
            if selected['motif'] != expected_motif:
                score_diff = selected['contextual_score'] - expected_guideline['contextual_score']
                print(f"   ❌ ERREUR DE SCORING: Différence de {score_diff:.4f}")
                
                # Analyse détaillée des scores
                self._analyze_scoring_difference(query, selected, expected_guideline, case_name)
        else:
            print(f"   ❌ Guideline attendue '{expected_motif}' NON TROUVÉE dans le top 10")
            print(f"   🔍 Problème de retrieval vectoriel (embeddings)")
        
        # 5. Test du résultat final
        final_result = generate_imaging_recommendation_rag(query, self.collection)
        actual_status = self._extract_status(final_result)
        
        print(f"\n{Fore.YELLOW}5. RÉSULTAT FINAL:{Style.RESET_ALL}")
        print(f"   Attendu: {expected_status}")
        print(f"   Obtenu:  {actual_status}")
        
        success = (actual_status == expected_status)
        if success:
            print(f"   ✅ {Fore.GREEN}SUCCÈS{Style.RESET_ALL}")
        else:
            print(f"   ❌ {Fore.RED}ÉCHEC{Style.RESET_ALL}")
            self.errors.append({
                'case': case_name,
                'query': query,
                'expected_motif': expected_motif,
                'expected_status': expected_status,
                'actual_motif': selected['motif'],
                'actual_status': actual_status,
                'score_issue': selected['motif'] != expected_motif
            })
        
        return success
    
    def _analyze_scoring_difference(self, query, selected, expected, case_name):
        """Analyse détaillée des différences de scoring"""
        print(f"\n{Fore.MAGENTA}   ANALYSE DÉTAILLÉE DU SCORING:{Style.RESET_ALL}")
        
        # Recalcul des scores avec debug
        selected_score = calculate_contextual_score(query, selected['document'], selected['metadata'], selected['distance'])
        expected_score = calculate_contextual_score(query, expected['document'], expected['metadata'], expected['distance'])
        
        print(f"   📊 Score sélectionné ({selected['motif']}): {selected_score:.4f}")
        print(f"   📊 Score attendu ({expected['motif']}): {expected_score:.4f}")
        
        # Facteurs identifiés
        factors = []
        
        # Distance vectorielle
        if selected['distance'] < expected['distance']:
            factors.append(f"Distance vectorielle favorise sélectionné ({selected['distance']:.4f} < {expected['distance']:.4f})")
        else:
            factors.append(f"Distance vectorielle favorise attendu ({expected['distance']:.4f} < {selected['distance']:.4f})")
        
        # Analyse du texte
        query_lower = query.lower()
        selected_text_lower = selected['document'].lower()
        expected_text_lower = expected['document'].lower()
        
        # Correspondances de mots-clés
        selected_matches = self._count_keyword_matches(query_lower, selected_text_lower)
        expected_matches = self._count_keyword_matches(query_lower, expected_text_lower)
        
        if selected_matches > expected_matches:
            factors.append(f"Plus de correspondances mots-clés dans sélectionné ({selected_matches} vs {expected_matches})")
        elif expected_matches > selected_matches:
            factors.append(f"Plus de correspondances mots-clés dans attendu ({expected_matches} vs {selected_matches})")
        
        for factor in factors:
            print(f"   • {factor}")
        
        # Recommandation d'amélioration
        self.scoring_issues.append({
            'case': case_name,
            'issue': f"Préfère {selected['motif']} à {expected['motif']}",
            'score_diff': selected_score - expected_score,
            'distance_diff': selected['distance'] - expected['distance'],
            'factors': factors
        })
    
    def _count_keyword_matches(self, query, text):
        """Compte les correspondances de mots-clés"""
        query_words = set(query.split())
        text_words = set(text.split())
        return len(query_words.intersection(text_words))
    
    def _extract_status(self, result):
        """Extrait le statut du résultat"""
        if 'RECOMMANDATION (RAG) : ' in result:
            status_part = result.split('RECOMMANDATION (RAG) : ')[1]
            if ' : ' in status_part:
                return status_part.split(' : ')[0]
        return 'AUTRE'
    
    def run_diagnostic_tests(self):
        """Lance les tests diagnostiques sur des cas problématiques identifiés"""
        
        print(f"{Fore.CYAN}{'='*80}")
        print(f"🔬 DIAGNOSTIC RAG - ANALYSE DES POINTS D'AMÉLIORATION")  
        print(f"{'='*80}{Style.RESET_ALL}")
        
        # Cas de test problématiques identifiés
        test_cases = [
            {
                'name': 'Colique néphrétique vs Biliaire',
                'query': 'Homme 45 ans, douleur lombaire brutale irradiant vers l\'aine avec hématurie microscopique',
                'expected_motif': 'colique_nephretique',
                'expected_status': 'INDIQUÉE'
            },
            {
                'name': 'Appendicite adulte vs Pédiatrique',
                'query': 'Femme 28 ans, douleur fosse iliaque droite depuis 12h avec fièvre 38.5°C et nausées',
                'expected_motif': 'douleur_abdominale',
                'expected_status': 'INDIQUÉE'
            },
            {
                'name': 'HTIC enfant correct',
                'query': 'Enfant 8 ans, vomissements matinaux répétés depuis 1 semaine avec céphalées et troubles visuels',
                'expected_motif': 'pediatrie_neurologie',
                'expected_status': 'URGENTE'
            },
            {
                'name': 'Méningite vs HTIC',
                'query': 'Patient 34 ans, céphalées fébriles brutales avec photophobie et raideur de nuque',
                'expected_motif': 'cephalees_aigues',
                'expected_status': 'URGENTE'
            },
            {
                'name': 'SEP vs autres neuro',
                'query': 'Femme 30 ans, troubles de la marche progressifs avec paresthésies des membres et fatigue',
                'expected_motif': 'sclerose_plaques',
                'expected_status': 'INDIQUÉE'
            },
            {
                'name': 'Grossesse - faux positif',
                'query': 'Patiente 22 ans, douleurs abdominales FID avec fièvre',
                'expected_motif': 'douleur_abdominale',
                'expected_status': 'INDIQUÉE'
            },
            {
                'name': 'Lombalgie commune - négative',
                'query': 'Homme 35 ans, lombalgie commune depuis 4 semaines sans amélioration, bon état général',
                'expected_motif': 'lombalgie',
                'expected_status': 'AUCUNE'
            }
        ]
        
        successes = 0
        total = len(test_cases)
        
        for test_case in test_cases:
            success = self.analyze_case(
                test_case['query'],
                test_case['expected_motif'], 
                test_case['expected_status'],
                test_case['name']
            )
            if success:
                successes += 1
        
        self._generate_improvement_report(successes, total)
    
    def _generate_improvement_report(self, successes, total):
        """Génère un rapport d'amélioration détaillé"""
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"📊 RAPPORT D'AMÉLIORATION - FINE-TUNING RECOMMENDATIONS")
        print(f"{'='*80}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}📈 PERFORMANCE GLOBALE:{Style.RESET_ALL}")
        accuracy = (successes / total) * 100
        print(f"   Précision: {accuracy:.1f}% ({successes}/{total})")
        
        if accuracy >= 80:
            print(f"   ✅ {Fore.GREEN}Excellent - Fine-tuning mineur nécessaire{Style.RESET_ALL}")
        elif accuracy >= 60:
            print(f"   ⚠️  {Fore.YELLOW}Correct - Améliorations ciblées recommandées{Style.RESET_ALL}")
        else:
            print(f"   ❌ {Fore.RED}Problématique - Révision majeure nécessaire{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}🔧 POINTS D'AMÉLIORATION IDENTIFIÉS:{Style.RESET_ALL}")
        
        # Analyse des erreurs par type
        error_types = {}
        for error in self.errors:
            error_type = f"{error['expected_motif']} → {error['actual_motif']}"
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)
        
        for i, (error_type, errors) in enumerate(error_types.items(), 1):
            print(f"\n   {i}. {Fore.RED}ERREUR TYPE: {error_type}{Style.RESET_ALL}")
            print(f"      Fréquence: {len(errors)} cas")
            for error in errors:
                print(f"      • {error['case']}: {error['expected_status']} → {error['actual_status']}")
        
        print(f"\n{Fore.YELLOW}🎯 RECOMMANDATIONS DE FINE-TUNING:{Style.RESET_ALL}")
        
        # Recommandations spécifiques basées sur l'analyse
        recommendations = []
        
        # Analyse des issues de scoring
        scoring_issues_by_type = {}
        for issue in self.scoring_issues:
            issue_type = issue['issue']
            if issue_type not in scoring_issues_by_type:
                scoring_issues_by_type[issue_type] = []
            scoring_issues_by_type[issue_type].append(issue)
        
        for i, (issue_type, issues) in enumerate(scoring_issues_by_type.items(), 1):
            avg_score_diff = sum(issue['score_diff'] for issue in issues) / len(issues)
            print(f"\n   {i}. {Fore.MAGENTA}AJUSTEMENT SCORING:{Style.RESET_ALL} {issue_type}")
            print(f"      Différence moyenne: {avg_score_diff:+.4f}")
            
            if avg_score_diff > 0.5:
                print(f"      ⚡ Action: Réduire le boost de {issue_type.split(' à ')[0]}")
                recommendations.append(f"Réduire bonification pour motif contenant '{issue_type.split(' à ')[0]}'")
            elif avg_score_diff > 0.2:
                print(f"      🔧 Action: Ajuster légèrement le scoring de {issue_type.split(' à ')[0]}")
                recommendations.append(f"Ajustement mineur pour '{issue_type.split(' à ')[0]}'")
            
            # Facteurs communs
            common_factors = {}
            for issue in issues:
                for factor in issue['factors']:
                    if factor not in common_factors:
                        common_factors[factor] = 0
                    common_factors[factor] += 1
            
            for factor, count in common_factors.items():
                if count > 1:
                    print(f"      📊 Facteur récurrent: {factor} ({count}x)")
        
        print(f"\n{Fore.GREEN}✅ ACTIONS PRIORITAIRES:{Style.RESET_ALL}")
        for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommandations
            print(f"   {i}. {rec}")
        
        # Métriques techniques
        print(f"\n{Fore.YELLOW}📊 MÉTRIQUES TECHNIQUES:{Style.RESET_ALL}")
        if self.scoring_issues:
            avg_score_diff = sum(abs(issue['score_diff']) for issue in self.scoring_issues) / len(self.scoring_issues)
            avg_distance_diff = sum(abs(issue['distance_diff']) for issue in self.scoring_issues) / len(self.scoring_issues)
            print(f"   Différence score moyenne: {avg_score_diff:.4f}")
            print(f"   Différence distance moyenne: {avg_distance_diff:.4f}")

def main():
    """Fonction principale"""
    try:
        diagnostic = RAGScoringDiagnostic()
        diagnostic.run_diagnostic_tests()
        return 0
    except Exception as e:
        print(f"\n❌ {Fore.RED}Erreur lors du diagnostic: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
