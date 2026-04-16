from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
import difflib

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Load text data
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

DATA = load_data()

# Search context
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

    scored.sort(reverse=True)

    return "\n".join([l for _, l in scored[:8]])

@app.route("/")
def home():
    return "AI Bot Running (No PDFs)"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json["message"]

    context = search_context(question)

    if not context.strip():
        return jsonify({"reply": "I couldn't find that information."})

    prompt = f"""
    You are a helpful college assistant.

    Answer ONLY using the context below.
    If not found, say you don't know.

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

if __name__ == "__main__":
    app.run()    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
