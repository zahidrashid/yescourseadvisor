from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ---------------------------
# OpenAI Setup
# ---------------------------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
    except:
        pass
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

    # Group into sections
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

    # Score blocks
    scored = []

    for block in matched_blocks:
        text = " ".join(block).lower()
        text_words = text.split()

        score = 0

        # Unique matches only
        common_words = set(words) & set(text_words)
        score += len(common_words) * 3

        # Heading boost
        heading = block[0].lower()
        for word in words:
            if word in heading:
                score += 5

        if score > 2:  # threshold
            scored.append((score, block))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, block in scored[:3]:
        results.append("\n".join(block))

    if results:
        return "\n\n".join(results)
    else:
        return ""

# ---------------------------
# AI Response Generator
# ---------------------------
def generate_ai_response(question, context):
    try:
        prompt = f"""
You are a helpful course advisor chatbot.

Use the context below to answer the question.
If the answer is not in the context, say:
"I don't have that information right now."

Context:
{context}

Question:
{question}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return "⚠️ AI service is currently unavailable."

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    return "Smart AI Bot Running zahid"

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
