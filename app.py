from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
import difflib

app = Flask(__name__)
CORS(app)

# OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Load text data
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

DATA = load_data()

# Search relevant context
def search_context(question):
    lines = DATA.split("\n")
    words = question.lower().split()
    scored = []

    for line in lines:
        score = 0
        line_lower = line.lower()

        for word in words:
            if word in line_lower:
                score += 2
            else:
                match = difflib.get_close_matches(word, line_lower.split(), n=1, cutoff=0.8)
                if match:
                    score += 1

        if score > 1:
            scored.append((score, line))

    scored.sort(key=lambda x: x[0], reverse=True)

    return "\n".join([l for _, l in scored[:8]])

# Home route
@app.route("/")
def home():
    return "AI Bot Running 🚀"

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    try:
        question = request.json.get("message", "")

        if not question:
            return jsonify({"reply": "Please enter a question."})

        context = search_context(question)

        if not context.strip():
            return jsonify({"reply": "I couldn't find that information."})

        prompt = f"""
You are a helpful college assistant.

Answer ONLY using the context below.
If the answer is not found, say:
"I couldn't find that information."

Keep the answer clear and short.

CONTEXT:
{context}

QUESTION:
{question}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        reply = response.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

# Run app (for Render)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
