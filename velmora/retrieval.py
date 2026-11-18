import math
from collections import Counter


class TfidfIndex:
    def __init__(self, docs):
        self.ids = [doc_id for doc_id, _ in docs]
        n = len(docs)

        df = Counter()
        for _, tokens in docs:
            df.update(set(tokens))

        self.idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        #word in no article gets the highest idf
        self.unknown_idf = math.log(n + 1) + 1

        self.vectors = [self.vectorize(tokens) for _, tokens in docs]

    def get_idf(self, term):
        return self.idf.get(term, self.unknown_idf)

    def vectorize(self, tokens):
        tf = Counter(tokens)
        vec = {t: count * self.get_idf(t) for t, count in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm == 0:
            return {}
        return {t: v / norm for t, v in vec.items()}

    def search(self, query_tokens, k=5):
        # unknown query words stay in the query norm, so they lower the score
        q = self.vectorize(query_tokens)
        if not q:
            return []
        scores = []
        for doc_id, vec in zip(self.ids, self.vectors):
            score = sum(w * vec.get(t, 0.0) for t, w in q.items())
            if score > 0:
                scores.append((doc_id, score))
        # sort by score then by id so ties always come out the same
        scores.sort(key=lambda pair: (-pair[1], pair[0]))
        return scores[:k]
