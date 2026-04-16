from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Load your data
with open("data.txt", "r", encoding="utf-8") as f:
    DATA = f.read()

@app.route("/")
def home():
    return "AI College Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json["message"]

    prompt = f"""
    You are a college assistant.
    Answer only using the data below.

    DATA:
    {DATA}

    Question: {question}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    reply = response.choices[0].message.content

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
