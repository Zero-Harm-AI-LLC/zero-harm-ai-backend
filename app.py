from flask import Flask, request, jsonify
from dotenv import load_dotenv
from proxy import proxy_request
from detectors import run_detectors
from logger import log_request
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route("/api/moderate", methods=["POST"])
def moderate():
    try:
        data = request.get_json(force=True)

        # Log request
        log_request(data)

        # Run detectors
        detector_results = run_detectors(data)

        # Proxy to OpenAI or other service
        proxy_results = proxy_request(data)

        return jsonify({
            "detectors": detector_results,
            "proxy": proxy_results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
