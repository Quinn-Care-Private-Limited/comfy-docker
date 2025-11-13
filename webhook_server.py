#!/usr/bin/env python3
"""
Simple HTTP server with POST webhook route for logging HTTP body.
"""

import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    POST webhook endpoint that logs the HTTP request body.
    """
    try:
        # Get the raw body
        raw_body = request.get_data(as_text=True)

        # Try to parse as JSON for pretty logging
        try:
            json_body = request.get_json()
            body_str = json.dumps(json_body, indent=2)
            logger.info(f"Webhook received (JSON):\n{body_str}")
        except Exception:
            # If not JSON, log as raw text
            logger.info(f"Webhook received (raw):\n{raw_body}")

        # Log additional request metadata
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Content-Length: {request.content_length}")

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Webhook received and logged",
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    import os

    port = int(os.environ.get("WEBHOOK_PORT", 3000))
    host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")

    logger.info(f"Starting webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=False)
