from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import os
import re
from difflib import SequenceMatcher

# ======================================================
# FLASK SETUP
# ======================================================

app = Flask(__name__)
CORS(app)

# ======================================================
# GROQ SETUP
# ======================================================

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

# ======================================================
# CACHE
# ======================================================

DATA_CACHE = ""
LAST_MODIFIED = 0

# ======================================================
# LOAD DATA
# ======================================================

def load_data():
    global DATA_CACHE, LAST_MODIFIED

    try:
        file_path = "data.txt"

        mtime = os.path.getmtime(file_path)

        # Reload only if updated
        if mtime != LAST_MODIFIED:

            with open(file_path, "r", encoding="utf-8") as f:
                DATA_CACHE = f.read()

            LAST_MODIFIED = mtime

    except Exception as e:
        print("LOAD ERROR:", e)

    return DATA_CACHE

# ======================================================
# CLEAN TEXT
# ======================================================

def clean_text(text):

    text = text.lower()

    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()

# ======================================================
# SIMILARITY
# ======================================================

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# ======================================================
# SEARCH FUNCTION
# ======================================================

def search_answer(question):

    DATA = load_data()

    if not DATA:
        return ""

    question_clean = clean_text(question)

    # Split sections using blank lines
    sections = re.split(r'\n\s*\n', DATA)

    # ==================================================
    # SPECIAL DIRECT MATCHES
    # ==================================================

    direct_keywords = [
        "detailed subject structure",
        "subject structure",
        "all subjects",
        "semester subjects",
        "full subjects"
    ]

    for keyword in direct_keywords:

        if keyword in question_clean:

            for section in sections:

                if "detailed subject structure" in clean_text(section):
                    return section

    # ==================================================
    # NORMAL SEARCH
    # ==================================================

    scored = []

    for section in sections:

        section_clean = clean_text(section)

        score = 0

        q_words = question_clean.split()
        s_words = section_clean.split()

        # Exact + partial matching
        for qw in q_words:

            for sw in s_words:

                # Exact match
                if qw == sw:
                    score += 5

                # Partial match
                elif qw in sw or sw in qw:
                    score += 2

        # Similarity boost
        sim = similarity(question_clean, section_clean)

        score += sim * 10

        # ACCA bonus
        if "acca" in question_clean and "acca" in section_clean:
            score += 20

        # Subject bonus
        if "subject" in question_clean and "subject" in section_clean:
            score += 10

        if score > 2:
            scored.append((score, section))

    # Sort by highest score
    scored.sort(reverse=True, key=lambda x: x[0])

    # Top matches
    top_sections = []

    for score, section in scored[:20]:
        top_sections.append(section)

    return "\n\n".join(top_sections)

# ======================================================
# AI RESPONSE
# ======================================================

def generate_ai_response(question, context):

    if not context.strip():
        return "I don't have that information."

    try:

        prompt = f"""
You are a helpful college chatbot assistant.

STRICT RULES:
- Answer ONLY using the provided context.
- Do NOT use outside knowledge.
- Do NOT invent information.
- If the information is missing, say:
  "I don't have that information."
- Keep answers clear, natural, and accurate.

CONTEXT:
{context}

QUESTION:
{question}
"""

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            temperature=0,

            max_tokens=500,

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

# ======================================================
# HOME ROUTE
# ======================================================

@app.route("/")
def home():

    return "Smart AI College Chatbot Running"

# ======================================================
# HEALTH CHECK
# ======================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok"
    })

# ======================================================
# CHAT ROUTE
# ======================================================

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

        # ==================================================
        # SEARCH CONTEXT
        # ==================================================

        context = search_answer(question)

        print("\n==============================")
        print("QUESTION:")
        print(question)

        print("\nCONTEXT:")
        print(context)
        print("==============================\n")

        # ==================================================
        # AI ANSWER
        # ==================================================

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

# ======================================================
# RUN SERVER
# ======================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True
    )
