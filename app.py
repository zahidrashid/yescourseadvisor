from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import difflib
from google import genai

app = Flask(__name__)
CORS(app)

# ✅ Google GenAI client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

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
    return "AI Bot Running (Smart yes college 🚀)"

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    try:
        question = request.json.get("message", "")

        if not question:
            return jsonify({"reply": "Please enter a question."})

        context = search_context(question)

        # ✅ Smart fallback (always answer)
        if not context.strip():
            context = DATA[:2000]

        # ✅ Improved prompt
        prompt = f"""
You are a helpful assistant for YES International College.

Answer clearly and naturally using the context.
You can summarize or list programs if needed.

If the question is about courses, list relevant programs.

CONTEXT:
{context}

QUESTION:
{question}
"""

        # ✅ Gemini API call
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        # ✅ SAFE RESPONSE PARSING (FIXED ERROR)
        try:
            reply = response.candidates[0].content.parts[0].text
        except:
            reply = "I couldn't generate a response."

        return jsonify({"reply": reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({"reply": "⚠️ Server error. Please try again."})

# Run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
