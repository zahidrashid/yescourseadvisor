from flask import Flask, request, jsonify
from flask_cors import CORS
import os

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

# 🔥 SMART SEARCH (handles large data cleanly)
def search_answer(question):
    question = question.lower()
    lines = DATA.split("\n")

    matched_blocks = []
    current_block = []

    # Step 1: Group into sections
    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Detect headings (like "Location:", "Diploma Programs:")
        if ":" in line and len(line) < 60:
            if current_block:
                matched_blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        matched_blocks.append(current_block)

    # Step 2: Score blocks based on question
    scored = []
    words = question.split()

    for block in matched_blocks:
        text = " ".join(block).lower()
        score = sum(1 for word in words if word in text)

        if score > 0:
            scored.append((score, block))

    # Step 3: Sort best matches
    scored.sort(key=lambda x: x[0], reverse=True)

    # Step 4: Return top results
    results = []
    for _, block in scored[:3]:
        results.append("\n".join(block))

    if results:
        return "\n\n".join(results)
    else:
        return "❓ Sorry, I couldn't find that information."

# Home route
@app.route("/")
def home():
    return "Smart Bot Running (No API Zahid 🚀)"

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
