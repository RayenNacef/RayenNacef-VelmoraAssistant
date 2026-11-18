import unittest

from velmora.text import split_sentences, stem, tokenize


class TestStem(unittest.TestCase):
    def test_plurals(self):
        self.assertEqual(stem("batteries"), stem("battery"))
        self.assertEqual(stem("countries"), stem("country"))
        self.assertEqual(stem("returns"), stem("return"))
        self.assertEqual(stem("boxes"), stem("box"))
        self.assertEqual(stem("addresses"), stem("address"))

    def test_past_tense(self):
        self.assertEqual(stem("returned"), stem("return"))
        self.assertEqual(stem("received"), stem("receive"))
        self.assertEqual(stem("shipped"), stem("ship"))
        self.assertEqual(stem("called"), stem("call"))

    def test_words_that_must_not_be_cut(self):
        self.assertEqual(stem("express"), "express")
        self.assertEqual(stem("status"), "status")


class TestNegation(unittest.TestCase):
    def test_negation_is_kept(self):
        self.assertIn("not", tokenize("This item cannot be returned"))
        self.assertIn("not", tokenize("I can't log in"))
        self.assertIn("not", tokenize("I don’t have the code"))
        self.assertIn("no", tokenize("no customs fees"))

    def test_contraction_leaves_no_junk(self):
        self.assertNotIn("t", tokenize("I can't log in"))
        self.assertNotIn("don", tokenize("I don't know"))

    def test_negated_and_positive_differ(self):
        self.assertNotEqual(tokenize("can be returned"), tokenize("cannot be returned"))


class TestTokenize(unittest.TestCase):
    def test_stopwords_and_punctuation(self):
        self.assertEqual(tokenize("How long does Standard delivery take?"),
                         ["standard", "delivery", "tak"])

    def test_empty(self):
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize("?!"), [])

    def test_prices_stay_in_one_sentence(self):
        self.assertEqual(split_sentences("It costs 4.90 EUR. Free from 60 EUR."),
                         ["It costs 4.90 EUR.", "Free from 60 EUR."])


if __name__ == "__main__":
    unittest.main()
