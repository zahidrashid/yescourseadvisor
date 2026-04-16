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

# Keywords for filtering
COURSE_KEYWORDS = ["diploma", "certificate", "bsc", "ba", "acca", "program"]
LOCATION_KEYWORDS = ["located", "level", "block", "kuala lumpur"]

# Smarter search with filter
def search_answer(question, filter_type=None):
    words = question.lower().split()
    scored = []

    for line in LINES:
        score = 0

        for word in words:
            if word in line:
                score += 2
            else:
                matches = difflib.get_close_matches(word, line.split(), n=1, cutoff=0.8)
                if matches:
                    score += 1

        if score > 0:
            # Apply filter
            if filter_type == "courses":
                if not any(k in line for k in COURSE_KEYWORDS):
                    continue

            if filter_type == "location":
                if not any(k in line for k in LOCATION_KEYWORDS):
                    continue

            scored.append((score, line))

    scored.sort(reverse=True)
    results = [line for score, line in scored[:8]]

    if results:
        return "\n".join(results)

    return "Sorry, I couldn't find that information."

# Intent detection
def intent_reply(question):
    q = question.lower()

    if "course" in q or "program" in q:
        return search_answer(q, "courses")

    if "location" in q or "where" in q:
        return search_answer(q, "location")

    return None

@app.route("/")
def home():
    return "Smart Filtered Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("message", "")

    # Intent-based filtered response
    intent = intent_reply(question)
    if intent:
        return jsonify({"reply": intent})

    # fallback
    answer = search_answer(question)
    return jsonify({"reply": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
