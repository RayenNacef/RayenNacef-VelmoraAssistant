# Failure analysis

Current version (v4): 28/35 correct, 2 wrong answers, 5 false refusals,
5/5 unanswerable refused. Outcomes come from the keyword judge
(`results/eval_results.jsonl`). The causes are my own reading of each
question, its ranking and the article text.

| # | Cause | Questions | Outcome |
|---|---|---|---|
| 1 | Words in no article and no rewrite rule | Q15 | false refusal |
| 2 | Right article, blocked by the checks | Q08 | false refusal |
| 3 | Wrong article ranked 1st | Q02, Q10 | false refusal |
| 4 | Right article, wrong sentence | Q16 | wrong answer |
| 5 | Conflict not detected | Q04 | wrong answer |
| 6 | Needs outside knowledge | Q17 | false refusal |

## 1. Words in no article — Q15
"Can I send back something I **bought by mistake**?" KB-12 is 1st, but
"bought" and "mistake" are in no article. Score 0.17, coverage 0.15, refused.
A rule for this would be written for this one question.

## 2. Blocked by the checks — Q08
"How long do refunds **take**?" KB-15 is 1st (0.27), but "take" is not in
it, coverage 0.44 < 0.5. Loosening the check turns other refusals into
wrong answers (see `--sweep`).

## 3. Wrong article 1st — Q10, Q02
- Q10 (Express cut-off): the old KB-07 wins, "Express" is in its title and
  most sentences. "cut-off time" is missing, refused.
- Q02 (payment methods): KB-15 (refunds, "original payment method") beats
  KB-02. Score 0.22, refused.

*Fix idea:* weight titles more, rank old articles below new ones.

## 4. Wrong sentence — Q16
"Which countries do you deliver to outside France?" Answer: "We do not
ship outside the EU." The list of countries is in another sentence. Same
issue on dev (D02, D09, D12).

## 5. Conflict missed — Q04
"How many days to return an item?" Gives 30 days (KB-12), misses 14 days
for sale items (KB-13). KB-13 ranks too low for the check. Q08 has the same problem.

## 6. Outside knowledge — Q17
"Switzerland" is in no article; knowing it is outside the EU needs
outside knowledge. **I think refusing is acceptable here.**

## What the rewrite fixed (v3 -> v4)

| Question | Rule | Answer now |
|---|---|---|
| Q05 package stuck for a week | package -> parcel, stuck -> not moved, a week -> 7 days | KB-09: contact support after 7 days |
| Q22 broken item, how fast to report | broken -> damaged, how fast -> how long | KB-16: within 48 hours |
| Q23 warranty on batteries | warranty -> guarantee | KB-17: 1 year |
| Q27 can't remember how to get into my profile | -> forgot, login, account | KB-20: Forgot password |
| Q37 opening hours of support | -> available | KB-27: Mon–Fri 9:00–18:00 |

I read all five answers. Nothing got worse. Optimistic: the rules were
written after seeing these failures.

## Dev failures

- D01 password length: words in no article (group 1).
- D02 pickup point delivery time: wrong article (group 3).
- D09, D12: wrong sentence (group 4).
- D19 "recycle a battery" (unanswerable): answered from KB-24, score 0.39.
  The hard case the eval does not have.

## Manual check of the judge

Of the 28 "correct" answers: 27 really answer, Q32 is a lenient pass
(gives the size table, not "M"). Q17 is arguably a good refusal. One
person, one reading.
