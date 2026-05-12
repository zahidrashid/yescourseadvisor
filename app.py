from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from difflib import SequenceMatcher
from groq import Groq

app = Flask(__name__)
CORS(app)

# ==========================================
# GROQ SETUP
# ==========================================
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

# ==========================================
# CACHE DATA
# ==========================================
DATA_CACHE = ""
LAST_MODIFIED = 0

def load_data():
    global DATA_CACHE, LAST_MODIFIED

    try:
        mtime = os.path.getmtime("data.txt")

        # Reload only if file changed
        if mtime != LAST_MODIFIED:
            with open("data.txt", "r", encoding="utf-8") as f:
                DATA_CACHE = f.read()

            LAST_MODIFIED = mtime

    except Exception as e:
        print("LOAD ERROR:", e)

    return DATA_CACHE

# ==========================================
# CLEAN TEXT
# ==========================================
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return text

# ==========================================
# SIMILARITY
# ==========================================
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# ==========================================
# SMART SEARCH
# ==========================================
def search_answer(question):
    DATA = load_data()

    if not DATA:
        return ""

    question_clean = clean_text(question)

    # Split using blank lines
    sections = re.split(r'\n\s*\n', DATA)

    scored = []

    for section in sections:

        section_clean = clean_text(section)

        score = 0

        q_words = question_clean.split()
        s_words = section_clean.split()

        # Flexible keyword matching
        for qw in q_words:
            for sw in s_words:

                if qw == sw:
                    score += 5

                elif qw in sw or sw in qw:
                    score += 2

        # Similarity score
        sim = similarity(question_clean, section_clean)
        score += sim * 10

        # Bonus for programme names
        if "acca" in question_clean and "acca" in section_clean:
            score += 15

        if score > 2:
            scored.append((score, section))

    # Sort highest score first
    scored.sort(reverse=True, key=lambda x: x[0])

    # Get top sections
    top_sections = []

    for score, section in scored[:8]:
        top_sections.append(section)

    return "\n\n".join(top_sections)

# ==========================================
# AI RESPONSE
# ==========================================
def generate_ai_response(question, context):

    if not context.strip():
        return "I don't have that information."

    try:

        prompt = f"""
You are a college chatbot assistant.

IMPORTANT RULES:
- Answer ONLY using the provided context.
- Do NOT use outside knowledge.
- Do NOT add extra information.
- If information is missing, say:
  "I don't have that information."
- Keep answers short, clear, and human-like.

CONTEXT:
{context}

QUESTION:
{question}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=300,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful college assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response.choices[0].message.content.strip()

        if not answer:
            return "I don't have that information."

        return answer

    except Exception as e:
        print("GROQ ERROR:", e)
        return "Server error. Please try again later."

# ==========================================
# HOME
# ==========================================
@app.route("/")
def home():
    return "Smart AI College Chatbot Running"

# ==========================================
# HEALTH CHECK
# ==========================================
@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })

# ==========================================
# CHAT API
# ==========================================
@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        if not data:
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

        # Step 1: Search data
        context = search_answer(question)

        # Step 2: Generate AI answer
        answer = generate_ai_response(question, context)

        return jsonify({
            "reply": answer,
            "status": "success"
        })

    except Exception as e:
        print("CHAT ERROR:", e)

        return jsonify({
            "reply": "Server error.",
            "status": "error"
        })

# ==========================================
# RUN SERVER
# ==========================================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True
    )
