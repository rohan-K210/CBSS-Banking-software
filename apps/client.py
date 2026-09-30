"""
Client Transaction Application (Port 5001).

Routes:
    /login (GET/POST)          → Customer login
    /add (GET/POST)            → Make transaction (with fraud detection)
    /client                    → Client dashboard
    /fraud (GET/POST)          → Fraud review (pending transactions)
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
from shared.database import get_cursor, get_connection
from shared.security import create_app, require_session
from services.fraud_model import predict_fraud

logger = logging.getLogger(__name__)


def create_client_app() -> Flask:
    """Create and configure the client transaction Flask app."""
    settings = get_settings()
    app = create_app(settings.client_app)

    # Static files served automatically by Flask from static/

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
    # Make Transaction
    # -----------------------------------------------------------------------
    @app.route("/add", methods=["GET", "POST"])
    @require_session
    def add():
        if request.method == "POST":
            receiver_id = request.form.get("receiver_id")
            amount = float(request.form.get("amount", 0))
            sender_id = session["sender_id"]
            now = datetime.now()

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

                    # Run fraud detection
                    status = predict_fraud(
                        sender_id=sender_id,
                        receiver_id=int(receiver_id),
                        amount=amount,
                        ip_address=sender_ip,
                        mac_address=sender_mac,
                    )

                    # Map prediction to status
                    txn_status = "Pending" if status == "blocked" else "Approved"

                    # Insert transaction
                    cursor.execute(
                        """INSERT INTO transactions
                           (id, sender_id, receiver_id, amount, date,
                            sender_ip_address, sender_mac_address,
                            receiver_ip_address, receiver_mac_address, status)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (transaction_id, sender_id, receiver_id, amount, now,
                         sender_ip, sender_mac, receiver_ip, receiver_mac, txn_status),
                    )

                flash(f"Transaction added successfully! Transaction ID: {transaction_id}", "success")
                logger.info("Transaction added: id=%s sender=%s receiver=%s amount=%.2f status=%s",
                            transaction_id, sender_id, receiver_id, amount, txn_status)
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
    # Fraud Review
    # -----------------------------------------------------------------------
    @app.route("/fraud", methods=["GET", "POST"])
    @require_session
    def fraud():
        if request.method == "POST":
            transaction_id = request.form.get("transaction_id")
            decision = request.form.get("decision")

            try:
                with get_cursor() as cursor:
                    if decision == "approve":
                        cursor.execute(
                            "UPDATE transactions SET status = 'Approved' WHERE id = %s",
                            (transaction_id,),
                        )
                        flash(f"Transaction {transaction_id} approved.", "success")
                    elif decision == "reject":
                        cursor.execute(
                            "UPDATE transactions SET status = 'Rejected' WHERE id = %s",
                            (transaction_id,),
                        )
                        flash(f"Transaction {transaction_id} rejected.", "danger")
                    logger.info("Fraud decision: transaction=%s decision=%s", transaction_id, decision)
            except Exception as e:
                flash(f"Error processing decision: {e}", "error")
                logger.error("Fraud decision error: %s", e)

            return redirect(url_for("fraud"))

        # Fetch pending transactions
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT id AS transaction_id, sender_id, receiver_id, amount, date "
                    "FROM transactions WHERE status = 'Pending'"
                )
                transactions = cursor.fetchall()
            return render_template("client/fraud.html", transactions=transactions)
        except Exception as e:
            logger.error("Failed to fetch pending transactions: %s", e)
            return render_template("client/fraud.html", transactions=[])

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
    # JSON API Endpoints (for AJAX/JavaScript consumption)
    # -----------------------------------------------------------------------

    @app.route("/api/transactions")
    @require_session
    def api_transactions():
        """Return current user's transactions as JSON."""
        sender_id = session["sender_id"]
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id, sender_id, receiver_id, amount, date, status
                     FROM transactions WHERE sender_id = %s ORDER BY date DESC""",
                    (sender_id,),
                )
                transactions = cursor.fetchall()
            for txn in transactions:
                if txn.get("date"):
                    txn["date"] = txn["date"].isoformat()
            return jsonify({"success": True, "data": transactions})
        except Exception as e:
            logger.error("Failed to fetch transactions: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch transactions"}}), 500

    @app.route("/api/customer/info")
    @require_session
    def api_customer_info():
        """Return current logged-in customer info."""
        sender_id = session["sender_id"]
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id, full_name, bank_balance, credit_score, occupation
                     FROM customers WHERE id = %s""",
                    (sender_id,),
                )
                customer = cursor.fetchone()
            if not customer:
                return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Customer not found"}}), 404
            return jsonify({"success": True, "data": customer})
        except Exception as e:
            logger.error("Failed to fetch customer info: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch customer info"}}), 500

    # -----------------------------------------------------------------------
    # Health Check
    # -----------------------------------------------------------------------
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "service": "client"})

    return app


# ---------------------------------------------------------------------------
# Direct run support
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    settings = get_settings()
    app = create_client_app()
    app.run(
        host=settings.client_app.host,
        port=settings.client_app.port,
        debug=settings.client_app.debug,
    )
