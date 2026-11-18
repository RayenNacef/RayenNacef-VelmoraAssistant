import unittest

from velmora.assistant import Assistant
from velmora.rewrite import rewrite_question


def article(id_, title, body):
    return {"id": id_, "title": title, "category": "Test", "updated": "2026-01-01", "body": body}


ARTICLES = [
    article("KB-01", "Parcel lost or not received",
            "If tracking has not moved for 7 days, contact support. We send a new parcel or refund you."),
    article("KB-02", "Gift cards", "Gift cards are valid for 24 months. They are sent by email."),
]


class TestRewrite(unittest.TestCase):
    def test_customer_words_become_help_center_words(self):
        self.assertEqual(rewrite_question("My package is stuck"), "my parcel is not moved")
        self.assertEqual(rewrite_question("Can I send it back?"), "can i return it ?")
        self.assertEqual(rewrite_question("It arrived broken"), "it arrived damaged")
        self.assertIn("login", rewrite_question("I can't sign in"))

    def test_negation_before_the_rule(self):
        
        self.assertEqual(rewrite_question("I can't remember my password"), "i forgot my password")

    def test_time_words(self):
        self.assertEqual(rewrite_question("for a week"), "for 7 days")
        self.assertEqual(rewrite_question("How fast is it?"), "how long is it?")

    def test_normal_question_is_unchanged(self):
        self.assertEqual(rewrite_question("How long is a gift card valid?"),
                         "how long is a gift card valid?")

    def test_word_inside_another_word_is_not_rewritten(self):
        # "packaging" is not "package", "points" alone is not loyalty points
        self.assertEqual(rewrite_question("original packaging"), "original packaging")
        self.assertEqual(rewrite_question("pickup points"), "pickup points")


class TestAssistantWithRewrite(unittest.TestCase):
    def test_synonym_question_is_answered_only_with_rewrite(self):
        question = "My package is stuck for a week"
        self.assertTrue(Assistant(ARTICLES, rewrite=False).answer(question)["refused"])
        r = Assistant(ARTICLES).answer(question)
        self.assertFalse(r["refused"])
        self.assertEqual(r["cited"], ["KB-01"])
        self.assertIn("7 days", r["answer"])


if __name__ == "__main__":
    unittest.main()
