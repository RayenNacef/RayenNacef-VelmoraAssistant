import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)  

from velmora.assistant import Assistant
from velmora.kb import load_articles

KB_DIR = os.path.join(ROOT, "ai", "kb")


def main():
    if len(sys.argv) < 2:
        print('usage: python3 ask.py "your question"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    result = Assistant(load_articles(KB_DIR)).answer(question)

    print(result["answer"])
    if result["cited"]:
        print("\nSources:", ", ".join(result["cited"]))
    print(f"\n[top score {result['top_score']}, coverage {result['coverage']}, "
          f"ranking {result['ranking']}]")


if __name__ == "__main__":
    main()
