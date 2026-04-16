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
LOCATION_KEYWORDS = ["located", "kuala lumpur", "block", "jalan"]
FACILITY_KEYWORDS = ["level", "facility", "department"]

# Clean text
def clean_line(line):
    return line.strip()

# Generic search
def search_filtered(question, keywords):
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
            if not any(k in line for k in keywords):
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
        return "• " + "\n• ".join(results[:5])

    return "Sorry, I couldn't find that information."

@app.route("/")
def home():
    return "Smart Multi Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("message", "").lower()

    # 📚 Courses
    if "course" in question or "program" in question:
        return jsonify({"reply": search_filtered(question, COURSE_KEYWORDS)})

    # 📍 Location
    if "location" in question or "where" in question or "address" in question:
        return jsonify({"reply": search_filtered(question, LOCATION_KEYWORDS)})

    # 🏫 Facilities
    if "facility" in question or "class" in question:
        return jsonify({"reply": search_filtered(question, FACILITY_KEYWORDS)})

    # fallback
    return jsonify({"reply": "Please ask about courses, location, or facilities."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
