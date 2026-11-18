# Design note: Velmora help-center assistant

## 1. The need and my assumptions

The team wants answers it can trust and measure. So the real deliverable
is an honest evaluation, and an assistant that says "I don't know"
instead of guessing.
- A wrong answer costs more than "I don't know", which only sends the
  customer to a human.
- "Today" is 1 July 2026, so the summer sale rules (KB-13) apply.

## 2. Architecture, and two choices I hesitated over

Question -> rewrite customer words (package -> parcel) -> TF-IDF + cosine
over 30 articles -> two checks (score ≥ 0.25, coverage ≥ 0.5) -> best
sentence + next one, with cited ids -> conflict check on ranks 2–3.
Standard library only, deterministic. `python3 scripts/run_eval.py` prints
recall@k, correct / wrong / false refusals, correct refusals and citation
checks. `python3 scripts/serve.py` shows the same on a local page.

### TF-IDF vs. Embeddings

Synonyms and differences in wording were among the main causes of retrieval failures. Although I have experience with embeddings and considered using local semantic search, I decided against introducing an embedding model for this assignment.

Embeddings would require an additional library and a pre-trained model to be downloaded and loaded, introducing setup requirements and inference overhead. This would also make the solution less lightweight and harder to reproduce.

Given the small knowledge base (30 short articles), I expected limited benefits compared with a simpler, domain-specific solution. I therefore chose TF-IDF with a curated query-rewriting table to handle common synonyms and variations in wording.

This approach keeps the system lightweight, deterministic and easy to run, while improving lexical matching without introducing additional model dependencies.

*Show both articles or trust the newest.* The newest is not always right:
KB-13 is a sale rule, not a replacement for KB-12. So both are shown,
newest first, with dates; anything older than 2 years is marked "may be
out of date".

## 3. What I tested, and what I could not

58 unit tests: metrics, judge, outcomes, citations, tokenizing, rewrite
rules, ranking, refusals, conflicts, web page.

Thresholds were set on 20 dev questions I wrote, not on eval. v1 (22/35,
5/5 refusals) is the honest, blind number. v4 (28/35) came after reading eval
failures, so it is optimistic: the rewrite changes 7 eval questions, only
2 dev ones.

Main finding: dev cannot separate thresholds that give 18/35 to 28/35 on
eval. I could not test on real customer questions, and 5 unanswerable
questions move the refusal rate in 20-point steps.

## 4. What I cut

Optional items chosen: **conflict detection** and **the threshold table**
(`--sweep`).
- Embeddings: extra dependency and model, small expected gain (section 2).
- Bigrams: tried; they hid the KB-06/KB-07 conflict on Q03.
- LLM: needs a key or a model, and can invent answers.
- BM25, and a built-in judge check.

## 5. How I used AI

I used AI as a supporting tool:

- **Technical exploration:** I used it to compare TF-IDF, BM25 and local embeddings, understand their benefits and limitations.
- **Query rewriting:** I used AI to help identify possible synonyms and alternative customer expressions and suggest rewriting rules. I reviewed and adapted these rules before including them in the implementation.
- **Documentation:** I used AI to help organize and format some README tables and improve the clarity of the documentation.
- **Testing:** I used it to suggest additional test cases and edge cases that I might have overlooked, then reviewed and adapted them to the actual system behavior.

AI suggestions were treated as recommendations, not decisions. I remained responsible for the implementation, evaluating the trade-offs, validating the results and deciding which suggestions were appropriate for the project.
## 6. With one more day

**Data augmentation:** expand the evaluation set with paraphrased
questions, synonyms, ambiguous queries and hard unanswerable questions, to test retrieval beyond the original examples, set the thresholds properly and test the rewrite table on wording I did not write it for. Then same-category conflict checks.

## Limits

**Invented answers.** Answers are copied, so no fact is made up. The risk
is a true sentence that does not answer (Q04, Q16, dev D19). *Next:*
refuse when the chosen sentence scores too low.

**Old or disagreeing articles.** KB-06 vs KB-07 is caught (Q03, Q18).
KB-13 is missed (Q04, Q08): it ranks too low. *Next:* compare
same-category articles; retire KB-07.

**No-answer questions.** 5/5 refused (best score 0.14), but they are easy.
Cost: 5 false refusals, mostly words in no article. *Next:* log refused
questions and grow the table from them.
