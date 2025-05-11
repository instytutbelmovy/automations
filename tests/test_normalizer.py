import unittest
from automations.normalizer import Normalizer


class TestNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = Normalizer()

    def test_tokinization_normalize(self):
        self.assertEqual(self.normalizer.tokinization_normalize("прывітаньне"), "прывітаньне")
        self.assertEqual(self.normalizer.tokinization_normalize("прывiтаньне"), "прывітаньне")  # ангельская i
        self.assertEqual(self.normalizer.tokinization_normalize("прывіта'ньне"), "прывітаʼньне")  # апостраф
        self.assertEqual(self.normalizer.tokinization_normalize("прывіта´ньне"), "прывіта́ньне")  # націск
        self.assertEqual(self.normalizer.tokinization_normalize("Прывітаньне"), "Прывітаньне")
        self.assertEqual(self.normalizer.tokinization_normalize("ГУСЯ-СЮСЯ"), "ГУСЯ-СЮСЯ")

    def test_grammar_db_aggressive_normalize(self):
        self.assertEqual(self.normalizer.grammar_db_aggressive_normalize("прывітаньне"), "прывітаньне")
        self.assertEqual(self.normalizer.grammar_db_aggressive_normalize("прывiтаньне"), "прывітаньне")
        self.assertEqual(self.normalizer.grammar_db_aggressive_normalize("прывіта'ньне"), "прывітаʼньне")
        self.assertEqual(self.normalizer.grammar_db_aggressive_normalize("прывіта´ньне"), "прывіта́ньне")
        self.assertEqual(self.normalizer.grammar_db_aggressive_normalize("Прывітаньне"), "прывітаньне")  # lowercase
        self.assertEqual(self.normalizer.grammar_db_aggressive_normalize("ўчора"), "учора")  # ў -> у
        self.assertEqual(self.normalizer.grammar_db_aggressive_normalize("ЎЧОРА"), "учора")  # Ў -> у

    def test_grammar_db_light_normalize(self):
        self.assertEqual(self.normalizer.grammar_db_light_normalize("прывітаньне"), "прывітаньне")
        self.assertEqual(self.normalizer.grammar_db_light_normalize("прывiтаньне"), "прывітаньне")
        self.assertEqual(self.normalizer.grammar_db_light_normalize("прывіта'ньне"), "прывітаʼньне")
        self.assertEqual(self.normalizer.grammar_db_light_normalize("прывіта´ньне"), "прывіта́ньне")
        self.assertEqual(self.normalizer.grammar_db_light_normalize("Прывітаньне"), "Прывітаньне")  # НЕ lowercase
        self.assertEqual(self.normalizer.grammar_db_light_normalize("прывіта+ньне"), "прывіта́ньне")  # + націск

    def test_is_apostrophe(self):
        self.assertTrue(self.normalizer.is_apostrophe("ʼ"))
        self.assertTrue(self.normalizer.is_apostrophe("'"))
        self.assertTrue(self.normalizer.is_apostrophe("'"))
        self.assertFalse(self.normalizer.is_apostrophe("а"))

    def test_is_letter(self):
        self.assertTrue(self.normalizer.is_letter("а"))
        self.assertTrue(self.normalizer.is_letter("Ё"))
        self.assertTrue(self.normalizer.is_letter("́"))  # націск
        self.assertTrue(self.normalizer.is_letter("ʼ"))  # апостраф
        self.assertTrue(self.normalizer.is_letter("-"))
        self.assertTrue(self.normalizer.is_letter("q"))
        self.assertTrue(self.normalizer.is_letter("9"))
        self.assertFalse(self.normalizer.is_letter("!"))
        # todo: дадаць тэсты для камбінаваных літар з націскам, калі будзе рэалізавана

    def test_unstress(self):
        self.assertEqual(self.normalizer.unstress("прывіта́ньне"), "прывітаньне")
        self.assertEqual(self.normalizer.unstress("прывіта´ньне"), "прывітаньне")
        self.assertEqual(self.normalizer.unstress("прывіта+ньне"), "прывітаньне")
        self.assertEqual(self.normalizer.unstress("прывітаньне"), "прывітаньне")

    def test_has_stress(self):
        self.assertTrue(self.normalizer.has_stress("прывіта́ньне"))
        self.assertTrue(self.normalizer.has_stress("прывіта´ньне"))
        self.assertTrue(self.normalizer.has_stress("прывіта+ньне"))
        self.assertFalse(self.normalizer.has_stress("прывітаньне"))

    def test_db_stress_normalize(self):
        self.assertEqual(self.normalizer.db_stress_normalize("прывіта́ньне"), "прывіта+ньне")
        self.assertEqual(self.normalizer.db_stress_normalize("прывіта´ньне"), "прывіта+ньне")
        self.assertEqual(self.normalizer.db_stress_normalize("прывітаньне"), "прывітаньне")


if __name__ == "__main__":
    unittest.main()
