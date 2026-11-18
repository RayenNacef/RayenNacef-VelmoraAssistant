import unittest

from scripts.serve import ask
from velmora.assistant import I_DONT_KNOW, Assistant


def article(id_, title, body):
    return {"id": id_, "title": title, "category": "Test", "updated": "2026-01-01", "body": body}


ARTICLES = [
    article("KB-01", "Gift cards", "Gift cards are valid for 24 months. They are sent by email."),
    article("KB-02", "Standard delivery", "Standard delivery takes 3 to 5 working days."),
]


class TestAskPage(unittest.TestCase):
    def setUp(self):
        self.assistant = Assistant(ARTICLES)

    def test_answer_has_citation_and_ranking(self):
        data = ask(self.assistant, "How long is a gift card valid?")
        self.assertFalse(data["refused"])
        self.assertEqual(data["cited"], ["KB-01"])
        self.assertEqual(data["ranking"][0]["id"], "KB-01")
        self.assertEqual(data["ranking"][0]["title"], "Gift cards")
        self.assertTrue(data["ranking"][0]["cited"])
        self.assertTrue(data["reason"].startswith("Answered"))

    def test_unknown_question_says_i_dont_know_without_citation(self):
        data = ask(self.assistant, "Do you have a shop in Lyon?")
        self.assertTrue(data["refused"])
        self.assertEqual(data["answer"], I_DONT_KNOW)
        self.assertEqual(data["cited"], [])
        self.assertEqual(data["ranking"], [])
        self.assertEqual(data["reason"], "I don't know")

    def test_low_score_reason(self):
        strict = Assistant(ARTICLES, min_score=0.99)
        data = ask(strict, "How long is a gift card valid?")
        self.assertTrue(data["refused"])
        self.assertIn("below 0.99", data["reason"])
        self.assertFalse(any(r["cited"] for r in data["ranking"]))

    def test_rewritten_question_is_shown_only_when_changed(self):
        self.assertIsNone(ask(self.assistant, "How long is a gift card valid?")["searched_as"])
        data = ask(self.assistant, "My package is late")
        self.assertEqual(data["searched_as"], "my parcel is late")

    def test_long_question_is_cut(self):
        data = ask(self.assistant, "gift " * 500)
        self.assertLessEqual(len(data["question"]), 500)


if __name__ == "__main__":
    unittest.main()
