import unittest

from velmora.assistant import I_DONT_KNOW, Assistant, numbers_disagree, sentences_conflict
from velmora.kb import parse_article
from velmora.text import tokenize


def article(id_, title, updated, body):
    return {"id": id_, "title": title, "category": "Test", "updated": updated, "body": body}


ARTICLES = [
    article("KB-01", "Express delivery", "2026-02-10",
            "Express delivery costs 7.90 EUR. It arrives the next working day."),
    article("KB-02", "Express delivery guide", "2022-09-14",
            "Express delivery costs 9.90 EUR. Orders must be placed before noon."),
    article("KB-03", "Gift cards", "2026-01-01",
            "Gift cards are valid for 24 months. They are sent by email."),
]


class TestRefusal(unittest.TestCase):
    def setUp(self):
        self.assistant = Assistant(ARTICLES)

    def test_empty_question_is_refused(self):
        for question in ["", "   ", "?"]:
            r = self.assistant.answer(question)
            self.assertTrue(r["refused"])
            self.assertEqual(r["answer"], I_DONT_KNOW)
            self.assertEqual(r["cited"], [])
            self.assertEqual(r["ranking"], [])

    def test_unknown_topic_is_refused(self):
        r = self.assistant.answer("Do you have a shop in Lyon?")
        self.assertTrue(r["refused"])
        self.assertEqual(r["cited"], [])

    def test_known_topic_is_answered_with_citation(self):
        r = self.assistant.answer("How long is a gift card valid?")
        self.assertFalse(r["refused"])
        self.assertIn("24 months", r["answer"])
        self.assertEqual(r["cited"], ["KB-03"])

    def test_article_with_empty_body_is_refused(self):
        empty = [article("KB-05", "Gift cards", "2026-01-01", "")]
        a = Assistant(empty)
        self.assertEqual(a.best_sentences("KB-05", {"gift"}), [])
        r = a.answer("gift cards")
        self.assertTrue(r["refused"])
        self.assertEqual(r["answer"], I_DONT_KNOW)
        self.assertEqual(r["cited"], [])

    def test_thresholds_are_configurable(self):
        strict = Assistant(ARTICLES, min_score=0.99)
        self.assertTrue(strict.answer("How long is a gift card valid?")["refused"])


class TestConflicts(unittest.TestCase):
    def test_conflict_is_shown_newest_first_with_dates(self):
        r = Assistant(ARTICLES).answer("How much does express delivery cost?")
        self.assertTrue(r["conflict"])
        self.assertEqual(r["cited"], ["KB-01", "KB-02"])
        self.assertIn("7.90", r["answer"])
        self.assertIn("9.90", r["answer"])
        self.assertIn("2026-02-10", r["answer"])
        self.assertIn("may be out of date", r["answer"])
        self.assertLess(r["answer"].index("KB-01"), r["answer"].index("KB-02"))

    def test_numbers_disagree(self):
        self.assertTrue(numbers_disagree("costs 7.90 EUR", "costs 9.90 EUR"))
        self.assertFalse(numbers_disagree("within 5 business days", "in 5 business days"))
        self.assertFalse(numbers_disagree("within 30 days", "costs 12 EUR"))

    def test_same_unit_but_other_topic_is_not_a_conflict(self):
        # 7 days vs 14 days, but delivery vs returns
        question = set(tokenize("How long does delivery take?"))
        self.assertFalse(sentences_conflict(
            "Delivery takes 7 days.", "Items can be returned within 14 days of delivery.", question))

    def test_same_topic_different_numbers_is_a_conflict(self):
        question = set(tokenize("How many days do I have to return an item?"))
        self.assertTrue(sentences_conflict(
            "You can return any item within 30 days.",
            "Sale items can be returned within 14 days.", question))


class TestOldArticle(unittest.TestCase):
    def test_old_article_gets_a_warning(self):
        old = [article("KB-09", "Bike locks", "2021-01-01", "A new key costs 12 EUR.")]
        r = Assistant(old).answer("How much is a new key for a bike lock?")
        self.assertFalse(r["refused"])
        self.assertIn("may be out of date", r["answer"])


class TestParseArticle(unittest.TestCase):
    def test_header_and_body(self):
        raw = "---\nid: KB-99\ntitle: Test: a title\nupdated: 2026-01-01\n---\n\n# Test\n\nFirst. Second."
        a = parse_article(raw)
        self.assertEqual(a["id"], "KB-99")
        self.assertEqual(a["title"], "Test: a title")
        self.assertEqual(a["body"], "First. Second.")

    def test_missing_header_is_an_error(self):
        with self.assertRaises(ValueError):
            parse_article("# no header here")


if __name__ == "__main__":
    unittest.main()
