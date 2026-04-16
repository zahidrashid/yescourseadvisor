from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ✅ OpenAI client
client = OpenAI(api_key=os.environ.get("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"))

# ✅ Load TXT data safely
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "No data available."

DATA = load_data()

# ✅ Smart context search (basic filtering)
def search_context(question):
    chunks = DATA.split("\n")
    relevant = []

    for chunk in chunks:
        if any(word in chunk.lower() for word in question.lower().split()):
            relevant.append(chunk)

    return "\n".join(relevant[:15])  # slightly more context

@app.route("/")
def home():
    return "AI TXT Bot Running"

# ✅ Chat endpoint (AI powered)
@app.route("/chat", methods=["POST"])
def chat():
    try:
        question = request.json.get("message", "").strip()

        if not question:
            return jsonify({"reply": "Please ask a question."})

        context = search_context(question)

        prompt = f"""
You are a professional assistant for YES International College.

Instructions:
- Answer clearly and professionally
- Use bullet points where helpful
- Only use the provided context
- If answer is not found, say "Information not available"

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
        print("ERROR:", str(e))
        return jsonify({"reply": f"Server Error: {str(e)}"})

# ✅ Required for Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
