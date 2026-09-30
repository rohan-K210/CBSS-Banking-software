"""
Simple Client Transaction Application (Port 5004).

Routes:
    /login (GET/POST)          → Customer login
    /add (GET/POST)            → Make transaction (no ML)
    /client                    → Client dashboard
    /show                      → Transaction history (client view)
    /logout                    → Logout
    /transaction_success       → Transaction success page
    /health                    → Health check
"""

import logging
import uuid
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from shared.config import get_settings
from shared.database import get_cursor
from shared.security import create_app, require_session

logger = logging.getLogger(__name__)


def create_simple_transaction_app() -> Flask:
    """Create and configure the simple transaction Flask app."""
    settings = get_settings()
    app = create_app(settings.simple_transaction_app)

    # -----------------------------------------------------------------------
    # Login
    # -----------------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            customer_id = request.form.get("customer_id")
            password = request.form.get("password")

            try:
                with get_cursor() as cursor:
                    cursor.execute(
                        "SELECT id, password FROM customers WHERE id = %s",
                        (customer_id,),
                    )
                    result = cursor.fetchone()

                if result and result[1] == password:
                    session["sender_id"] = result[0]
                    logger.info("Customer logged in: id=%s", customer_id)
                    return redirect(url_for("client"))
                else:
                    flash("Invalid customer ID or password.", "error")
                    logger.warning("Failed login attempt: id=%s", customer_id)
            except Exception as e:
                flash("Login error. Please try again.", "error")
                logger.error("Login error: %s", e)

            return redirect(url_for("login"))

        return render_template("client/login.html")

    # -----------------------------------------------------------------------
    # Make Transaction (no fraud detection)
    # -----------------------------------------------------------------------
    @app.route("/add", methods=["GET", "POST"])
    @require_session
    def add():
        if request.method == "POST":
            receiver_id = request.form.get("receiver_id")
            amount = request.form.get("amount")
            now = datetime.now()
            sender_id = session["sender_id"]

            transaction_id = str(uuid.uuid4())

            try:
                with get_cursor(dictionary=True) as cursor:
                    # Fetch sender details
                    cursor.execute(
                        "SELECT ip_address, mac_address FROM customers WHERE id = %s",
                        (sender_id,),
                    )
                    sender_details = cursor.fetchone()
                    sender_ip = sender_details["ip_address"] if sender_details else "Unknown"
                    sender_mac = sender_details["mac_address"] if sender_details else "Unknown"

                    # Fetch receiver details
                    cursor.execute(
                        "SELECT ip_address, mac_address FROM customers WHERE id = %s",
                        (receiver_id,),
                    )
                    receiver_details = cursor.fetchone()
                    receiver_ip = receiver_details["ip_address"] if receiver_details else "Unknown"
                    receiver_mac = receiver_details["mac_address"] if receiver_details else "Unknown"

                    # Insert transaction (no fraud detection)
                    cursor.execute(
                        """INSERT INTO transactions
                           (id, sender_id, receiver_id, amount, date,
                            sender_ip_address, sender_mac_address,
                            receiver_ip_address, receiver_mac_address)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (transaction_id, sender_id, receiver_id, amount, now,
                         sender_ip, sender_mac, receiver_ip, receiver_mac),
                    )

                flash(f"Transaction added successfully! Transaction ID: {transaction_id}", "success")
                logger.info("Transaction added: id=%s sender=%s receiver=%s amount=%s",
                            transaction_id, sender_id, receiver_id, amount)
                return redirect(url_for("transaction_success", transaction_id=transaction_id))

            except Exception as e:
                flash(f"Transaction failed: {e}", "error")
                logger.error("Transaction failed: %s", e)
                return redirect(url_for("add"))

        return render_template("client/make_transaction.html")

    # -----------------------------------------------------------------------
    # Transaction Success
    # -----------------------------------------------------------------------
    @app.route("/transaction_success")
    def transaction_success():
        transaction_id = request.args.get("transaction_id")
        return f"Transaction added successfully! Transaction ID: {transaction_id}"

    # -----------------------------------------------------------------------
    # Logout
    # -----------------------------------------------------------------------
    @app.route("/logout")
    def logout():
        sender_id = session.pop("sender_id", None)
        flash("You have been logged out.", "info")
        logger.info("Customer logged out: id=%s", sender_id)
        return redirect(url_for("login"))

    # -----------------------------------------------------------------------
    # Client Dashboard
    # -----------------------------------------------------------------------
    @app.route("/client")
    @require_session
    def client():
        return render_template("client/dashboard.html")

    # -----------------------------------------------------------------------
    # Transaction History (Client View)
    # -----------------------------------------------------------------------
    @app.route("/show")
    @require_session
    def transactions():
        sender_id = session["sender_id"]
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, receiver_id, amount, date FROM transactions WHERE sender_id = %s",
                    (sender_id,),
                )
                txns = cursor.fetchall()
            return render_template("client/transactions.html", transactions=txns)
        except Exception as e:
            logger.error("Failed to fetch transactions: %s", e)
            return render_template("client/transactions.html", transactions=[])

    # -----------------------------------------------------------------------
    # Health Check
    # -----------------------------------------------------------------------
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "service": "simple_transaction"})

    return app


# ---------------------------------------------------------------------------
# Direct run support
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    settings = get_settings()
    app = create_simple_transaction_app()
    app.run(
        host=settings.simple_transaction_app.host,
        port=settings.simple_transaction_app.port,
        debug=settings.simple_transaction_app.debug,
    )
