from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import difflib

app = Flask(__name__)
CORS(app)

# Load data
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read().lower()
    except:
        return ""

DATA = load_data()
LINES = DATA.split("\n")

# Synonyms dictionary
SYNONYMS = {
    "course": ["program", "courses", "programs"],
    "it": ["computer", "software", "technology"],
    "fee": ["fees", "cost", "price"],
    "location": ["address", "where", "place"],
    "faculty": ["teacher", "staff", "hod"]
}

# Normalize question
def expand_words(words):
    expanded = set(words)
    for word in words:
        for key, vals in SYNONYMS.items():
            if word == key or word in vals:
                expanded.update(vals)
                expanded.add(key)
    return list(expanded)

# Smart search
def search_answer(question):
    words = question.lower().split()
    words = expand_words(words)

    scored = []

    for line in LINES:
        score = 0

        for word in words:
            if word in line:
                score += 2
            else:
                # fuzzy match
                matches = difflib.get_close_matches(word, line.split(), n=1, cutoff=0.8)
                if matches:
                    score += 1

        if score > 0:
            scored.append((score, line))

    # sort by score
    scored.sort(reverse=True)

    results = [line for score, line in scored[:5]]

    if results:
        return "\n".join(results)

    return "Sorry, I couldn't find that information."

# Intent-based smart replies
def intent_reply(question):
    q = question.lower()

    if "location" in q or "where" in q:
        return search_answer("location")

    if "course" in q or "program" in q:
        return search_answer("programs")

    if "it" in q or "computer" in q:
        return search_answer("computer")

    return None

@app.route("/")
def home():
    return "Ultra Smart Free Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("message", "")

    # Try intent first
    intent = intent_reply(question)
    if intent:
        return jsonify({"reply": intent})

    # Otherwise normal smart search
    answer = search_answer(question)
    return jsonify({"reply": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
