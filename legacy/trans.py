import uuid
import pandas as pd  # Ensure pandas is imported
from flask import Flask, request, render_template, redirect, url_for, session, flash
from mysql.connector import connect
from datetime import datetime
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session handling

# Database connection details
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'IAMVENU123',
    'database': 'cbss'
}

# Route for login form and login processing
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        password = request.form.get('password')

        # SQL query to fetch the password from the database for the given customer ID
        query = '''SELECT id, password FROM customers WHERE id = %s'''
        connection = connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()

        # Check if customer exists and the password matches (plain text comparison)
        if result and result[1] == password:  # Compare the stored password with the entered password
            session['sender_id'] = result[0]  # Store sender_id in session
            return redirect(url_for('client'))  # Redirect to the client dashboard
        else:
            flash("Invalid customer ID or password.", "error")
            return redirect(url_for('login'))

    # Render the login form
    return render_template('login2.html')

# Route to render the form and handle form submission for transactions
@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'sender_id' not in session:  # Ensure the user is logged in
        flash("You must log in first.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get receiver_id and amount from the form
        receiver_id = request.form.get('receiver_id')
        amount = float(request.form.get('amount'))
        date = datetime.now()

        # Retrieve sender_id from the session
        sender_id = session['sender_id']

        # Generate a unique transaction ID using UUID
        transaction_id = str(uuid.uuid4())  # Generate a unique UUID

        # Retrieve IP and MAC addresses of sender from customer table
        connection = connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Fetch sender details
        cursor.execute("SELECT ip_address, mac_address FROM customers WHERE id = %s", (sender_id,))
        sender_details = cursor.fetchone()
        sender_ip = sender_details['ip_address'] if sender_details else "Unknown"
        sender_mac = sender_details['mac_address'] if sender_details else "Unknown"

        # Fetch receiver details
        cursor.execute("SELECT ip_address, mac_address FROM customers WHERE id = %s", (receiver_id,))
        receiver_details = cursor.fetchone()
        receiver_ip = receiver_details['ip_address'] if receiver_details else "Unknown"
        receiver_mac = receiver_details['mac_address'] if receiver_details else "Unknown"

        # Apply fraud detection model
        # Retrieve previous transactions of the sender and receiver for analysis
        query = """
        SELECT sender_id, receiver_id, amount, date FROM transactions WHERE sender_id = %s OR receiver_id = %s
        """
        cursor.execute(query, (sender_id, receiver_id))
        previous_transactions = cursor.fetchall()

        # Convert transactions to a pandas DataFrame
        df = pd.DataFrame(previous_transactions, columns=['sender_id', 'receiver_id', 'amount', 'date'])

        # Feature engineering (based on previous transactions)
        df['date'] = pd.to_datetime(df['date'])
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_large_transaction'] = df['amount'].apply(lambda x: 1 if x > 10000 else 0)  # Example feature

        # Use Decision Tree for fraud detection
        model = DecisionTreeClassifier()
        encoder = LabelEncoder()

        # Encode sender and receiver IDs
        df['sender_id_encoded'] = encoder.fit_transform(df['sender_id'])
        df['receiver_id_encoded'] = encoder.fit_transform(df['receiver_id'])

        # Prepare features and target
        X = df[['sender_id_encoded', 'receiver_id_encoded', 'amount', 'hour', 'day_of_week', 'is_large_transaction']]
        y = df['is_large_transaction']  # Example target: fraudulent transactions

        # Train model (for simplicity, we use all data as both training and testing here)
        model.fit(X, y)

        # Predict if the new transaction is potentially fraudulent
        new_transaction_data = {
            'sender_id_encoded': encoder.transform([sender_id])[0],
            'receiver_id_encoded': encoder.transform([receiver_id])[0],
            'amount': amount,
            'hour': date.hour,
            'day_of_week': date.weekday(),
            'is_large_transaction': 1 if amount > 10000 else 0
        }

        new_transaction_df = pd.DataFrame([new_transaction_data])
        prediction = model.predict(new_transaction_df)

        # If the model predicts fraud (1), mark the transaction as pending
        if prediction[0] == 1:
            # Insert transaction with 'Pending' status for fraud review
            status = 'Pending'
        else:
            # Insert transaction with 'Approved' status
            status = 'Approved'

        # SQL query to insert transaction (include generated transaction_id and status)
        query = """
        INSERT INTO transactions (id, sender_id, receiver_id, amount, date, sender_ip_address, sender_mac_address, receiver_ip_address, receiver_mac_address, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (transaction_id, sender_id, receiver_id, amount, date, sender_ip, sender_mac, receiver_ip, receiver_mac, status))
        connection.commit()

        # Close the database connection
        cursor.close()
        connection.close()

        # Redirect to a success page, passing the transaction ID
        flash(f"Transaction added successfully! Transaction ID: {transaction_id}", "success")
        return redirect(url_for('transaction_success', transaction_id=transaction_id))

    # Render the form template on GET request
    return render_template('MAKETRANSCLIENT.html')

# Success page for transaction
@app.route('/transaction_success')
def transaction_success():
    # Get transaction ID from the URL
    transaction_id = request.args.get('transaction_id')
    return f"Transaction added successfully! Transaction ID: {transaction_id}"

# Route for logout
@app.route('/logout')
def logout():
    session.pop('sender_id', None)  # Remove sender_id from session
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Route to display client dashboard
@app.route('/client')
def client():
    if 'sender_id' not in session:  # Ensure the user is logged in
        flash("You must log in first.", "warning")
        return redirect(url_for('login'))
    
    return render_template('client1.html')

# Route to show fraudulent transactions (to be reviewed)
@app.route('/fraud', methods=['GET', 'POST'])
def fraud():
    if 'sender_id' not in session:
        flash("You must log in first.", "warning")
        return redirect(url_for('login'))

    # Example: Fetch fraudulent transactions for review
    connection = connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''SELECT transaction_id, sender_id, receiver_id, amount, date FROM transactions WHERE status = 'Pending' ''')
    transactions = cursor.fetchall()

    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        decision = request.form.get('decision')

        # Update transaction status based on decision (approve or reject)
        if decision == 'approve':
            cursor.execute('''UPDATE transactions SET status = 'Approved' WHERE transaction_id = %s''', (transaction_id,))
            flash(f"Transaction {transaction_id} approved.", "success")
        elif decision == 'reject':
            cursor.execute('''UPDATE transactions SET status = 'Rejected' WHERE transaction_id = %s''', (transaction_id,))
            flash(f"Transaction {transaction_id} rejected.", "danger")
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('fraud'))  # Refresh the fraud page after processing the decision

    # Render the fraud page with fraudulent transactions
    return render_template('fraud.html', transactions=transactions)

# Route to show all transactions for the logged-in client
@app.route('/show')
def transactions():
    if 'sender_id' not in session:
        flash("You must log in first.", "warning")
        return redirect(url_for('login'))
    
    sender_id = session['sender_id']

    # SQL query to get transactions where the client is either sender or receiver
    query = """SELECT id, receiver_id, amount, date, status FROM transactions WHERE sender_id = %s"""
    connection = connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute(query, (sender_id,))
    transactions = cursor.fetchall()
    connection.close()

    # Pass the transactions data to the template
    return render_template('Showtrans.html', transactions=transactions)

if __name__ == "__main__":
    app.run(debug=True)
