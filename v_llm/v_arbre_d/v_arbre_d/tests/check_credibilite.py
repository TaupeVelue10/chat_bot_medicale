import io
import sys
import os
import unittest

# Ensure project root is on sys.path so `from main import ...` works when running tests directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main import analyse_texte_medical, decision_imagerie, afficher_contraindications


class TestCredibiliteClinique(unittest.TestCase):
    def test_parse_age_sex(self):
        f = analyse_texte_medical("Patiente 45 ans avec fièvre")
        self.assertEqual(f['age'], 45)
        self.assertEqual(f['sexe'], 'f')

        f2 = analyse_texte_medical("patient 30 ans")
        self.assertEqual(f2['age'], 30)
        self.assertEqual(f2['sexe'], 'm')

    def test_fever_variants(self):
        variants = ['fièvre', 'fievre', 'fébrile', 'fébr']
        for v in variants:
            with self.subTest(v=v):
                self.assertTrue(analyse_texte_medical(v)['fievre'])

    def test_decision_imagerie_pregnancy_urgent(self):
        f = {
            'age': 30,
            'sexe': 'f',
            'fievre': True,
            'brutale': False,
            'deficit': False,
            'vertige': False,
            'oncologique': False,
            'grossesse': True,
            'chirurgie': False,
            'pacemaker': False,
            'claustrophobie': False,
            'troubles_visuels': False,
            'acouphene': False,
            'douleurs_articulaires': False
        }
        out = decision_imagerie(f)
        self.assertIn('URGENCE', out)
        self.assertIn('grossesse', out.lower())

    def test_oncologique_injection(self):
        f = {
            'age': 60,
            'sexe': 'm',
            'fievre': False,
            'brutale': False,
            'deficit': False,
            'vertige': False,
            'oncologique': True,
            'grossesse': False,
            'chirurgie': False,
            'pacemaker': False,
            'claustrophobie': False,
            'troubles_visuels': False,
            'acouphene': False,
            'douleurs_articulaires': False
        }
        out = decision_imagerie(f)
        self.assertIn('injection', out.lower())

    def test_contraindications_output(self):
        f = {
            'age': None,
            'sexe': 'f',
            'fievre': False,
            'brutale': False,
            'deficit': False,
            'vertige': False,
            'oncologique': False,
            'grossesse': False,
            'chirurgie': False,
            'pacemaker': False,
            'claustrophobie': False,
            'troubles_visuels': False,
            'acouphene': False,
            'douleurs_articulaires': False
        }
        captured = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured
            afficher_contraindications(f)
        finally:
            sys.stdout = old_stdout

        out = captured.getvalue()
        # Expect reminders about pregnancy/testing for women of childbearing age
        self.assertIn('Grossesse', out)

    def test_load_keywords_file(self):
        # S'assurer que l'analyse utilise les mots-clés du fichier JSON si présent
        from main import _load_keywords
        kws = _load_keywords()
        self.assertIn('fievre', kws)
        self.assertTrue(isinstance(kws['fievre'], list))

    def test_typos_and_synonyms(self):
        # Variantes et fautes d'orthographe doivent être reconnues
        samples = [
            ('Patiente 28 ans avec fievre et vertige', ['fievre', 'vertige']),
            ('patient 50 ans febrile, antécédent de cancer', ['fievre', 'oncologique']),
            ('patiente enceinte, douleur machoire', ['grossesse', 'douleurs_articulaires']),
            ('patient claustro phobie', ['claustrophobie'])
        ]

        for text, expected_keys in samples:
            with self.subTest(text=text):
                parsed = analyse_texte_medical(text)
                for k in expected_keys:
                    self.assertTrue(parsed.get(k), msg=f"{k} not detected in: {text}")

    def test_false_positive_reduction(self):
        # Phrase neutre ne doit pas déclencher fièvre ou oncologie
        p = analyse_texte_medical('patient pour bilan annuel sans symptome particulier')
        self.assertFalse(p['fievre'])
        self.assertFalse(p['oncologique'])

    def test_combination_rules(self):
        # combinaison fièvre + brutale → urgence
        p = analyse_texte_medical('patiente 33 ans fievre installation brutale')
        out = decision_imagerie(p)
        self.assertIn('URGENCE', out)

    def test_plausibility_checks(self):
        # Age clearly implausible (>120)
        f = analyse_texte_medical('patiente 130 ans')

        def is_plausible(parsed):
            age = parsed.get('age')
            if age is not None and not (0 < age <= 120):
                return False
            # Pregnancy should only be true for females
            if parsed.get('grossesse') and parsed.get('sexe') != 'f':
                return False
            # Pregnancy with age outside typical childbearing range is suspicious
            if parsed.get('grossesse') and age is not None and not (12 <= age <= 55):
                return False
            return True

        self.assertFalse(is_plausible(f))

        # Inconsistent: male + enceinte
        f2 = analyse_texte_medical('patient 35 ans enceinte')
        self.assertFalse(is_plausible(f2))


if __name__ == '__main__':
    unittest.main()
