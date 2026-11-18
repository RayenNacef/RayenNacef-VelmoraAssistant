import re


STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "from", "by", "with", "about", "as", "into", "is", "are", "was",
    "were", "be", "been", "am", "do", "does", "did", "can", "could", "will",
    "would", "should", "may", "might", "must", "i", "me", "my", "you", "your",
    "we", "us", "our", "it", "its", "this", "that", "there", "what", "which",
    "who", "when", "where", "why", "how", "long", "much", "many", "have", "has",
    "had", "any", "some", "so", "yes", "than", "then", "also",
    "after", "before", "same", "anymore", "get", "need",
}

DOUBLE_ENDINGS = ("bb", "dd", "gg", "mm", "nn", "pp", "rr", "tt")


def stem(word):
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 5 and word.endswith("ed"):
        word = word[:-2]
        if word.endswith(DOUBLE_ENDINGS):
            word = word[:-1]
    elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us")):
        word = word[:-1]

    if len(word) > 3 and word.endswith("e"):  # receive, received = receiv
        word = word[:-1]
    return word


def expand_negations(text):
    # otherwise "can't" becomes "can" + "t" and the "not" is lost
    text = text.lower().replace("’", "'")
    text = re.sub(r"\bcannot\b", "can not", text)
    text = re.sub(r"\bcan't\b", "can not", text)
    text = re.sub(r"\bwon't\b", "will not", text)
    text = re.sub(r"n't\b", " not", text)
    return text


def tokenize(text):
    tokens = []
    for word in re.findall(r"[a-z0-9]+", expand_negations(text)):
        if word in STOPWORDS:
            continue
        word = stem(word)
        if word not in STOPWORDS:
            tokens.append(word)
    return tokens


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]
