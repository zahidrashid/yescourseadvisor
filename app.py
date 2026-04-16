from flask import Flask, request, jsonify
from flask_cors import CORS
import difflib

app = Flask(__name__)
CORS(app)

# Load data
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

DATA = load_data()
LINES = DATA.split("\n")

# Search function
def search_answer(question):
    words = question.lower().split()
    scored = []

    for line in LINES:
        score = 0
        line_lower = line.lower()

        for word in words:
            if word in line_lower:
                score += 2
            else:
                match = difflib.get_close_matches(word, line_lower.split(), n=1, cutoff=0.8)
                if match:
                    score += 1

        if score > 0:
            scored.append((score, line))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = [line for _, line in scored[:5] if line.strip()]

    if results:
        return "• " + "\n• ".join(results)
    else:
        return "Sorry, I couldn't find that information."

# Home route
@app.route("/")
def home():
    return "Bot Running (No API 🚀)"

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("message", "")

    if not question:
        return jsonify({"reply": "Please enter a question."})

    answer = search_answer(question)

    return jsonify({"reply": answer})

# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
