"""
Fraud Detection Application (Port 5003).

Routes:
    /hacker (GET)  → Hacker dashboard
    /hacker (POST) → Fraud detection attack
    /health        → Health check
"""

import logging
import random
from datetime import datetime

import ipaddress as ipaddress_mod
from flask import Flask, jsonify, render_template, request

from shared.config import get_settings
from shared.database import get_cursor
from shared.security import create_app
from services.fraud_model import predict_fraud

logger = logging.getLogger(__name__)


def create_fraud_detector_app() -> Flask:
    """Create and configure the fraud detector Flask app."""
    settings = get_settings()
    app = create_app(settings.fraud_detector_app)

    @app.route("/hacker")
    def hacker():
        return render_template("shared/hacker.html")

    @app.route("/hacker", methods=["POST"])
    def attack():
        receiver_id = 0
        sender_id = 2
        amount = float(request.form["amount"])

        mac_address = "00:00:00:00:00:00" if receiver_id == 0 else "00:11:22:33:44:55"
        ip_address = "0.0.0.0" if receiver_id == 0 else "192.168.1.100"
        now = datetime.now()
        transaction_id = str(random.randint(100000, 999999))

        try:
            status = predict_fraud(
                sender_id=sender_id,
                receiver_id=receiver_id if receiver_id != 0 else None,
                amount=amount,
                ip_address=ip_address,
                mac_address=mac_address,
            )

            with get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO transactions
                       (id, sender_id, receiver_id, amount, date,
                        sender_ip_address, sender_mac_address,
                        receiver_ip_address, receiver_mac_address, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        transaction_id, sender_id,
                        receiver_id if receiver_id != 0 else None,
                        amount, now, ip_address, mac_address,
                        ip_address if receiver_id != 0 else None,
                        mac_address if receiver_id != 0 else None,
                        status,
                    ),
                )

            logger.info("Fraud detection attack: amount=%.2f status=%s", amount, status)
            return render_template("shared/hacker.html", status=status)

        except Exception as e:
            logger.error("Fraud detection attack failed: %s", e)
            return render_template("shared/hacker.html", status=f"Error: {e}")

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "service": "fraud_detector"})

    return app


# ---------------------------------------------------------------------------
# Direct run support
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    settings = get_settings()
    app = create_fraud_detector_app()
    app.run(
        host=settings.fraud_detector_app.host,
        port=settings.fraud_detector_app.port,
        debug=settings.fraud_detector_app.debug,
    )
