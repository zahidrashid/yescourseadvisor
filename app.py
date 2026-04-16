from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pdfplumber
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 📂 Extract text from all PDFs
def load_pdfs():
    text = ""
    folder = "pdfs"
    
    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            with pdfplumber.open(os.path.join(folder, file)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
    
    return text

DATA = load_pdfs()

# 🔍 Simple smart search (chunk matching)
def search_context(question):
    chunks = DATA.split("\n")
    
    relevant = []
    for chunk in chunks:
        if any(word in chunk.lower() for word in question.lower().split()):
            relevant.append(chunk)
    
    return "\n".join(relevant[:10])  # limit

@app.route("/")
def home():
    return "AI PDF Bot Running"

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json["message"]

    context = search_context(question)

    prompt = f"""
    You are a college assistant.
    Answer only using the context below.

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
