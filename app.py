from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# ---------------------------
# Google Gemini Setup
# ---------------------------
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# ---------------------------
# Cache Data (FAST)
# ---------------------------
DATA_CACHE = ""
LAST_MODIFIED = 0

def load_data():
    global DATA_CACHE, LAST_MODIFIED
    try:
        mtime = os.path.getmtime("data.txt")
        if mtime != LAST_MODIFIED:
            with open("data.txt", "r", encoding="utf-8") as f:
                DATA_CACHE = f.read()
            LAST_MODIFIED = mtime
    except Exception as e:
        print("LOAD DATA ERROR:", e)
    return DATA_CACHE

def clean_text(text):
    return re.sub(r'[^a-z0-9 ]', '', text.lower())

# ---------------------------
# Smart Search Engine
# ---------------------------
def search_answer(question):
    DATA = load_data()
    question_clean = clean_text(question)
    words = question_clean.split()

    lines = DATA.split("\n")

    matched_blocks = []
    current_block = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # detect heading
        if ":" in line and len(line) < 60:
            if current_block:
                matched_blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)

    if current_block:
        matched_blocks.append(current_block)

    scored = []

    for block in matched_blocks:
        text = " ".join(block).lower()
        text_words = text.split()

        score = 0

        common_words = set(words) & set(text_words)
        score += len(common_words) * 3

        # heading boost
        heading = block[0].lower()
        for word in words:
            if word in heading:
                score += 5

        if score > 2:
            scored.append((score, block))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, block in scored[:3]:
        results.append("\n".join(block))

    return "\n\n".join(results)

# ---------------------------
# AI Response (Gemini)
# ---------------------------
def generate_ai_response(question, context):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
You are a helpful chatbot.

Use the context below to answer the question clearly.
If the answer is not in the context, say:
"I don't have that information right now."

Context:
{context}

Question:
{question}
"""

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        print("GEMINI ERROR:", e)
        return f"⚠️ Error: {str(e)}"

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    return "Smart AI Bot (Gemini) Running newww"

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

    # Step 1: Search your data
    context = search_answer(question)

    # Step 2: Generate AI answer
    answer = generate_ai_response(question, context)

    return jsonify({
        "reply": answer,
        "status": "success"
    })

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
