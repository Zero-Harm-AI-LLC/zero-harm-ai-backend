
import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
try:
    import openai
    from dotenv import load_dotenv
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    openai = None

app = Flask(__name__)
CORS(app)

SENSITIVE_KEYWORDS = ["hate", "attack", "self-harm", "suicide", "violence", "explosive"]
PATTERNS = [r"\bi (want|plan|intend) to (kill|hurt|harm)\b", r"\b(credit card|ssn|social security|bank account)\b"]

@app.route('/api/moderate/hybrid', methods=['POST'])
def moderate_hybrid():
    data = request.json
    text = data.get('input', '').lower()
    matched_keywords = [k for k in SENSITIVE_KEYWORDS if k in text]
    matched_patterns = [p for p in PATTERNS if re.search(p, text)]
    flagged = bool(matched_keywords or matched_patterns)
    reasons = []
    if matched_keywords:
        reasons.append("keywords: " + ", ".join(matched_keywords))
    if matched_patterns:
        reasons.append("regex match")
    return jsonify({'flagged': flagged, 'reason': "; ".join(reasons) if flagged else "safe"})

@app.route('/api/moderate/openai', methods=['POST'])
def moderate_openai():
    if not openai or not openai.api_key:
        return jsonify({'error': 'OpenAI not configured'}), 500
    data = request.json
    input_text = data.get("input", "")
    try:
        response = openai.Moderation.create(input=input_text)
        result = response["results"][0]
        flagged = result["flagged"]
        categories = [k for k, v in result["categories"].items() if v]
        return jsonify({"flagged": flagged, "categories": categories, "reason": ", ".join(categories) if categories else "safe"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def health():
    return "Zero Harm AI Flask backend is running."
