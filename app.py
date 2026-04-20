from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# ---------------------------
# Load & Clean Data
# ---------------------------
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def clean_text(text):
    return re.sub(r'[^a-z0-9 ]', '', text.lower())

# ---------------------------
# Smart Search Engine
# ---------------------------
def search_answer(question):
    DATA = load_data()  # 🔥 always reload latest data
    question_clean = clean_text(question)
    words = question_clean.split()

    lines = DATA.split("\n")

    matched_blocks = []
    current_block = []

    # Step 1: Group into sections
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if ":" in line and len(line) < 60:
            if current_block:
                matched_blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        matched_blocks.append(current_block)

    # Step 2: Score blocks (IMPROVED)
    scored = []

    for block in matched_blocks:
        text = " ".join(block).lower()
        text_words = text.split()

        score = 0

        for word in words:
            if word in text_words:
                score += 3  # exact word match

            elif word in text:
                score += 1  # partial match

        # 🔥 Boost if keyword appears in heading
        heading = block[0].lower()
        for word in words:
            if word in heading:
                score += 5

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

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    return "Smart Yes Bot Running 🚀"

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({
            "reply": "Please send a message.",
            "status": "error"
        })

    question = data.get("message", "").strip()

    if not question:
        return jsonify({
            "reply": "Please enter a question.",
            "status": "error"
        })

    answer = search_answer(question)

    return jsonify({
        "reply": answer,
        "status": "success"
    })

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
