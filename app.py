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
# DATA CACHE
# ==========================================
DATA_FOLDER = "data"

DATA_CACHE = {}
LAST_MODIFIED = {}
COMBINED_DATA = ""

# ==========================================
# BROCHURE URL
# ==========================================
BROCHURE_BASE = "https://yes.edu.my/brochure/"

# ==========================================
# COURSE BROCHURES
# ==========================================
BROCHURES = {

    # ACCA
    "acca": "acca-brochure.pdf",
    "association of chartered certified accountants": "acca-brochure.pdf",

    # Certificate
    "certificate business studies":
        "certificate-business-studies-brochure.pdf",

    "certificate food beverage":
        "certificate-food-beverage-brochure.pdf",

    "certificate food and beverage":
        "certificate-food-beverage-brochure.pdf",

    "certificate hotel operation":
        "certificate-hotel-operation-brochure.pdf",

    "certificate intensive english":
        "certificate-intensive-english-brochure.pdf",

    "certificate software engineering":
        "certificate-software-engineering-brochure.pdf",

    # Diploma

    "diploma business management":
        "diploma-business-management-brochure.pdf",

    "diploma business management odl":
        "diploma-business-management-odl-brochure.pdf",

    "diploma computer science":
        "diploma-computer-science-brochure.pdf",

    "diploma graphic design":
        "diploma-graphic-design-brochure.pdf",

    "diploma early childhood":
        "diploma-in-early-childhood-brochure.pdf",

    "diploma property management":
        "diploma-in-property-management-brochure.pdf",

    "diploma psychology":
        "diploma-in-psychology-brochure.pdf",

    "diploma information systems":
        "diploma-information-systems-brocure.pdf",

    "diploma logistic supply management":
        "diploma-logistic-supply-management-brochure.pdf",

    # Bachelor

    "bachelor business administration":
        "bachelor-business-administration-brochure.pdf",

    "business administration":
        "bachelor-business-administration-brochure.pdf",

    "bachelor software engineering":
        "bachelor-software-engineering-brochure.pdf",

    "software engineering":
        "bachelor-software-engineering-brochure.pdf",

    "bachelor visual communication":
        "bachelor-visual-communication--brochure.pdf",

    "visual communication":
        "bachelor-visual-communication--brochure.pdf",

    # HND

    "hnd business":
        "hnd-business-brochure.pdf",

    "hnd computing":
        "hnd-computing-brochure.pdf",

    "hnd graphic design":
        "hnd-graphic-design-brochure.pdf",

    "hnd interior design":
        "hnd-interior-design-brochure.pdf",

    "hnd procurement supply":
        "hnd-procurement-supply-brochure.pdf",

    # Others

    "teesside":
        "teeside-university-brochure.pdf",

    "teeside":
        "teeside-university-brochure.pdf",

    "amjb":
        "amjb-handbook.pdf"
}

# ==========================================
# COURSE SYNONYMS
# ==========================================
SYNONYMS = {

    "cs":
        "computer science",

    "it":
        "information systems",

    "english":
        "intensive english",

    "graphic":
        "graphic design",

    "hotel":
        "hotel operation",

    "business":
        "business management",

    "software":
        "software engineering",

    "acca course":
        "acca",

    "degree":
        "bachelor",

    "foundation":
        "certificate"
}

# ==========================================
# LOAD TXT FILES
# ==========================================
def load_all_data():

    global DATA_CACHE
    global LAST_MODIFIED
    global COMBINED_DATA

    updated = False

    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    for root, dirs, files in os.walk(DATA_FOLDER):

        for file in files:

            if not file.endswith(".txt"):
                continue

            filepath = os.path.join(root, file)

            relative = os.path.relpath(filepath, DATA_FOLDER)

            modified = os.path.getmtime(filepath)

            if (
                relative not in LAST_MODIFIED
                or LAST_MODIFIED[relative] != modified
            ):

                with open(
                    filepath,
                    "r",
                    encoding="utf-8"
                ) as f:

                    DATA_CACHE[relative] = f.read()

                LAST_MODIFIED[relative] = modified

                updated = True

                print("Loaded:", relative)

    if updated or not COMBINED_DATA:

        COMBINED_DATA = "\n\n".join(DATA_CACHE.values())

    return COMBINED_DATA
    # ==========================================
# CLEAN TEXT
# ==========================================

CLEAN_REGEX = re.compile(r'[^a-z0-9\s]')

def clean_text(text):

    text = text.lower()

    text = CLEAN_REGEX.sub(" ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ==========================================
# EXPAND QUESTION USING SYNONYMS
# ==========================================

def expand_question(question):

    question = clean_text(question)

    for key, value in SYNONYMS.items():

        question = question.replace(key, value)

    return question


# ==========================================
# STRING SIMILARITY
# ==========================================

def similarity(a, b):

    return SequenceMatcher(None, a, b).ratio()


# ==========================================
# FIND BROCHURE
# ==========================================

def get_brochure(question):

    q = expand_question(question)

    for course, pdf in BROCHURES.items():

        if course in q:

            return BROCHURE_BASE + pdf

    return None


# ==========================================
# SEARCH ANSWER
# ==========================================

def search_answer(question):

    data = load_all_data()

    if not data:

        return ""

    question_clean = expand_question(question)

    sections = re.split(r"\n\s*\n", data)

    scored = []

    keywords = [
        "acca",
        "registry",
        "certificate",
        "diploma",
        "bachelor",
        "degree",
        "hnd",
        "business",
        "software",
        "computer",
        "science",
        "graphic",
        "hotel",
        "english",
        "culinary",
        "psychology",
        "property",
        "logistic",
        "information",
        "visa",
        "loan",
        "admission",
        "fees",
        "entry",
        "duration",
        "semester",
        "intake"
    ]

    q_words = set(question_clean.split())

    for section in sections:

        if not section.strip():
            continue

        section_clean = clean_text(section)

        s_words = set(section_clean.split())

        score = 0

        # =====================================
        # EXACT WORD MATCH
        # =====================================

        common = q_words.intersection(s_words)

        score += len(common) * 6

        # =====================================
        # PARTIAL WORD MATCH
        # =====================================

        for qw in q_words:

            for sw in s_words:

                if qw != sw and (qw in sw or sw in qw):

                    score += 2

        # =====================================
        # IMPORTANT KEYWORD BONUS
        # =====================================

        for keyword in keywords:

            if keyword in question_clean and keyword in section_clean:

                score += 10

        # =====================================
        # STRING SIMILARITY BONUS
        # =====================================

        score += similarity(question_clean, section_clean) * 12

        if score > 5:

            scored.append((score, section))

    scored.sort(reverse=True, key=lambda x: x[0])

    context = ""

    for score, section in scored:

        if len(context) > 2200:
            break

        context += section.strip()
        context += "\n\n"

    return context.strip()


# ==========================================
# DEBUG SEARCH (OPTIONAL)
# ==========================================

def debug_search(question):

    data = load_all_data()

    sections = re.split(r"\n\s*\n", data)

    print("=" * 70)
    print("QUESTION:", question)
    print("=" * 70)

    for section in sections[:5]:

        print(section[:200])
        print("-" * 50)

# ==========================================
# AI RESPONSE
# ==========================================

def generate_ai_response(question, context):

    if not context.strip():
        return (
            "I don't have that information.\n\n"
            "For more information, please visit:\n"
            "https://yes.edu.my/brochure/"
        )

    brochure = get_brochure(question)

    try:

        prompt = f"""
You are the OFFICIAL YES International College AI Assistant.

IMPORTANT RULES

1. Answer ONLY from the CONTEXT below.

2. Never use outside knowledge.

3. Never guess.

4. Never invent fees, duration, entry requirements,
or programme details.

5. If the answer is not found in the context, reply exactly:

I don't have that information.

6. Keep answers friendly.

7. Keep answers under 150 words.

8. If the question is about a course or programme,
summarize the programme clearly.

9. Use bullet points whenever appropriate.

CONTEXT

{context}

QUESTION

{question}
"""

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            temperature=0,

            max_tokens=350,

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are the official YES International College assistant."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ]

        )

        answer = response.choices[0].message.content.strip()

        if not answer:

            answer = "I don't have that information."

        # ==========================================
        # ADD BROCHURE
        # ==========================================

        if brochure:

            answer += (
                "\n\n"
                "📄 Programme Brochure\n"
                f"{brochure}"
            )

        # ==========================================
        # WEBSITE LINK
        # ==========================================

        answer += (
            "\n\n"
            "🌐 YES International College\n"
            "https://yes.edu.my/"
        )

        return answer

    except Exception as e:

        print("GROQ ERROR:", e)

        return (
            "Sorry, I couldn't process your request.\n"
            "Please try again later."
        )
# ==========================================
# HOME
# ==========================================
@app.route("/")
def home():

    load_all_data()

    return jsonify({
        "status": "running",
        "message": "YES International College AI Chatbot",
        "loaded_files": len(DATA_CACHE)
    })


# ==========================================
# HEALTH CHECK
# ==========================================
@app.route("/health")
def health():

    load_all_data()

    return jsonify({

        "status": "ok",

        "files_loaded": list(DATA_CACHE.keys()),

        "total_files": len(DATA_CACHE),

        "brochures": len(BROCHURES)

    })


# ==========================================
# CHAT API
# ==========================================
@app.route("/chat", methods=["POST"])
def chat():

    try:

        load_all_data()

        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "reply": "Please send a JSON request."
            })

        question = data.get("message", "").strip()

        if question == "":
            return jsonify({
                "status": "error",
                "reply": "Please enter your question."
            })

        # ==================================
        # DIRECT BROCHURE RESPONSE
        # ==================================
        brochure = get_brochure(question)

        if brochure:
            return jsonify({
                "status": "success",
                "reply": f"📄 You can view the programme brochure here:\n\n{brochure}"
            })

        # ==================================
        # NORMAL AI RESPONSE
        # ==================================
        context = search_answer(question)
        answer = generate_ai_response(question, context)

        return jsonify({
            "status": "success",
            "reply": answer
        })

    except Exception as e:

        print("CHAT ERROR:", e)

        return jsonify({
            "status": "error",
            "reply": "Sorry, something went wrong."
        })

# ==========================================
# RELOAD DATA
# ==========================================
@app.route("/reload")
def reload_data():

    global DATA_CACHE
    global LAST_MODIFIED
    global COMBINED_DATA

    DATA_CACHE = {}
    LAST_MODIFIED = {}
    COMBINED_DATA = ""

    load_all_data()

    return jsonify({

        "status": "success",

        "message": "Knowledge base reloaded.",

        "files": list(DATA_CACHE.keys())

    })


# ==========================================
# LIST COURSES
# ==========================================
@app.route("/courses")
def courses():

    return jsonify({

        "total_courses": len(BROCHURES),

        "courses": sorted(BROCHURES.keys())

    })


# ==========================================
# START SERVER
# ==========================================
if __name__ == "__main__":

    print("=" * 70)
    print("YES INTERNATIONAL COLLEGE AI CHATBOT")
    print("=" * 70)

    load_all_data()

    print("Knowledge Files Loaded:", len(DATA_CACHE))

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 10000)),

        debug=True

    )
