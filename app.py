from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from proxy import process_prompt
from logger import log_request
import os

# Load environment variables
load_dotenv()

CONTACTS = []

app = Flask(__name__)
CORS(app)

@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)

        # Log request
        log_request(data)

        # Proxy to OpenAI or other service
        results = process_prompt(data)

        return jsonify({
            "redacted": results.get('redacted', ""),           
            "detectors": results.get('detected', {}),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return "Zero Harm AI Flask backend is running."

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    if not (name and email and message):
        return jsonify({'error':'missing fields'}), 400
    CONTACTS.append({'name':name,'email':email,'message':message})
    # In production send an email via SMTP or hook to CRM
    return jsonify({'ok':True, 'message':'received'})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
