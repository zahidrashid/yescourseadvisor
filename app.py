from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from groq import Groq

app = Flask(__name__)
CORS(app)

# ---------------------------
# Groq Setup
# ---------------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------------------
# Cache Data
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
        print("LOAD ERROR:", e)
    return DATA_CACHE

def clean_text(text):
    return re.sub(r'[^a-z0-9 ]', '', text.lower())

# ---------------------------
# Smart Search
# ---------------------------
def search_answer(question):
    DATA = load_data()
    words = clean_text(question).split()

    lines = DATA.split("\n")

    blocks = []
    current = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if ":" in line and len(line) < 60:
            if current:
                blocks.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append(current)

    scored = []

    for block in blocks:
        text = " ".join(block).lower()
        text_words = text.split()

        score = 0
        common = set(words) & set(text_words)
        score += len(common) * 3

        heading = block[0].lower()
        for w in words:
            if w in heading:
                score += 5

        if score > 2:
            scored.append((score, block))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _, block in scored[:3]:
        results.append("\n".join(block))

    return "\n\n".join(results)

# ---------------------------
# AI Response (Groq)
# ---------------------------
def generate_ai_response(question, context):
    try:
        prompt = f"""
You are a helpful chatbot.

Use the context below to answer the question clearly.
If the answer is not in the context, say:
"I don't have that information."
Keep the answer short and natural.

Context:
{context}

Question:
{question}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # ✅ Updated working model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", e)
        return f"⚠️ Error: {str(e)}"

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    return "Smart AI Bot (Groq) Running New"

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

    # Step 2: Generate AI response
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
