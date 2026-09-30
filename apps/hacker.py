"""
Hacker Attack Simulator Application (Port 5002).

Routes:
    /           → Hacker dashboard
    /hacker     → POST attack simulation
    /health     → Health check
"""

import logging
import random
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from shared.config import get_settings
from shared.database import get_cursor
from shared.security import create_app
from services.attack_model import predict_attack

logger = logging.getLogger(__name__)


def create_hacker_app() -> Flask:
    """Create and configure the hacker attack simulator Flask app."""
    settings = get_settings()
    app = create_app(settings.hacker_app)

    @app.route("/")
    def home():
        return render_template("shared/hacker.html")

    @app.route("/hacker", methods=["POST"])
    def attack():
        receiver_id = 0  # Hacker's ID
        sender_id = 2    # Customer 2's ID
        amount = float(request.form["amount"])
        mac_address = "00:11:22:33:44:55"
        ip_address = "192.168.1.100"
        now = datetime.now()
        transaction_id = str(random.randint(100000, 999999))

        try:
            status = predict_attack(
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
                    (transaction_id, sender_id, receiver_id, amount, now,
                     ip_address, mac_address, ip_address, mac_address, status),
                )

            logger.info("Attack simulation: amount=%.2f status=%s", amount, status)
            return render_template("shared/hacker.html", status=status)

        except Exception as e:
            logger.error("Attack simulation failed: %s", e)
            return render_template("shared/hacker.html", status=f"Error: {e}")

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "service": "hacker"})

    return app


# ---------------------------------------------------------------------------
# Direct run support
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    settings = get_settings()
    app = create_hacker_app()
    app.run(
        host=settings.hacker_app.host,
        port=settings.hacker_app.port,
        debug=settings.hacker_app.debug,
    )
