from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from sqlalchemy import create_engine
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

app = Flask(__name__)

# =============================================================================
# Database configuration (single source of truth)
# =============================================================================
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'IAMVENU123',
    'database': 'cbss'
}


def get_db_connection():
    """Return a mysql.connector connection using db_config."""
    return mysql.connector.connect(**db_config)


def get_sqlalchemy_engine():
    """Return a SQLAlchemy engine for pandas read_sql usage."""
    return create_engine(
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}/{db_config['database']}"
    )


# =============================================================================
# Root & Customer Management Routes
# =============================================================================

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/cust')
def cust():
    return render_template('customer.html', results=None)


@app.route('/add_customer', methods=['POST'])
def add_customer():
    try:
        full_name = request.form.get('addFullName')
        gender = request.form.get('addGender')
        age = request.form.get('addAge')
        address = request.form.get('addAddress')
        contact_number = request.form.get('addContactNumber')
        annual_income = request.form.get('addAnnualIncome')
        credit_score = request.form.get('addCreditScore')
        debt_to_income_ratio = request.form.get('addDebtToIncomeRatio')
        occupation = request.form.get('addOccupation')
        loan_status = request.form.get('addLoanStatus')
        insurance_status = request.form.get('addInsuranceStatus')
        ip_address = request.form.get('addIpAddress')
        mac_address = request.form.get('addMacAddress')
        bank_balance = request.form.get('addBankBalance')
        password = request.form.get('addPassword')

        connection = get_db_connection()
        cursor = connection.cursor()
        query = """INSERT INTO customers (full_name, gender, age, address, contact_number, annual_income,
                   credit_score, debt_to_income_ratio, occupation, loan_status, insurance_status, ip_address,
                   mac_address, bank_balance, password)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (full_name, gender, age, address, contact_number, annual_income, credit_score,
                               debt_to_income_ratio, occupation, loan_status, insurance_status, ip_address,
                               mac_address, bank_balance, password))
        connection.commit()
        results = {'message': 'Customer added successfully!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)


@app.route('/edit_customer', methods=['POST'])
def edit_customer():
    try:
        customer_id = request.form.get('editId')
        full_name = request.form.get('editFullName')
        gender = request.form.get('editGender')
        age = request.form.get('editAge')
        address = request.form.get('editAddress')
        contact_number = request.form.get('editContactNumber')
        annual_income = request.form.get('editAnnualIncome')
        credit_score = request.form.get('editCreditScore')
        debt_to_income_ratio = request.form.get('editDebtToIncomeRatio')
        occupation = request.form.get('editOccupation')
        loan_status = request.form.get('editLoanStatus')
        insurance_status = request.form.get('editInsuranceStatus')
        ip_address = request.form.get('editIpAddress')
        mac_address = request.form.get('editMacAddress')
        bank_balance = request.form.get('editBankBalance')
        password = request.form.get('editPassword')

        connection = get_db_connection()
        cursor = connection.cursor()
        query = """UPDATE customers SET full_name = %s, gender = %s, age = %s, address = %s, contact_number = %s,
                   annual_income = %s, credit_score = %s, debt_to_income_ratio = %s, occupation = %s, loan_status = %s,
                   insurance_status = %s, ip_address = %s, mac_address = %s, bank_balance = %s, password = %s
                   WHERE id = %s"""
        cursor.execute(query, (full_name, gender, age, address, contact_number, annual_income, credit_score,
                               debt_to_income_ratio, occupation, loan_status, insurance_status, ip_address,
                               mac_address, bank_balance, password, customer_id))
        connection.commit()
        results = {'message': 'Customer updated successfully!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)


@app.route('/delete_customer', methods=['POST'])
def delete_customer():
    try:
        customer_id = request.form.get('deleteCustomerID')
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
        connection.commit()
        results = {'message': 'Customer deleted successfully!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)


@app.route('/search_customer', methods=['POST'])
def search_customer():
    customer_id = request.form.get('searchCustomerID')
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        result = cursor.fetchone()
        if result:
            results = {
                'id': result[0], 'full_name': result[1], 'gender': result[2],
                'age': result[3], 'address': result[4], 'contact_number': result[5],
                'annual_income': result[6], 'credit_score': result[7],
                'debt_to_income_ratio': result[8], 'occupation': result[9],
                'loan_status': result[10], 'insurance_status': result[11],
                'ip_address': result[12], 'mac_address': result[13],
                'bank_balance': result[14], 'password': result[15]
            }
        else:
            results = {'message': 'Customer not found!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)


# =============================================================================
# Employee Management Routes
# =============================================================================

@app.route('/emp')
def emp():
    return render_template('employee.html')


@app.route('/add_employee', methods=['POST'])
def add_employee():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    gender = request.form['gender']
    dob = request.form['date_of_birth']
    position = request.form['position']
    department = request.form['department']
    hire_date = request.form['hire_date']
    salary = request.form['salary']
    email = request.form['email']
    phone = request.form['phone_number']
    address = request.form['address']
    emergency_contact = request.form['emergency_contact']
    emergency_phone = request.form['emergency_phone_number']
    performance_rating = request.form['performance_rating']

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO employees (first_name, last_name, gender, date_of_birth, position, department,
                               hire_date, salary, email, phone_number, address, emergency_contact,
                               emergency_contact_phone, performance_rating)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (first_name, last_name, gender, dob, position, department, hire_date, salary, email, phone,
          address, emergency_contact, emergency_phone, performance_rating))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('emp'))


@app.route('/edit_employee', methods=['POST'])
def edit_employee():
    employee_id = request.form['employee_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    gender = request.form['gender']
    dob = request.form['date_of_birth']
    position = request.form['position']
    department = request.form['department']
    hire_date = request.form['hire_date']
    salary = request.form['salary']
    email = request.form['email']
    phone = request.form['phone_number']
    address = request.form['address']
    emergency_contact = request.form['emergency_contact']
    emergency_phone = request.form['emergency_phone_number']
    performance_rating = request.form['performance_rating']
    is_active = request.form['is_active']

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE employees
        SET first_name = %s, last_name = %s, gender = %s, date_of_birth = %s, position = %s, department = %s,
            hire_date = %s, salary = %s, email = %s, phone_number = %s, address = %s, emergency_contact = %s,
            emergency_contact_phone = %s, performance_rating = %s, is_active = %s
        WHERE employee_id = %s
    """, (first_name, last_name, gender, dob, position, department, hire_date, salary, email, phone, address,
          emergency_contact, emergency_phone, performance_rating, is_active, employee_id))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('emp'))


@app.route('/delete_employee', methods=['POST'])
def delete_employee():
    employee_id = request.form['employee_id']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM employees WHERE employee_id = %s", (employee_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('emp'))


@app.route('/search_employee', methods=['POST'])
def search_employee():
    employee_id = request.form['employee_id']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
    employee = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('employee.html', employee=employee)


# =============================================================================
# Loan Evaluation (ML Model)
# =============================================================================

def load_and_train_loan_model():
    """Load customer data and train the loan approval Decision Tree model."""
    engine = get_sqlalchemy_engine()
    query = """
    SELECT id, full_name, age, annual_income, credit_score, debt_to_income_ratio,
           occupation, loan_status, insurance_status FROM customers;
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    df['loan_status'] = df['loan_status'].map({'Approved': 1, 'Pending': 0, 'Rejected': -1})
    df['insurance_status'] = df['insurance_status'].map({'Insured': 1, 'Uninsured': 0})

    df = df[['age', 'annual_income', 'credit_score', 'debt_to_income_ratio',
             'occupation', 'insurance_status', 'loan_status']]
    df = pd.get_dummies(df, columns=['occupation'], drop_first=True)

    X = df.drop(['loan_status'], axis=1)
    y = df['loan_status']

    model = DecisionTreeClassifier(random_state=42)
    model.fit(X, y)
    return model, X


# Train at startup (requires DB to be available)
loan_model, loan_features = load_and_train_loan_model()


def predict_loan_approval(customer_id):
    """Predict loan approval for a given customer ID using the trained model."""
    try:
        engine = get_sqlalchemy_engine()
        query = """
        SELECT age, annual_income, credit_score, debt_to_income_ratio, occupation, insurance_status
        FROM customers WHERE id = %s;
        """
        with engine.connect() as conn:
            customer_data = pd.read_sql(query, conn, params=(customer_id,))

        if customer_data.empty:
            return "Customer ID not found."

        customer_data['insurance_status'] = (
            1 if customer_data['insurance_status'].values[0] == 'Insured' else 0
        )

        customer_df = pd.DataFrame([{
            'age': customer_data['age'].values[0],
            'annual_income': customer_data['annual_income'].values[0],
            'credit_score': customer_data['credit_score'].values[0],
            'debt_to_income_ratio': customer_data['debt_to_income_ratio'].values[0],
            'insurance_status': customer_data['insurance_status']
        }])

        if 'occupation' in customer_data.columns:
            customer_df['occupation'] = customer_data['occupation'].values[0]
            customer_df = pd.get_dummies(customer_df, columns=['occupation'], drop_first=True)

        for col in loan_features.columns:
            if col not in customer_df.columns:
                customer_df[col] = 0

        features = customer_df[loan_features.columns]
        prediction = loan_model.predict(features)

        status_map = {1: "Approved", 0: "Pending", -1: "Rejected"}
        return status_map.get(prediction[0], "Unknown Status")
    except Exception as e:
        return f"Error in prediction: {e}"


@app.route('/loan-valuation', methods=['GET', 'POST'])
def loan_valuation():
    result = None
    if request.method == 'POST':
        customer_id = request.form['customerId']
        result = predict_loan_approval(customer_id)
    return render_template('loan.html', result=result)


# =============================================================================
# Customer Segmentation (KMeans Clustering)
# =============================================================================

def get_customer_data_by_id(customer_id):
    """Fetch a single customer's features for clustering."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT age, annual_income, credit_score, debt_to_income_ratio, bank_balance
        FROM customers WHERE id = %s;
    """, (customer_id,))
    customer_data = cursor.fetchone()
    cursor.close()
    connection.close()
    return pd.DataFrame([customer_data]) if customer_data else None


def get_all_customer_data():
    """Fetch all customers' features for fitting the KMeans model."""
    engine = get_sqlalchemy_engine()
    query = "SELECT age, annual_income, credit_score, debt_to_income_ratio, bank_balance FROM customers;"
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


def fit_kmeans(full_data):
    """Fit KMeans on the full customer dataset and return model + scaler."""
    features = full_data[['age', 'annual_income', 'credit_score', 'debt_to_income_ratio', 'bank_balance']]
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=4, random_state=42)
    full_data['cluster'] = kmeans.fit_predict(features_scaled)
    return full_data, kmeans, scaler


def get_customer_cluster(kmeans, scaler, customer_data):
    """Predict the cluster for a single customer."""
    features = customer_data[['age', 'annual_income', 'credit_score', 'debt_to_income_ratio', 'bank_balance']]
    input_scaled = scaler.transform(features)
    return kmeans.predict(input_scaled)[0]


cluster_descriptions = {
    0: "Young, low income, high debt-to-income ratio (potentially risky customers).",
    1: "Middle-aged, high income, good credit score (financially stable customers).",
    2: "Older customers with moderate income and low debt (retirement-focused customers).",
    3: "Young professionals with good incomes but still building credit (emerging customers)."
}


@app.route('/segm', methods=['GET', 'POST'])
def segm():
    if request.method == 'POST':
        customer_id = request.form['customerId']
        customer_data = get_customer_data_by_id(customer_id)

        if customer_data is not None:
            full_data = get_all_customer_data()
            segmented_data, kmeans, scaler = fit_kmeans(full_data)
            cluster = get_customer_cluster(kmeans, scaler, customer_data)
            result_description = cluster_descriptions[cluster]
            return render_template('segm.html', results=result_description)

        return render_template('segm.html', results="Customer ID not found.")
    return render_template('segm.html', results="")


# =============================================================================
# Transaction History (Admin View)
# =============================================================================

@app.route('/show')
def transactions():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, sender_id, receiver_id, amount, date FROM transactions")
    transactions = cursor.fetchall()
    connection.close()
    return render_template('Showtransadmin.html', transactions=transactions)


@app.route('/admin')
def client_dashboard():
    return render_template('login1.html')


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True)
