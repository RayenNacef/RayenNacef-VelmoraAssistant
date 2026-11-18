import unittest

from velmora.retrieval import TfidfIndex

DOCS = [
    ("KB-A", ["express", "delivery", "price"]),
    ("KB-B", ["standard", "delivery", "price"]),
    ("KB-C", ["gift", "card"]),
]


class TestTfidf(unittest.TestCase):
    def test_best_article_first(self):
        ranking = TfidfIndex(DOCS).search(["express", "delivery"])
        self.assertEqual(ranking[0][0], "KB-A")

    def test_scores_are_cosines(self):
        ranking = TfidfIndex(DOCS).search(["gift", "card"])
        self.assertAlmostEqual(ranking[0][1], 1.0)
        for _, score in ranking:
            self.assertTrue(0 < score <= 1.0 + 1e-9)

    def test_ties_are_broken_by_id(self):
        docs = [("KB-2", ["lock", "key"]), ("KB-1", ["lock", "key"])]
        ranking = TfidfIndex(docs).search(["lock"])
        self.assertEqual([d for d, _ in ranking], ["KB-1", "KB-2"])
        self.assertEqual(ranking, TfidfIndex(docs).search(["lock"]))

    def test_unknown_words_lower_the_score(self):
        index = TfidfIndex(DOCS)
        known = index.search(["standard", "delivery"])[0][1]
        with_unknown = index.search(["standard", "delivery", "carbon", "footprint"])[0][1]
        self.assertLess(with_unknown, known)

    def test_no_match_gives_empty_list(self):
        index = TfidfIndex(DOCS)
        self.assertEqual(index.search([]), [])
        self.assertEqual(index.search(["switzerland"]), [])

    def test_empty_collection(self):
        self.assertEqual(TfidfIndex([]).search(["delivery"]), [])


if __name__ == "__main__":
    unittest.main()
