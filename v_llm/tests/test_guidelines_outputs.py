from src.ollama import rag_biomistral_query
from src.indexage import create_index

# Liste de scénarios de test (input, output attendu partiel)
test_cases = [
    {
        "input": "céphalées brutales, fièvre, déficit moteur",
        "expected": "URGENCE: Adresser aux urgences immédiatement"
    },
    {
        "input": "céphalées, antécédent de cancer du sein",
        "expected": "Scanner cérébral avec injection"
    },
    {
        "input": "céphalées chroniques, pas de fièvre, pas de déficit, pas de cancer",
        "expected": "Pour préciser: Groupe 1"
    },
    {
        "input": "céphalées progressives depuis 1 mois, pas de fièvre, pas de déficit, pas d’antécédent oncologique",
        "expected": "IRM cérébrale"
    },
    {
        "input": "céphalées, pace-maker, pas de fièvre, pas de déficit",
        "expected": "Scanner cérébral"
    },
    # Scanner guidelines
    {
        "input": "céphalées, femme de 30 ans, scanner demandé",
        "expected": "test de grossesse"
    },
    {
        "input": "céphalées, femme de 25 ans enceinte de 2 semaines, scanner demandé",
        "expected": "contre-indication absolue"
    },
    {
        "input": "céphalées, scanner injecté demandé, patient de 65 ans",
        "expected": "dosage créatinine"
    },
    {
        "input": "céphalées, scanner injecté demandé, antécédent de chirurgie rénale",
        "expected": "dosage créatinine"
    },
    {
        "input": "céphalées, scanner injecté demandé, allergie à l'iode",
        "expected": "vérifier allergie au produit de contraste iodé"
    },
    # IRM guidelines
    {
        "input": "céphalées, chirurgie récente avec pose de matériel il y a 3 semaines, IRM demandée",
        "expected": "attendre la 6ème semaine"
    },
    {
        "input": "céphalées, femme enceinte de 2 mois, IRM demandée",
        "expected": "contre-indication à l’IRM"
    },
    {
        "input": "céphalées, pace-maker, IRM demandée",
        "expected": "se rapprocher du centre d’imagerie"
    },
    {
        "input": "céphalées, valve cardiaque, IRM demandée",
        "expected": "envoyer les références du matériel"
    },
    {
        "input": "céphalées, prothèse articulaire posée il y a 2 mois, IRM demandée",
        "expected": "aucun problème"
    },
    {
        "input": "céphalées, claustrophobie, IRM demandée",
        "expected": "se rapprocher du centre d’imagerie"
    },
    {
        "input": "céphalées, IRM injectée demandée, antécédent d’allergie",
        "expected": "vérifier absence d’allergie"
    },
    # Systematic questions
    {
        "input": "céphalées",
        "expected": "poser des questions systématiques"
    },
    {
        "input": "céphalées, douleurs articulaires",
        "expected": "maladie de Horton"
    },
    {
        "input": "céphalées, troubles visuels, image stroboscopique",
        "expected": "préciser le type de trouble visuel"
    },
    {
        "input": "céphalées, cécité",
        "expected": "considérer comme déficit moteur"
    },
    {
        "input": "céphalées, vertiges",
        "expected": "considérer comme déficit moteur"
    },
    {
        "input": "céphalées, acouphènes",
        "expected": "préciser sur l’ordonnance"
    },
    {
        "input": "céphalées, premier épisode",
        "expected": "premier épisode"
    },
    {
        "input": "céphalées, pas premier épisode",
        "expected": "déjà un bilan"
    },
    {
        "input": "céphalées, céphalées constantes chroniques",
        "expected": "chroniques ou par crises"
    },
    {
        "input": "céphalées, antécédents oncologiques",
        "expected": "contexte oncologique"
    },
    {
        "input": "céphalées, antécédents infectieux cérébraux",
        "expected": "antécédents particuliers"
    },
    # Realistic patient scenarios for guideline coverage
    {
        "input": "céphalées, femme de 28 ans, scanner demandé, pas de ménopause, pas de contraception",
        "expected": "test de grossesse"
    },
    {
        "input": "céphalées, femme de 45 ans, scanner injecté demandé, antécédent de malformation rénale",
        "expected": "dosage créatinine"
    },
    {
        "input": "céphalées, homme de 70 ans, scanner injecté demandé",
        "expected": "dosage créatinine"
    },
    {
        "input": "céphalées, scanner injecté demandé, allergie à la Bétadine",
        "expected": "ne contre-indique pas le scanner"
    },
    {
        "input": "céphalées, femme enceinte de 1 mois, IRM demandée",
        "expected": "contre-indication à l’IRM"
    },
    {
        "input": "céphalées, chirurgie cérébrale avec pose de matériel il y a 2 semaines, IRM demandée",
        "expected": "attendre la 6ème semaine"
    },
    {
        "input": "céphalées, pace-maker, IRM demandée",
        "expected": "se rapprocher du centre d’imagerie"
    },
    {
        "input": "céphalées, valve cardiaque mécanique, IRM demandée",
        "expected": "envoyer les références du matériel"
    },
    {
        "input": "céphalées, prothèse de hanche posée il y a 2 mois, IRM demandée",
        "expected": "aucun problème"
    },
    {
        "input": "céphalées, claustrophobie, IRM demandée",
        "expected": "se rapprocher du centre d’imagerie"
    },
    {
        "input": "céphalées, IRM injectée demandée, patient ayant déjà eu une IRM injectée",
        "expected": "pas besoin de créatinine"
    },
    {
        "input": "céphalées, IRM injectée demandée, antécédent d’allergie",
        "expected": "vérifier absence d’allergie"
    },
    {
        "input": "céphalées, homme de 35 ans, fièvre, déficit sensitif",
        "expected": "URGENCE"
    },
    {
        "input": "céphalées, femme de 60 ans, antécédent de cancer du poumon",
        "expected": "Scanner en 1ère intention"
    },
    {
        "input": "céphalées, pas de fièvre, pas de déficit, pas d’antécédent oncologique, pas de contre-indication",
        "expected": "IRM en première intention"
    },
    {
        "input": "céphalées, antécédent d’allergie aux crustacés, scanner injecté demandé",
        "expected": "ne contre-indique pas le scanner"
    },
    {
        "input": "céphalées, douleurs articulaires, suspicion de maladie de Horton",
        "expected": "maladie de Horton"
    },
    {
        "input": "céphalées, troubles visuels, cécité",
        "expected": "considérer comme déficit moteur"
    },
    {
        "input": "céphalées, vertiges",
        "expected": "considérer comme déficit moteur"
    },
    {
        "input": "céphalées, acouphènes",
        "expected": "préciser sur l’ordonnance"
    },
    {
        "input": "céphalées, premier épisode",
        "expected": "premier épisode"
    },
    {
        "input": "céphalées, crises répétées depuis 6 mois",
        "expected": "chroniques ou par crises"
    },
    {
        "input": "céphalées, antécédents infectieux cérébraux",
        "expected": "antécédents particuliers"
    },
]

def run_tests():
    collection = create_index()
    print("\n--- Tests automatiques des guidelines client ---\n")
    for idx, case in enumerate(test_cases, 1):
        print(f"Test {idx}: {case['input']}")
        output = rag_biomistral_query(case['input'], collection)
        print(f"Réponse: {output}")
        if case['expected'].lower() in output.lower():
            print("✅ OK\n")
        else:
            print(f"❌ ECHEC (attendu: {case['expected']})\n")

if __name__ == "__main__":
    run_tests()
