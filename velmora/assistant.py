import re
from datetime import date

from velmora.retrieval import TfidfIndex
from velmora.rewrite import rewrite_question
from velmora.text import split_sentences, stem, tokenize

TODAY = date(2026, 7, 1)

MIN_SCORE = 0.25
MIN_COVERAGE = 0.5
CONFLICT_RATIO = 0.6   #2nd and 3rd article must score at least 60% of the 1st
OLD_AFTER_DAYS = 730
MIN_SHARED_WORDS = 2   #question words two sentences must share to be compared

I_DONT_KNOW = "I don't know. The help center does not seem to cover this question."

NUMBER_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(%|[a-z]+)")
NOT_UNITS = {"to", "and", "or", "on", "of", "a", "the"}


def numbers_by_unit(text):
    
    found = {}
    for number, unit in NUMBER_RE.findall(text.lower()):
        unit = stem(unit)
        if unit in NOT_UNITS:
            continue
        found.setdefault(unit, set()).add(number)
    return found


def numbers_disagree(text_a, text_b):
    a = numbers_by_unit(text_a)
    b = numbers_by_unit(text_b)
    for unit in a:
        if unit in b and not (a[unit] & b[unit]):
            return True
    return False


def sentences_conflict(sentence_a, sentence_b, question_terms):
    # same topic (shared question words) but different numbers for the same unit
    if not numbers_disagree(sentence_a, sentence_b):
        return False
    units = set(numbers_by_unit(sentence_a)) | set(numbers_by_unit(sentence_b))
    shared = question_terms & set(tokenize(sentence_a)) & set(tokenize(sentence_b))
    shared = {t for t in shared if t not in units and not t.isdigit()}
    return len(shared) >= MIN_SHARED_WORDS


class Assistant:
    def __init__(self, articles, min_score=MIN_SCORE, min_coverage=MIN_COVERAGE,
                 conflict_ratio=CONFLICT_RATIO, rewrite=True):
        self.articles = {a["id"]: a for a in articles}
        self.min_score = min_score
        self.min_coverage = min_coverage
        self.conflict_ratio = conflict_ratio
        self.rewrite = rewrite
        docs = [(a["id"], tokenize(a["title"] + " " + a["body"])) for a in articles]
        self.index = TfidfIndex(docs)

    def prepare(self, question):
        # customer words -> help-center words (velmora/rewrite.py)
        return rewrite_question(question) if self.rewrite else question

    def search(self, question, k=5):
        return self.index.search(tokenize(self.prepare(question)), k)

    def coverage(self, question_terms, article_id):
        # share of the question words (weighted by idf) found in the article.
        if not question_terms:
            return 0.0
        article = self.articles[article_id]
        article_terms = set(tokenize(article["title"] + " " + article["body"]))
        total = sum(self.index.get_idf(t) for t in question_terms)
        found = sum(self.index.get_idf(t) for t in question_terms if t in article_terms)
        return found / total

    def best_sentences(self, article_id, question_terms):
        # best sentence + the next one
        article = self.articles[article_id]
        sentences = split_sentences(article["body"])
        if not sentences:
            return []
        useful_terms = question_terms - set(tokenize(article["title"]))
        best_i, best_score = 0, -1.0
        for i, sentence in enumerate(sentences):
            terms = set(tokenize(sentence))
            score = sum(self.index.get_idf(t) for t in useful_terms if t in terms)
            if score > best_score:
                best_i, best_score = i, score
        return sentences[best_i:best_i + 2]

    def is_old(self, article_id):
        updated = date.fromisoformat(self.articles[article_id]["updated"])
        return (TODAY - updated).days > OLD_AFTER_DAYS

    def label(self, article_id):
        article = self.articles[article_id]
        text = f"{article_id} (updated {article['updated']}"
        if self.is_old(article_id):
            text += ", may be out of date"
        return text + ")"

    def refusal(self, ranking, top_score=0.0, cov=0.0):
        return {
            "answer": I_DONT_KNOW,
            "cited": [],
            "refused": True,
            "ranking": [doc_id for doc_id, _ in ranking],
            "scores": [round(s, 4) for _, s in ranking],
            "top_score": round(top_score, 4),
            "coverage": round(cov, 4),
            "conflict": False,
        }

    def answer(self, question):
        terms = set(tokenize(self.prepare(question)))
        ranking = self.search(question, k=5)
        if not ranking:
            return self.refusal(ranking)

        top_id, top_score = ranking[0]
        cov = self.coverage(terms, top_id)
        if top_score < self.min_score or cov < self.min_coverage:
            return self.refusal(ranking, top_score, cov)

        chosen = {top_id: self.best_sentences(top_id, terms)}
        if not chosen[top_id]:
            # article matched on its title but has no text to answer from
            return self.refusal(ranking, top_score, cov)

        # check for a conflict in the next 2 articles
        for doc_id, score in ranking[1:3]:
            if score < self.min_score or score < self.conflict_ratio * top_score:
                continue
            theirs = self.best_sentences(doc_id, terms)
            if any(sentences_conflict(a, b, terms) for a in chosen[top_id] for b in theirs):
                chosen[doc_id] = theirs

        result = self.refusal(ranking, top_score, cov)
        result["refused"] = False

        if len(chosen) > 1:
            # show both, newest first, with dates
            ids = sorted(chosen, key=lambda d: self.articles[d]["updated"], reverse=True)
            lines = ["The help center is not consistent on this:"]
            for doc_id in ids:
                lines.append(f"- {self.label(doc_id)}: {' '.join(chosen[doc_id])}")
            result["answer"] = "\n".join(lines)
            result["conflict"] = True
        else:
            ids = [top_id]
            text = " ".join(chosen[top_id])
            if self.is_old(top_id):
                text += f" (Note: {self.label(top_id)}.)"
            result["answer"] = text

        result["cited"] = ids
        return result
