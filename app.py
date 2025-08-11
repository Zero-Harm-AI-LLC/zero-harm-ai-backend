from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from proxy import process_prompt
from logger import log_request
from email.mime.text import MIMEText
import smtplib
import os

# Load environment variables
load_dotenv()

CONTACTS = []

app = Flask(__name__)
CORS(app)

@app.route("/api/check_privacy", methods=["POST"])
def check_privacy():
    try:
        data = request.get_json(force=True)
        prompt = data["text"]
        # Log request
        log_request(prompt)

        # Proxy to OpenAI or other service
        redacted, detected = process_prompt(prompt)

        return jsonify({
            "redacted": redacted,
            "detectors": detected,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health_check", methods=["GET"])
def health_check():
    return "Zero Harm AI Flask backend is running."

@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.json
    to_email = data.get("email")
    subject = data.get("name")
    body = data.get("message")

    if not all([to_email, subject, body]):
        return jsonify({"error": "Missing required fields",
                        "to_email": to_email,
                        "subject": subject,
                        "body": body}), 400

    try:
        msg = MIMEText(body, "html")
        msg["Subject"] = subject + " " + to_email
        msg["From"] = os.environ["EMAIL_USER"]
        msg["To"] = "info@zeroharmai.com"   # send to our email box

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
            server.send_message(msg)

        return jsonify({"message": "Email sent successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Only run the Flask development server locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
