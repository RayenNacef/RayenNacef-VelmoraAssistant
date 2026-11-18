import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  

from velmora import metrics
from velmora.assistant import Assistant
from velmora.kb import load_articles

KB_DIR = os.path.join(ROOT, "ai", "kb")

SCORE_STEPS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
COVERAGE_STEPS = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def load_questions(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run(assistant, questions):
    return [metrics.score_question(q, assistant.answer(q["question"])) for q in questions]


def print_summary(s):
    n, u, a = s["answerable"], s["unanswerable"], s["answered"]
    print(f"Questions: {s['questions']} ({n} answerable, {u} unanswerable)")
    print()
    print("Retrieval (answerable questions)")
    for k in (1, 3, 5):
        print(f"recall@{k}: {s[f'recall@{k}']:.3f}")
    print("==========")
    print("Answerable questions (keyword judge, see README for its limits)")
    print(f"correct answers:{s['correct']:>2}/{n}  ({s['correct_share']:.1%})")
    print(f"wrong answers:  {s['incorrect']:>2}/{n}  (answered, keywords missing)")
    print(f"false refusals: {s['false_refusals']:>2}/{n}  (said \"I don't know\")")
    print("==========")
    print("Unanswerable questions")
    print(f"correct refusals:{s['correct_refusals']:>2}/{u}")
    print(f"answered anyway:{s['wrongly_answered']:>2}/{u}")
    print("==========")
    print(f"Citations (the {a} answered answerable questions)")
    print(f"cites at least one gold article: {s['cited_any_gold']:>2}/{a}")
    print(f"cites only gold articles: {s['cited_only_gold']:>2}/{a}")
    print(f"cites every gold article: {s['cited_all_gold']:>2}/{a}")


def print_sweep(assistant, questions, name, steps):
    # move one threshold, keep the other one at its default
    original = getattr(assistant, name)
    print(f"\nThreshold table: {name} (other threshold at its default)")
    print(f"  {name:>12} | correct | wrong answer | false refusal | correct refusal")
    try:
        for value in steps:
            setattr(assistant, name, value)
            s = metrics.summarize(run(assistant, questions))
            n, u = s["answerable"], s["unanswerable"]
            marker = "  <- default" if abs(value - original) < 1e-9 else ""
            print(f"  {value:>12.2f} | {s['correct']:>3}/{n:<3} | {s['incorrect']:>6}/{n:<5} | "
                  f"{s['false_refusals']:>7}/{n:<5} | {s['correct_refusals']:>7}/{u}{marker}")
    finally:
        setattr(assistant, name, original)


def main():
    parser = argparse.ArgumentParser(description="Evaluate the Velmora help-center assistant.")
    parser.add_argument("--data", default=os.path.join(ROOT, "ai", "eval.jsonl"))
    parser.add_argument("--out", default=os.path.join(ROOT, "results", "eval_results.jsonl"))
    parser.add_argument("--sweep", action="store_true", help="also print the threshold tables")
    args = parser.parse_args()

    assistant = Assistant(load_articles(KB_DIR))
    questions = load_questions(args.data)
    rows = run(assistant, questions)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print_summary(metrics.summarize(rows))
    print(f"\nPer-question results written to {os.path.relpath(args.out)}")

    if args.sweep:
        print_sweep(assistant, questions, "min_score", SCORE_STEPS)
        print_sweep(assistant, questions, "min_coverage", COVERAGE_STEPS)


if __name__ == "__main__":
    main()
