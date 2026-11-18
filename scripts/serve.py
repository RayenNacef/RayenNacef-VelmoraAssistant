import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT) 

from velmora.assistant import Assistant
from velmora.kb import load_articles
from velmora.text import expand_negations

KB_DIR = os.path.join(ROOT, "ai", "kb")
PAGE = os.path.join(ROOT, "ui", "index.html")

MAX_BODY = 10_000
MAX_QUESTION = 500


def why(assistant, result):
    
    score, cov = result["top_score"], result["coverage"]
    if not result["refused"]:
        return (f"Answered: best score {score} ≥ {assistant.min_score} and "
                f"coverage {cov:.0%} ≥ {assistant.min_coverage:.0%}.")
    if not result["ranking"]:
        return "I don't know"
    failed = []
    if score < assistant.min_score:
        failed.append(f"best score {score} is below {assistant.min_score}")
    if cov < assistant.min_coverage:
        failed.append(f"only {cov:.0%} of the question's words (weighted by idf) "
                      f"are in the best article, {assistant.min_coverage:.0%} needed")
    if not failed:
        return "I don't know: the best article has no text to answer from."
    return "I don't know: " + "; ".join(failed) + "."


def ask(assistant, question):
    question = question.strip()[:MAX_QUESTION]
    result = assistant.answer(question)
    ranking = []
    for doc_id, score in zip(result["ranking"], result["scores"]):
        article = assistant.articles[doc_id]
        ranking.append({
            "id": doc_id,
            "title": article["title"],
            "updated": article["updated"],
            "score": score,
            "cited": doc_id in result["cited"],
        })


    searched_as = assistant.prepare(question)
    if searched_as == " ".join(expand_negations(question).split()):
        searched_as = None
    return {
        "question": question,
        "searched_as": searched_as,
        "answer": result["answer"],
        "cited": result["cited"],
        "refused": result["refused"],
        "conflict": result["conflict"],
        "top_score": result["top_score"],
        "coverage": result["coverage"],
        "reason": why(assistant, result),
        "ranking": ranking,
    }


class Handler(BaseHTTPRequestHandler):
    assistant = None

    def send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, code, data):
        self.send(code, "application/json", json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_json(404, {"error": "not found"})
            return
        with open(PAGE, "rb") as f:
            self.send(200, "text/html; charset=utf-8", f.read())

    def do_POST(self):
        if self.path != "/ask":
            self.send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self.send_json(400, {"error": "bad request size"})
            return
        try:
            question = json.loads(self.rfile.read(length) or b"{}")["question"]
            if not isinstance(question, str):
                raise TypeError
        except (ValueError, KeyError, TypeError):
            self.send_json(400, {"error": 'send JSON like {"question": "..."}'})
            return
        self.send_json(200, ask(self.assistant, question))


def main():
    parser = argparse.ArgumentParser(description="Velmora assistant.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    Handler.assistant = Assistant(load_articles(KB_DIR))
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
