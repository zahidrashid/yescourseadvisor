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

COURSE_KEYWORDS = ["diploma", "certificate", "bsc", "ba", "acca", "design", "program"]

# Clean line (remove junk text)
def clean_line(line):
    line = line.strip()
    line = line.replace("art & design:", "")
    line = line.replace("programs:", "")
    return line

# Smart filtered search
def search_courses(question):
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
            if not any(k in line for k in COURSE_KEYWORDS):
                continue

            # remove unwanted lines
            if "located" in line or "level" in line or "block" in line:
                continue

            scored.append((score, clean_line(line)))

    scored.sort(reverse=True)

    results = []
    seen = set()

    for score, line in scored:
        if line and line not in seen:
            results.append(line)
            seen.add(line)

    if results:
        return "• " + "\n• ".join(results[:8])

    return "Sorry, no courses found."

@app.route("/")
def home():
    return "Clean Smart Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("message", "").lower()

    if "course" in question or "program" in question or "design" in question:
        return jsonify({"reply": search_courses(question)})

    return jsonify({"reply": "Please ask about courses or programs."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
