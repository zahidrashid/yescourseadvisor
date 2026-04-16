from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# ✅ Load data
def load_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read().lower()
    except:
        return ""

DATA = load_data()

# ✅ Smart search function
def search_answer(question):
    question = question.lower()
    lines = DATA.split("\n")

    matches = []

    for line in lines:
        if any(word in line for word in question.split()):
            matches.append(line)

    if matches:
        return "\n".join(matches[:5])
    
    return "Sorry, I couldn't find that information."

@app.route("/")
def home():
    return "Free College Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("message", "")
    answer = search_answer(question)

    return jsonify({"reply": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
