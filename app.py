from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import pdfplumber
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# ✅ OpenAI client
client = OpenAI(api_key=os.environ.get("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"))

# ✅ Load PDFs safely
def load_pdfs():
    text = ""
    folder = "pdfs"

    # If folder missing
    if not os.path.exists(folder):
        return "No PDF data available."

    for file in os.listdir(folder):
        if file.endswith(".pdf"):
            try:
                with pdfplumber.open(os.path.join(folder, file)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:   # avoid None error
                            text += page_text + "\n"
            except Exception as e:
                print(f"Error reading {file}: {e}")

    return text

# Load data once
DATA = load_pdfs()

# ✅ Smart keyword-based context search
def search_context(question):
    chunks = DATA.split("\n")
    relevant = []

    for chunk in chunks:
        if any(word in chunk.lower() for word in question.lower().split()):
            relevant.append(chunk)

    return "\n".join(relevant[:10])  # limit context

@app.route("/")
def home():
    return "AI PDF Bot Running"

# ✅ Chat endpoint with error handling
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

# ✅ Required for Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
