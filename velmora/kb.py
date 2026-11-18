import os


def parse_article(raw):
    lines = raw.strip().splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("article has no header")

    article = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        key, _, value = lines[i].partition(":")
        article[key.strip()] = value.strip()
        i += 1

    if "id" not in article:
        raise ValueError("article header has no id")

    #body without the markdown headings
    body = [line.strip() for line in lines[i + 1:]]
    body = [line for line in body if line and not line.startswith("#")]
    article["body"] = " ".join(body)
    return article


def load_articles(kb_dir):
    articles = []
    for name in sorted(os.listdir(kb_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(kb_dir, name), encoding="utf-8") as f:
            articles.append(parse_article(f.read()))
    return articles
