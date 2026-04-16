from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)

# ✅ Enable CORS (fixes your error)
CORS(app)

# Load data
with open("data.txt", "r", encoding="utf-8") as f:
    DATA = f.read().lower()

# Home route (for testing)
@app.route("/")
def home():
    return "College Bot is running!"

# Chat route
@app.route("/chat", methods=["POST"])
def chat():
    question = request.json["message"].lower()

    if "bca" in question and "fee" in question:
        return jsonify({"reply": "BCA fee is 50000 per year"})
    
    if "bba" in question and "fee" in question:
        return jsonify({"reply": "BBA fee is 40000 per year"})
    
    if "faculty" in question:
        return jsonify({"reply": "Computer Science HOD is Mr. XYZ"})
    
    return jsonify({"reply": "Sorry, I couldn't find that info."})

# Run app (important for Render)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
