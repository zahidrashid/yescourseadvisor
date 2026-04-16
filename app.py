from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ✅ OpenAI client
client = OpenAI(api_key=os.environ.get("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"))

# ✅ Load TXT data
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "No data available."

DATA = load_data()

# ✅ Smart context search
def search_context(question):
    chunks = DATA.split("\n")
    relevant = []

    for chunk in chunks:
        if any(word in chunk.lower() for word in question.lower().split()):
            relevant.append(chunk)

    return "\n".join(relevant[:10])  # limit

@app.route("/")
def home():
    return "AI TXT Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        question = request.json.get("message", "")

        if not question:
            return jsonify({"reply": "Please ask a question."})

        context = search_context(question)

        prompt = f"""
        You are a helpful college assistant.
        Answer ONLY using the context below.
        If answer is not found, say "Information not available".

        CONTEXT:
        {context}

        Question: {question}
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
