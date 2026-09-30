"""
Admin Dashboard Application (Port 5000).

Routes:
    /                       → Login page (root)
    /admin                  → Admin dashboard
    /cust                   → Customer management
    /add_customer (POST)    → Add customer
    /edit_customer (POST)   → Edit customer
    /delete_customer (POST) → Delete customer
    /search_customer (POST) → Search customer
    /emp                    → Employee management
    /add_employee (POST)    → Add employee
    /edit_employee (POST)   → Edit employee
    /delete_employee (POST) → Delete employee
    /search_employee (POST) → Search employee
    /loan-valuation         → Loan evaluation (ML)
    /segm                   → Customer segmentation (ML)
    /show                   → Transaction history (admin view)
    /health                 → Health check
"""

import logging
from flask import Flask, render_template, request, redirect, url_for

from shared.config import get_settings
from shared.database import get_cursor, get_connection
from shared.security import create_app
from services.loan_model import predict_loan_approval
from services.segmentation_model import predict_cluster, CLUSTER_DESCRIPTIONS

logger = logging.getLogger(__name__)


def create_admin_app() -> Flask:
    """Create and configure the admin dashboard Flask app."""
    settings = get_settings()
    app = create_app(settings.admin_app)

    # Static files served automatically by Flask from static/

    # -----------------------------------------------------------------------
    # Root & Login
    # -----------------------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("admin/root.html")

    @app.route("/admin")
    def client_dashboard():
        return render_template("admin/dashboard.html")

    # -----------------------------------------------------------------------
    # Customer Management
    # -----------------------------------------------------------------------
    @app.route("/cust")
    def cust():
        return render_template("admin/customers.html", results=None)

    @app.route("/add_customer", methods=["POST"])
    def add_customer():
        try:
            full_name = request.form.get("addFullName")
            gender = request.form.get("addGender")
            age = request.form.get("addAge")
            address = request.form.get("addAddress")
            contact_number = request.form.get("addContactNumber")
            annual_income = request.form.get("addAnnualIncome")
            credit_score = request.form.get("addCreditScore")
            debt_to_income_ratio = request.form.get("addDebtToIncomeRatio")
            occupation = request.form.get("addOccupation")
            loan_status = request.form.get("addLoanStatus")
            insurance_status = request.form.get("addInsuranceStatus")
            ip_address = request.form.get("addIpAddress")
            mac_address = request.form.get("addMacAddress")
            bank_balance = request.form.get("addBankBalance")
            password = request.form.get("addPassword")

            with get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO customers
                       (full_name, gender, age, address, contact_number, annual_income,
                        credit_score, debt_to_income_ratio, occupation, loan_status,
                        insurance_status, ip_address, mac_address, bank_balance, password)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (full_name, gender, age, address, contact_number, annual_income,
                     credit_score, debt_to_income_ratio, occupation, loan_status,
                     insurance_status, ip_address, mac_address, bank_balance, password),
                )
            results = {"message": "Customer added successfully!"}
            logger.info("Customer added: %s", full_name)
        except Exception as e:
            results = {"error": str(e)}
            logger.error("Failed to add customer: %s", e)

        return render_template("admin/customers.html", results=results)

    @app.route("/edit_customer", methods=["POST"])
    def edit_customer():
        try:
            customer_id = request.form.get("editId")
            full_name = request.form.get("editFullName")
            gender = request.form.get("editGender")
            age = request.form.get("editAge")
            address = request.form.get("editAddress")
            contact_number = request.form.get("editContactNumber")
            annual_income = request.form.get("editAnnualIncome")
            credit_score = request.form.get("editCreditScore")
            debt_to_income_ratio = request.form.get("editDebtToIncomeRatio")
            occupation = request.form.get("editOccupation")
            loan_status = request.form.get("editLoanStatus")
            insurance_status = request.form.get("editInsuranceStatus")
            ip_address = request.form.get("editIpAddress")
            mac_address = request.form.get("editMacAddress")
            bank_balance = request.form.get("editBankBalance")
            password = request.form.get("editPassword")

            with get_cursor() as cursor:
                cursor.execute(
                    """UPDATE customers SET full_name=%s, gender=%s, age=%s, address=%s,
                       contact_number=%s, annual_income=%s, credit_score=%s,
                       debt_to_income_ratio=%s, occupation=%s, loan_status=%s,
                       insurance_status=%s, ip_address=%s, mac_address=%s,
                       bank_balance=%s, password=%s
                       WHERE id=%s""",
                    (full_name, gender, age, address, contact_number, annual_income,
                     credit_score, debt_to_income_ratio, occupation, loan_status,
                     insurance_status, ip_address, mac_address, bank_balance, password,
                     customer_id),
                )
            results = {"message": "Customer updated successfully!"}
            logger.info("Customer updated: id=%s", customer_id)
        except Exception as e:
            results = {"error": str(e)}
            logger.error("Failed to update customer: %s", e)

        return render_template("admin/customers.html", results=results)

    @app.route("/delete_customer", methods=["POST"])
    def delete_customer():
        try:
            customer_id = request.form.get("deleteCustomerID")
            with get_cursor() as cursor:
                cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
            results = {"message": "Customer deleted successfully!"}
            logger.info("Customer deleted: id=%s", customer_id)
        except Exception as e:
            results = {"error": str(e)}
            logger.error("Failed to delete customer: %s", e)

        return render_template("admin/customers.html", results=results)

    @app.route("/search_customer", methods=["POST"])
    def search_customer():
        customer_id = request.form.get("searchCustomerID")
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
                result = cursor.fetchone()

            if result:
                results = result  # Already a dict when dictionary=True
            else:
                results = {"message": "Customer not found!"}
        except Exception as e:
            results = {"error": str(e)}
            logger.error("Failed to search customer: %s", e)

        return render_template("admin/customers.html", results=results)

    # -----------------------------------------------------------------------
    # Employee Management
    # -----------------------------------------------------------------------
    @app.route("/emp")
    def emp():
        return render_template("admin/employees.html", employee=None)

    @app.route("/add_employee", methods=["POST"])
    def add_employee():
        results = {}
        try:
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            gender = request.form["gender"]
            dob = request.form["date_of_birth"]
            position = request.form["position"]
            department = request.form["department"]
            hire_date = request.form["hire_date"]
            salary = request.form["salary"]
            email = request.form["email"]
            phone = request.form["phone_number"]
            address = request.form["address"]
            emergency_contact = request.form["emergency_contact"]
            emergency_phone = request.form["emergency_phone_number"]
            performance_rating = request.form["performance_rating"]

            with get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO employees
                       (first_name, last_name, gender, date_of_birth, position, department,
                        hire_date, salary, email, phone_number, address, emergency_contact,
                        emergency_contact_phone, performance_rating)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (first_name, last_name, gender, dob, position, department,
                     hire_date, salary, email, phone, address, emergency_contact,
                     emergency_phone, performance_rating),
                )
            results = {"success": True, "message": f"Employee {first_name} {last_name} added successfully!"}
            logger.info("Employee added: %s %s", first_name, last_name)
        except Exception as e:
            results = {"success": False, "message": f"Failed to add employee: {e}"}
            logger.error("Failed to add employee: %s", e)

        return render_template("admin/employees.html", employee=None, results=results)

    @app.route("/edit_employee", methods=["POST"])
    def edit_employee():
        results = {}
        try:
            employee_id = request.form["employee_id"]
            with get_cursor() as cursor:
                cursor.execute(
                    """UPDATE employees
                       SET first_name=%s, last_name=%s, gender=%s, date_of_birth=%s,
                           position=%s, department=%s, hire_date=%s, salary=%s,
                           email=%s, phone_number=%s, address=%s, emergency_contact=%s,
                           emergency_contact_phone=%s, performance_rating=%s, is_active=%s
                       WHERE employee_id=%s""",
                    (
                        request.form["first_name"], request.form["last_name"],
                        request.form["gender"], request.form["date_of_birth"],
                        request.form["position"], request.form["department"],
                        request.form["hire_date"], request.form["salary"],
                        request.form["email"], request.form["phone_number"],
                        request.form["address"], request.form["emergency_contact"],
                        request.form["emergency_phone_number"],
                        request.form["performance_rating"],
                        request.form["is_active"], employee_id,
                    ),
                )
            results = {"success": True, "message": f"Employee {employee_id} updated successfully!"}
            logger.info("Employee updated: id=%s", employee_id)
        except Exception as e:
            results = {"success": False, "message": f"Failed to update employee: {e}"}
            logger.error("Failed to update employee: %s", e)

        return render_template("admin/employees.html", employee=None, results=results)

    @app.route("/delete_employee", methods=["POST"])
    def delete_employee():
        results = {}
        try:
            employee_id = request.form["employee_id"]
            with get_cursor() as cursor:
                cursor.execute("DELETE FROM employees WHERE employee_id = %s", (employee_id,))
            results = {"success": True, "message": f"Employee {employee_id} deleted successfully!"}
            logger.info("Employee deleted: id=%s", employee_id)
        except Exception as e:
            results = {"success": False, "message": f"Failed to delete employee: {e}"}
            logger.error("Failed to delete employee: %s", e)

        return render_template("admin/employees.html", employee=None, results=results)

    @app.route("/search_employee", methods=["POST"])
    def search_employee():
        employee_id = request.form["employee_id"]
        results = {}
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
                employee = cursor.fetchone()
            if employee:
                return render_template("admin/employees.html", employee=employee, results=results)
            else:
                results = {"success": False, "message": f"Employee {employee_id} not found."}
                return render_template("admin/employees.html", employee=None, results=results)
        except Exception as e:
            results = {"success": False, "message": f"Failed to search employee: {e}"}
            logger.error("Failed to search employee: %s", e)
            return render_template("admin/employees.html", employee=None, results=results)

    # -----------------------------------------------------------------------
    # Loan Evaluation
    # -----------------------------------------------------------------------
    @app.route("/loan-valuation", methods=["GET", "POST"])
    def loan_valuation():
        result = None
        if request.method == "POST":
            customer_id = request.form["customerId"]
            try:
                result = predict_loan_approval(customer_id)
            except Exception as e:
                result = {"result": "Error", "factors": [str(e)]}
                logger.error("Loan evaluation error: %s", e)
        return render_template("admin/loan.html", result=result)

    # -----------------------------------------------------------------------
    # Customer Segmentation
    # -----------------------------------------------------------------------
    @app.route("/segm", methods=["GET", "POST"])
    def segm():
        if request.method == "POST":
            customer_id = request.form["customerId"]
            try:
                cluster, description = predict_cluster(customer_id)
                return render_template("admin/segmentation.html", results=description)
            except Exception as e:
                return render_template("admin/segmentation.html", results="Customer ID not found.")
        return render_template("admin/segmentation.html", results="")

    # -----------------------------------------------------------------------
    # Transaction History (Admin View)
    # -----------------------------------------------------------------------
    @app.route("/show")
    def transactions():
        try:
            with get_cursor() as cursor:
                cursor.execute("SELECT id, sender_id, receiver_id, amount, date FROM transactions")
                txns = cursor.fetchall()
            return render_template("admin/transactions.html", transactions=txns)
        except Exception as e:
            logger.error("Failed to fetch transactions: %s", e)
            return render_template("Showtransadmin.html", transactions=[])

    # -----------------------------------------------------------------------
    # JSON API Endpoints (for AJAX/JavaScript consumption)
    # -----------------------------------------------------------------------
    from flask import jsonify

    @app.route("/api/customers")
    def api_customers():
        """Return all customers as JSON."""
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id, full_name, gender, age, address, contact_number,
                            annual_income, credit_score, debt_to_income_ratio,
                            occupation, loan_status, insurance_status,
                            ip_address, mac_address, bank_balance
                     FROM customers ORDER BY id"""
                )
                customers = cursor.fetchall()
            return jsonify({"success": True, "data": customers})
        except Exception as e:
            logger.error("Failed to fetch customers: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch customers"}}), 500

    @app.route("/api/customers/<int:customer_id>")
    def api_customer(customer_id):
        """Return a single customer as JSON."""
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id, full_name, gender, age, address, contact_number,
                            annual_income, credit_score, debt_to_income_ratio,
                            occupation, loan_status, insurance_status,
                            ip_address, mac_address, bank_balance
                     FROM customers WHERE id = %s""",
                    (customer_id,),
                )
                customer = cursor.fetchone()
            if not customer:
                return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Customer not found"}}), 404
            return jsonify({"success": True, "data": customer})
        except Exception as e:
            logger.error("Failed to fetch customer %s: %s", customer_id, e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch customer"}}), 500

    @app.route("/api/employees")
    def api_employees():
        """Return all employees as JSON."""
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT employee_id, first_name, last_name, gender, date_of_birth,
                            position, department, hire_date, salary, email,
                            phone_number, address, emergency_contact,
                            emergency_contact_phone, performance_rating, is_active
                     FROM employees ORDER BY employee_id"""
                )
                employees = cursor.fetchall()
            return jsonify({"success": True, "data": employees})
        except Exception as e:
            logger.error("Failed to fetch employees: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch employees"}}), 500

    @app.route("/api/employees/<int:employee_id>")
    def api_employee(employee_id):
        """Return a single employee as JSON."""
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT employee_id, first_name, last_name, gender, date_of_birth,
                            position, department, hire_date, salary, email,
                            phone_number, address, emergency_contact,
                            emergency_contact_phone, performance_rating, is_active
                     FROM employees WHERE employee_id = %s""",
                    (employee_id,),
                )
                employee = cursor.fetchone()
            if not employee:
                return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": "Employee not found"}}), 404
            return jsonify({"success": True, "data": employee})
        except Exception as e:
            logger.error("Failed to fetch employee %s: %s", employee_id, e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch employee"}}), 500

    @app.route("/api/transactions")
    def api_transactions():
        """Return all transactions as JSON (admin view)."""
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id, sender_id, receiver_id, amount, date, status
                     FROM transactions ORDER BY date DESC"""
                )
                transactions = cursor.fetchall()
            # Convert datetime objects to strings for JSON
            for txn in transactions:
                if txn.get("date"):
                    txn["date"] = txn["date"].isoformat()
            return jsonify({"success": True, "data": transactions})
        except Exception as e:
            logger.error("Failed to fetch transactions: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch transactions"}}), 500

    @app.route("/api/stats")
    def api_stats():
        """Return dashboard statistics as JSON."""
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute("SELECT COUNT(*) AS count FROM customers")
                customer_count = cursor.fetchone()["count"]
                cursor.execute("SELECT COUNT(*) AS count FROM employees")
                employee_count = cursor.fetchone()["count"]
                cursor.execute("SELECT COUNT(*) AS count FROM transactions")
                transaction_count = cursor.fetchone()["count"]
                cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM transactions")
                total_amount = float(cursor.fetchone()["total"])
                cursor.execute("SELECT COUNT(*) AS count FROM transactions WHERE status = 'Pending'")
                pending_count = cursor.fetchone()["count"]
                cursor.execute("SELECT COUNT(*) AS count FROM transactions WHERE status = 'Approved'")
                approved_count = cursor.fetchone()["count"]
            return jsonify({
                "success": True,
                "data": {
                    "customers": customer_count,
                    "employees": employee_count,
                    "transactions": transaction_count,
                    "total_amount": total_amount,
                    "pending_transactions": pending_count,
                    "approved_transactions": approved_count,
                },
            })
        except Exception as e:
            logger.error("Failed to fetch stats: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": "Failed to fetch stats"}}), 500

    # -----------------------------------------------------------------------
    # Employee JSON API (CRUD)
    # -----------------------------------------------------------------------
    @app.route("/api/employees/add", methods=["POST"])
    def api_add_employee():
        """Add a new employee via JSON."""
        try:
            data = request.get_json(force=True)
            with get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO employees
                       (first_name, last_name, gender, date_of_birth, position,
                        department, hire_date, salary, email, phone_number,
                        address, emergency_contact, emergency_contact_phone,
                        performance_rating, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        data["first_name"], data["last_name"],
                        data.get("gender", ""), data.get("date_of_birth") or None,
                        data.get("position", ""), data.get("department", ""),
                        data.get("hire_date") or None, data.get("salary", 0),
                        data["email"], data.get("phone_number", ""),
                        data.get("address", ""), data.get("emergency_contact", ""),
                        data.get("emergency_contact_phone", ""),
                        data.get("performance_rating", 0),
                        data.get("is_active", True),
                    ),
                )
            return jsonify({"success": True, "message": "Employee added successfully"})
        except Exception as e:
            logger.error("Failed to add employee: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    @app.route("/api/employees/edit", methods=["POST"])
    def api_edit_employee():
        """Edit an employee via JSON."""
        try:
            data = request.get_json(force=True)
            emp_id = data["employee_id"]
            fields = []
            values = []
            for key in ["first_name", "last_name", "gender", "date_of_birth",
                        "position", "department", "hire_date", "salary", "email",
                        "phone_number", "address", "emergency_contact",
                        "emergency_contact_phone", "performance_rating", "is_active"]:
                if key in data:
                    fields.append(f"{key} = %s")
                    values.append(data[key])
            if not fields:
                return jsonify({"success": False, "error": {"code": "NO_FIELDS", "message": "No fields to update"}}), 400
            values.append(emp_id)
            with get_cursor() as cursor:
                cursor.execute(f"UPDATE employees SET {', '.join(fields)} WHERE employee_id = %s", values)
            return jsonify({"success": True, "message": "Employee updated successfully"})
        except Exception as e:
            logger.error("Failed to edit employee: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    @app.route("/api/employees/delete", methods=["POST"])
    def api_delete_employee():
        """Delete an employee via JSON."""
        try:
            data = request.get_json(force=True)
            emp_id = data["employee_id"]
            with get_cursor() as cursor:
                cursor.execute("DELETE FROM employees WHERE employee_id = %s", (emp_id,))
            return jsonify({"success": True, "message": f"Employee {emp_id} deleted"})
        except Exception as e:
            logger.error("Failed to delete employee: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    @app.route("/api/employees/search", methods=["POST"])
    def api_search_employee():
        """Search for an employee by ID via JSON."""
        try:
            data = request.get_json(force=True)
            emp_id = data["employee_id"]
            with get_cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (emp_id,))
                employee = cursor.fetchone()
            if not employee:
                return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": f"Employee {emp_id} not found"}}), 404
            # Convert date objects to strings
            for key, val in employee.items():
                if hasattr(val, 'isoformat'):
                    employee[key] = val.isoformat()
            return jsonify({"success": True, "data": employee})
        except Exception as e:
            logger.error("Failed to search employee: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    # -----------------------------------------------------------------------
    # Customer JSON API (CRUD)
    # -----------------------------------------------------------------------
    @app.route("/api/customers/add", methods=["POST"])
    def api_add_customer():
        """Add a new customer via JSON."""
        try:
            data = request.get_json(force=True)
            with get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO customers
                       (full_name, gender, age, address, contact_number,
                        annual_income, credit_score, debt_to_income_ratio,
                        occupation, loan_status, insurance_status,
                        ip_address, mac_address, bank_balance, password)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        data["full_name"], data.get("gender", ""),
                        data.get("age"), data.get("address", ""),
                        data.get("contact_number", ""), data.get("annual_income", 0),
                        data.get("credit_score", 0), data.get("debt_to_income_ratio", 0),
                        data.get("occupation", ""), data.get("loan_status", "Rejected"),
                        data.get("insurance_status", "Uninsured"),
                        data.get("ip_address", ""), data.get("mac_address", ""),
                        data.get("bank_balance", 0), data.get("password", ""),
                    ),
                )
            return jsonify({"success": True, "message": "Customer added successfully"})
        except Exception as e:
            logger.error("Failed to add customer: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    @app.route("/api/customers/edit", methods=["POST"])
    def api_edit_customer():
        """Edit a customer via JSON."""
        try:
            data = request.get_json(force=True)
            cust_id = data["id"]
            fields = []
            values = []
            for key in ["full_name", "gender", "age", "address", "contact_number",
                        "annual_income", "credit_score", "debt_to_income_ratio",
                        "occupation", "loan_status", "insurance_status",
                        "ip_address", "mac_address", "bank_balance", "password"]:
                if key in data:
                    fields.append(f"{key} = %s")
                    values.append(data[key])
            if not fields:
                return jsonify({"success": False, "error": {"code": "NO_FIELDS", "message": "No fields to update"}}), 400
            values.append(cust_id)
            with get_cursor() as cursor:
                cursor.execute(f"UPDATE customers SET {', '.join(fields)} WHERE id = %s", values)
            return jsonify({"success": True, "message": "Customer updated successfully"})
        except Exception as e:
            logger.error("Failed to edit customer: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    @app.route("/api/customers/delete", methods=["POST"])
    def api_delete_customer():
        """Delete a customer via JSON."""
        try:
            data = request.get_json(force=True)
            cust_id = data["id"]
            with get_cursor() as cursor:
                cursor.execute("DELETE FROM customers WHERE id = %s", (cust_id,))
            return jsonify({"success": True, "message": f"Customer {cust_id} deleted"})
        except Exception as e:
            logger.error("Failed to delete customer: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    @app.route("/api/customers/search", methods=["POST"])
    def api_search_customer():
        """Search for a customer by ID via JSON."""
        try:
            data = request.get_json(force=True)
            cust_id = data["id"]
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id, full_name, gender, age, address, contact_number,
                            annual_income, credit_score, debt_to_income_ratio,
                            occupation, loan_status, insurance_status,
                            ip_address, mac_address, bank_balance
                     FROM customers WHERE id = %s""",
                    (cust_id,),
                )
                customer = cursor.fetchone()
            if not customer:
                return jsonify({"success": False, "error": {"code": "NOT_FOUND", "message": f"Customer {cust_id} not found"}}), 404
            return jsonify({"success": True, "data": customer})
        except Exception as e:
            logger.error("Failed to search customer: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    # -----------------------------------------------------------------------
    # Loan Evaluation JSON API
    # -----------------------------------------------------------------------
    @app.route("/api/loan/evaluate", methods=["POST"])
    def api_loan_evaluate():
        """Evaluate loan approval for a customer."""
        try:
            data = request.get_json(force=True)
            customer_id = data["customer_id"]
            result = predict_loan_approval(customer_id)
            return jsonify({"success": True, "data": result})
        except Exception as e:
            logger.error("Loan evaluation failed: %s", e)
            return jsonify({"success": False, "error": {"code": "ML_ERROR", "message": str(e)}}), 500

    # -----------------------------------------------------------------------
    # Customer Segmentation JSON API
    # -----------------------------------------------------------------------
    @app.route("/api/segmentation/predict", methods=["POST"])
    def api_segmentation_predict():
        """Predict customer segment."""
        try:
            from services.segmentation_model import predict_cluster
            data = request.get_json(force=True)
            customer_id = data["customer_id"]
            cluster, description = predict_cluster(customer_id)
            return jsonify({"success": True, "data": {"cluster": cluster, "description": description, "customer_id": customer_id}})
        except Exception as e:
            logger.error("Segmentation failed: %s", e)
            return jsonify({"success": False, "error": {"code": "ML_ERROR", "message": str(e)}}), 500

    # -----------------------------------------------------------------------
    # Fraud Detection JSON API
    # -----------------------------------------------------------------------
    @app.route("/api/fraud/pending", methods=["GET"])
    def api_fraud_pending():
        """Get pending fraud transactions."""
        try:
            with get_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT id AS transaction_id, sender_id, receiver_id, amount, date, status
                     FROM transactions WHERE status = 'Pending' ORDER BY date DESC"""
                )
                transactions = cursor.fetchall()
            for txn in transactions:
                if txn.get("date"):
                    txn["date"] = txn["date"].isoformat()
            return jsonify({"success": True, "data": transactions})
        except Exception as e:
            logger.error("Failed to fetch pending fraud transactions: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    @app.route("/api/fraud/decide", methods=["POST"])
    def api_fraud_decide():
        """Approve or reject a flagged transaction."""
        try:
            data = request.get_json(force=True)
            txn_id = data["transaction_id"]
            decision = data["decision"]  # "approve" or "reject"
            new_status = "Approved" if decision == "approve" else "Rejected"
            with get_cursor() as cursor:
                cursor.execute("UPDATE transactions SET status = %s WHERE id = %s", (new_status, txn_id))
            return jsonify({"success": True, "message": f"Transaction {txn_id} {new_status.lower()}"})
        except Exception as e:
            logger.error("Failed to process fraud decision: %s", e)
            return jsonify({"success": False, "error": {"code": "DB_ERROR", "message": str(e)}}), 500

    # -----------------------------------------------------------------------
    # Health Check
    # -----------------------------------------------------------------------
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "service": "admin"})

    return app


# ---------------------------------------------------------------------------
# Direct run support
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    settings = get_settings()
    app = create_admin_app()
    app.run(
        host=settings.admin_app.host,
        port=settings.admin_app.port,
        debug=settings.admin_app.debug,
    )
