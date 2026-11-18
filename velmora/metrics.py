CORRECT = "correct"
INCORRECT = "incorrect"                
FALSE_REFUSAL = "false_refusal"        # answerable but "I don't know"
CORRECT_REFUSAL = "correct_refusal"
WRONGLY_ANSWERED = "wrongly_answered"  #unanswerable but answered


def normalize(text):
    return " ".join(text.lower().split())


def recall_at_k(ranked_ids, gold_ids, k):
    if not gold_ids:
        return None
    top = set(ranked_ids[:k])
    return len(top & set(gold_ids)) / len(set(gold_ids))


def keywords_found(answer, keywords):
    
    if not answer or not keywords:
        return False
    text = normalize(answer)
    return all(normalize(k) in text for k in keywords)


def citation_checks(cited, gold):
    cited, gold = set(cited), set(gold)
    return {
        "cited_any_gold": bool(cited & gold),
        "cited_only_gold": bool(cited) and cited <= gold,
        "cited_all_gold": bool(gold) and gold <= cited,
    }


def score_question(item, result):
    gold = item.get("source_articles") or []
    answerable = item["answerable"]
    refused = result["refused"]

    row = {
        "id": item["id"],
        "question": item["question"],
        "answerable": answerable,
        "refused": refused,
        "answer": result["answer"],
        "cited": result["cited"],
        "gold_articles": gold,
        "ranking": result["ranking"],
        "top_score": result["top_score"],
        "coverage": result["coverage"],
        "conflict": result["conflict"],
    }
    for k in (1, 3, 5):
        row[f"recall@{k}"] = recall_at_k(result["ranking"], gold, k)

    keywords_ok = None
    if answerable and refused:
        outcome = FALSE_REFUSAL
    elif answerable:
        keywords_ok = keywords_found(result["answer"], item["answer_keywords"])
        outcome = CORRECT if keywords_ok else INCORRECT
    elif refused:
        outcome = CORRECT_REFUSAL
    else:
        outcome = WRONGLY_ANSWERED

    row["outcome"] = outcome
    row["keywords_ok"] = keywords_ok
    row["correct"] = outcome in (CORRECT, CORRECT_REFUSAL)

    # citations only make sense for answered, answerable questions
    if answerable and not refused:
        row.update(citation_checks(result["cited"], gold))
    else:
        row.update({"cited_any_gold": None, "cited_only_gold": None, "cited_all_gold": None})
    return row


def summarize(rows):
    answerable = [r for r in rows if r["answerable"]]
    unanswerable = [r for r in rows if not r["answerable"]]
    answered = [r for r in answerable if not r["refused"]]

    def count(group, outcome):
        return sum(1 for r in group if r["outcome"] == outcome)

    def mean(values):
        return sum(values) / len(values) if values else 0.0

    s = {
        "questions": len(rows),
        "answerable": len(answerable),
        "unanswerable": len(unanswerable),
        "correct": count(answerable, CORRECT),
        "incorrect": count(answerable, INCORRECT),
        "false_refusals": count(answerable, FALSE_REFUSAL),
        "correct_refusals": count(unanswerable, CORRECT_REFUSAL),
        "wrongly_answered": count(unanswerable, WRONGLY_ANSWERED),
        "answered": len(answered),
        "cited_any_gold": sum(1 for r in answered if r["cited_any_gold"]),
        "cited_only_gold": sum(1 for r in answered if r["cited_only_gold"]),
        "cited_all_gold": sum(1 for r in answered if r["cited_all_gold"]),
    }

    if s["correct"] + s["incorrect"] + s["false_refusals"] != s["answerable"]:
        raise ValueError("answerable outcomes do not add up")
    if s["correct_refusals"] + s["wrongly_answered"] != s["unanswerable"]:
        raise ValueError("unanswerable outcomes do not add up")

    for k in (1, 3, 5):
        s[f"recall@{k}"] = mean([r[f"recall@{k}"] for r in answerable])
    s["correct_share"] = s["correct"] / len(answerable) if answerable else 0.0
    return s
