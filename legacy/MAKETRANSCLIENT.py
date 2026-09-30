import uuid
from flask import Flask, request, render_template, redirect, url_for, session, flash
from mysql.connector import connect
from datetime import datetime

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
            return redirect(url_for('client'))
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
        amount = request.form.get('amount')
        date = datetime.now()

        # Retrieve sender_id from the session
        global sender_id
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

        # SQL query to insert transaction (include generated transaction_id)
        query = """
        INSERT INTO transactions (id, sender_id, receiver_id, amount, date, sender_ip_address, sender_mac_address, receiver_ip_address, receiver_mac_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Execute the query with additional fields for IP and MAC addresses
        cursor.execute(query, (transaction_id, sender_id, receiver_id, amount, date, sender_ip, sender_mac, receiver_ip, receiver_mac))
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


@app.route('/client')
def client():
    return render_template('client1.html')


from flask import Flask, render_template
from mysql.connector import connect


# Route to display transaction history for a specific client (Client ID = 2)
@app.route('/show')
def transactions():
      # Client ID to filter by
    sender_id = session['sender_id']


    # SQL query to get transactions where the client is either sender or receiver
    query = """
   SELECT id,receiver_id,amount,date FROM TRANSACTIONS WHERE sender_id=%s
    """

    # Database connection and query execution
    connection = connect(
        host="localhost",
        user="root",
        password="IAMVENU123",
        database="cbss"
    )
    cursor = connection.cursor()
    cursor.execute(query,(sender_id,))
    transactions = cursor.fetchall()
    connection.close()

    # Pass the transactions data to the template
    return render_template('Showtrans.html', transactions=transactions)

# Route for the client dashboard (you can adjust this as needed)



if __name__ == "__main__":
    app.run(debug=True)
