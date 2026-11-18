import unittest

from velmora import metrics


class TestRecallAtK(unittest.TestCase):
    def test_single_gold_article(self):
        ranked = ["KB-03", "KB-06", "KB-01"]
        self.assertEqual(metrics.recall_at_k(ranked, ["KB-06"], 1), 0.0)
        self.assertEqual(metrics.recall_at_k(ranked, ["KB-06"], 3), 1.0)

    def test_two_gold_articles_counts_half(self):
        ranked = ["KB-12", "KB-16", "KB-14", "KB-13"]
        self.assertEqual(metrics.recall_at_k(ranked, ["KB-12", "KB-13"], 3), 0.5)
        self.assertEqual(metrics.recall_at_k(ranked, ["KB-12", "KB-13"], 5), 1.0)

    def test_empty_ranking(self):
        self.assertEqual(metrics.recall_at_k([], ["KB-06"], 5), 0.0)

    def test_no_gold_article_gives_none(self):
        self.assertIsNone(metrics.recall_at_k(["KB-01"], [], 1))


class TestKeywordJudge(unittest.TestCase):
    def test_case_and_spaces_are_ignored(self):
        answer = "Standard delivery takes 3 to 5  Working Days."
        self.assertTrue(metrics.keywords_found(answer, ["3 to 5 working days"]))

    def test_all_keywords_are_needed(self):
        answer = "You can return it within 30 days."
        self.assertFalse(metrics.keywords_found(answer, ["30 days", "14 days"]))

    def test_no_answer_never_matches(self):
        self.assertFalse(metrics.keywords_found(None, ["10 days"]))
        self.assertFalse(metrics.keywords_found("", ["10 days"]))

    def test_known_weakness_substring(self):
        # known limit of the judge
        self.assertTrue(metrics.keywords_found("held for 110 days", ["10 days"]))


def item(answerable, keywords=None, gold=None):
    return {"id": "X", "question": "?", "answerable": answerable,
            "answer_keywords": keywords, "source_articles": gold or []}


def result(refused, answer="", cited=None, ranking=None):
    return {"answer": answer, "cited": cited or [], "refused": refused,
            "ranking": ranking or [], "top_score": 0.5, "coverage": 1.0,
            "conflict": False}


ANSWERABLE = item(True, ["10 days"], ["KB-10"])
UNANSWERABLE = item(False)


class TestOutcomes(unittest.TestCase):
    def test_correct_answer(self):
        row = metrics.score_question(ANSWERABLE, result(False, "Held for 10 days.", ["KB-10"]))
        self.assertEqual(row["outcome"], metrics.CORRECT)
        self.assertTrue(row["correct"])

    def test_answered_but_wrong(self):
        row = metrics.score_question(ANSWERABLE, result(False, "Held for 7 days.", ["KB-10"]))
        self.assertEqual(row["outcome"], metrics.INCORRECT)
        self.assertFalse(row["correct"])

    def test_false_refusal(self):
        row = metrics.score_question(ANSWERABLE, result(True, "I don't know."))
        self.assertEqual(row["outcome"], metrics.FALSE_REFUSAL)

    def test_refusal_is_never_correct_even_with_keywords(self):
        row = metrics.score_question(item(True, ["know"], ["KB-10"]), result(True, "I don't know."))
        self.assertEqual(row["outcome"], metrics.FALSE_REFUSAL)

    def test_correct_refusal(self):
        row = metrics.score_question(UNANSWERABLE, result(True, "I don't know."))
        self.assertEqual(row["outcome"], metrics.CORRECT_REFUSAL)
        self.assertTrue(row["correct"])

    def test_unanswerable_but_answered(self):
        row = metrics.score_question(UNANSWERABLE, result(False, "Something.", ["KB-01"]))
        self.assertEqual(row["outcome"], metrics.WRONGLY_ANSWERED)
        self.assertFalse(row["correct"])


class TestSummary(unittest.TestCase):
    def test_counts_add_up(self):
        rows = [
            metrics.score_question(ANSWERABLE, result(False, "10 days", ["KB-10"])),
            metrics.score_question(ANSWERABLE, result(False, "7 days", ["KB-10"])),
            metrics.score_question(ANSWERABLE, result(True)),
            metrics.score_question(UNANSWERABLE, result(True)),
            metrics.score_question(UNANSWERABLE, result(False, "x", ["KB-01"])),
        ]
        s = metrics.summarize(rows)
        self.assertEqual((s["correct"], s["incorrect"], s["false_refusals"]), (1, 1, 1))
        self.assertEqual((s["correct_refusals"], s["wrongly_answered"]), (1, 1))
        self.assertEqual(s["correct"] + s["incorrect"] + s["false_refusals"], s["answerable"])
        self.assertAlmostEqual(s["correct_share"], 1 / 3)

    def test_bad_row_is_caught(self):
        row = metrics.score_question(ANSWERABLE, result(True))
        row["outcome"] = "something else"
        with self.assertRaises(ValueError):
            metrics.summarize([row])


class TestCitations(unittest.TestCase):
    def test_extra_citation(self):
        c = metrics.citation_checks(["KB-06", "KB-07"], ["KB-06"])
        self.assertEqual(c, {"cited_any_gold": True, "cited_only_gold": False, "cited_all_gold": True})

    def test_missing_gold_citation(self):
        c = metrics.citation_checks(["KB-12"], ["KB-12", "KB-13"])
        self.assertEqual(c, {"cited_any_gold": True, "cited_only_gold": True, "cited_all_gold": False})

    def test_wrong_article(self):
        c = metrics.citation_checks(["KB-01"], ["KB-06"])
        self.assertEqual(c, {"cited_any_gold": False, "cited_only_gold": False, "cited_all_gold": False})

    def test_refused_rows_have_no_citation_check(self):
        row = metrics.score_question(ANSWERABLE, result(True))
        self.assertIsNone(row["cited_any_gold"])


if __name__ == "__main__":
    unittest.main()
