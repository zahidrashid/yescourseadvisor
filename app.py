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
# MULTIPLE FILE CACHE SYSTEM
# ==========================================
DATA_CACHE = {}
LAST_MODIFIED = {}

# Folder containing txt files
DATA_FOLDER = "data"

def load_all_data():

    global DATA_CACHE
    global LAST_MODIFIED

    combined_data = ""

    try:

        # Create folder automatically
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)

        # Read all txt files
        for filename in os.listdir(DATA_FOLDER):

            if filename.endswith(".txt"):

                filepath = os.path.join(DATA_FOLDER, filename)

                mtime = os.path.getmtime(filepath)

                # Reload only if modified
                if (
                    filename not in LAST_MODIFIED
                    or LAST_MODIFIED[filename] != mtime
                ):

                    with open(filepath, "r", encoding="utf-8") as f:
                        DATA_CACHE[filename] = f.read()

                    LAST_MODIFIED[filename] = mtime

                    print(f"Loaded: {filename}")

                combined_data += "\n\n" + DATA_CACHE.get(filename, "")

    except Exception as e:
        print("LOAD ERROR:", e)

    return combined_data

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

    DATA = load_all_data()

    if not DATA:
        return ""

    question_clean = clean_text(question)

    # Split sections using blank lines
    sections = re.split(r'\n\s*\n', DATA)

    scored = []

    for section in sections:

        section_clean = clean_text(section)

        score = 0

        q_words = question_clean.split()
        s_words = section_clean.split()

        # ==================================
        # KEYWORD MATCHING
        # ==================================
        for qw in q_words:

            for sw in s_words:

                # Exact match
                if qw == sw:
                    score += 5

                # Partial match
                elif qw in sw or sw in qw:
                    score += 2

        # ==================================
        # SIMILARITY SCORE
        # ==================================
        sim = similarity(question_clean, section_clean)

        score += sim * 10

        # ==================================
        # IMPORTANT KEYWORD BONUS
        # ==================================
        keywords = [
            "acca",
            "registry",
            "diploma",
            "certificate",
            "english",
            "hotel",
            "software",
            "business",
            "culinary",
            "visa",
            "loan"
        ]

        for keyword in keywords:

            if keyword in question_clean and keyword in section_clean:
                score += 10

        # ==================================
        # SAVE GOOD RESULTS
        # ==================================
        if score > 2:
            scored.append((score, section))

    # ======================================
    # SORT BEST RESULTS
    # ======================================
    scored.sort(reverse=True, key=lambda x: x[0])

    # ======================================
    # GET TOP MATCHES
    # ======================================
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
        "status": "ok",
        "files_loaded": list(DATA_CACHE.keys())
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

        # ==================================
        # STEP 1: SEARCH CONTEXT
        # ==================================
        context = search_answer(question)

        # ==================================
        # STEP 2: AI RESPONSE
        # ==================================
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

    print("===================================")
    print("SMART AI COLLEGE CHATBOT STARTED")
    print("===================================")

    # Preload files
    load_all_data()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True
    )
