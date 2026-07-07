from flask import Flask, request, jsonify
from flask_cors import CORS

import os
import time
import faiss
import numpy as np

from groq import Groq
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app)

# ==========================================
# CONFIGURATION
# ==========================================

DATA_FOLDER = "data"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 150

TOP_K = 8

GROQ_MODEL = "llama-3.1-8b-instant"

DEBUG = True

# ==========================================
# GROQ CLIENT
# ==========================================

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

# ==========================================
# EMBEDDING MODEL
# ==========================================

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

# ==========================================
# GLOBAL STORAGE
# ==========================================

documents = []

document_sources = []

index = None

file_times = {}

last_index_time = 0

def load_files():

    docs = []
    sources = []

    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)

    for root, dirs, files in os.walk(DATA_FOLDER):

        for file in files:

            if not file.lower().endswith(".txt"):
                continue

            path = os.path.join(root, file)

            try:

                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()

                if len(text) < 10:
                    continue

                docs.append(text)
                sources.append(path)

                if DEBUG:
                    print("Loaded:", path)

            except Exception as e:
                print("Cannot read:", path)
                print(e)

    return docs, sources


# ==========================================
# SPLIT TEXT INTO CHUNKS
# ==========================================

def split_text(text):

    chunks = []

    start = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ==========================================
# CHECK IF FILES CHANGED
# ==========================================

def files_changed():

    global file_times

    changed = False

    current = {}

    for root, dirs, files in os.walk(DATA_FOLDER):

        for file in files:

            if file.lower().endswith(".txt"):

                path = os.path.join(root, file)

                mtime = os.path.getmtime(path)

                current[path] = mtime

                if path not in file_times:
                    changed = True

                elif file_times[path] != mtime:
                    changed = True

    if len(current) != len(file_times):
        changed = True

    file_times = current

    return changed


# ==========================================
# BUILD VECTOR INDEX
# ==========================================

def build_index():



    global documents
    global document_sources
    global index
    global last_index_time

    print("\nBuilding vector index...")

    documents = []
    document_sources = []

    files, sources = load_files()

    for text, source in zip(files, sources):

        chunks = split_text(text)

        for chunk in chunks:

            documents.append(chunk)
            document_sources.append(source)

    if len(documents) == 0:

        print("No documents found.")
        return

    embeddings = embedding_model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings.astype("float32"))

    last_index_time = time.time()

    print("--------------------------------")
    print("Files :", len(files))
    print("Chunks:", len(documents))
    print("Index Built Successfully")
    print("--------------------------------")


# ==========================================
# SEMANTIC SEARCH
# ==========================================

def search_answer(question):

    global index

    if index is None:
        build_index()

    if files_changed():
        print("Files changed. Rebuilding index...")
        build_index()

    query = embedding_model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    distances, indices = index.search(
        query.astype("float32"),
        TOP_K
    )

    context = []
    used_sources = []

    SIMILARITY_THRESHOLD = 0.25

    for score, idx in zip(distances[0], indices[0]):

        if idx == -1:
            continue

        if score < SIMILARITY_THRESHOLD:
            continue

        context.append(documents[idx])

        if document_sources[idx] not in used_sources:
            used_sources.append(document_sources[idx])

    if DEBUG:

        print("\n==============================")
        print("QUESTION:")
        print(question)
        print("==============================")

        print("MATCHED FILES:")

        for s in used_sources:
            print(" -", s)

        print("==============================")

    return "\n\n".join(context)



# ==========================================
# GENERATE AI RESPONSE
# ==========================================


def generate_ai_response(question, context):

    if not context.strip():
        return "I don't have that information."

    prompt = f"""
You are the official AI assistant of YES International College.

STRICT RULES:

1. Answer ONLY from the provided context.

2. Never make up information.

3. If the answer is not found, reply exactly:

I don't have that information.

4. Be friendly.

5. Use bullet points whenever suitable.

6. Do not mention the word "context".

-------------------------

{context}

-------------------------

Question:

{question}

Answer:
"""

    try:

        response = client.chat.completions.create(

            model=GROQ_MODEL,

            temperature=0,

            max_tokens=500,

            messages=[
                {
                    "role":"system",
                    "content":"You are an official college assistant."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:

        print(e)

        return "Server error."

# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return "YES International College AI Chatbot Running"


# ==========================================
# HEALTH
# ==========================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "documents": len(documents),
        "files": len(file_times)
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
                "status": "error",
                "reply": "Please send a message."
            })

        question = data.get("message", "").strip()

        if question == "":
            return jsonify({
                "status": "error",
                "reply": "Please enter a question."
            })

        context = search_answer(question)

        if DEBUG:
            print("\n========== CONTEXT ==========")
            print(context)
            print("=============================\n")

        answer = generate_ai_response(question, context)

        return jsonify({
            "status": "success",
            "reply": answer
        })

    except Exception as e:

        print("CHAT ERROR:", e)

        return jsonify({
            "status": "error",
            "reply": "Server Error."
        })


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    print("=" * 60)
    print("YES AI CHATBOT STARTING...")
    print("=" * 60)

    build_index()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=True
    )
