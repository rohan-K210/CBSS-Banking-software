from flask import Flask, request, render_template, flash
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import mysql.connector
import pandas as pd
import ipaddress
import random
import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'IAMVENU123'  # Replace with your MySQL password
DB_NAME = 'CBSS'

# Connect to MySQL database
def get_db_connection():
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return connection

# Preprocess Data
def preprocess_data(df):
    df['sender_ip'] = df['sender_ip'].apply(lambda x: int(ipaddress.IPv4Address(x)) if pd.notnull(x) else 0)
    df['receiver_ip'] = df['receiver_ip'].apply(lambda x: int(ipaddress.IPv4Address(x)) if pd.notnull(x) else 0)
    df['sender_mac'] = df['sender_mac'].apply(lambda x: int(x.replace(':', ''), 16) if pd.notnull(x) else 0)
    df['receiver_mac'] = df['receiver_mac'].apply(lambda x: int(x.replace(':', ''), 16) if pd.notnull(x) else 0)
    return df

# Train the Fraud Detection Model
def train_model():
    connection = get_db_connection()
    query = "SELECT * FROM transactions WHERE sender_id = 2"
    transactions = pd.read_sql(query, connection)
    connection.close()
    
    transactions = transactions.rename(columns={
        'sender_ip_address': 'sender_ip',
        'receiver_ip_address': 'receiver_ip',
        'sender_mac_address': 'sender_mac',
        'receiver_mac_address': 'receiver_mac'
    })
    transactions = preprocess_data(transactions)
    
    X = transactions.drop(columns=['id', 'date', 'status'])
    y = transactions['status'].apply(lambda x: 1 if x == 'Blocked' else 0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)
    
    return model

# Initialize Model
model = train_model()

# Routes
@app.route("/")
def home():
    return render_template("hacker.html")

@app.route("/hacker", methods=["POST"])
def attack():
    # Extract attack details from form
    receiver_id = 0  # Hacker's ID
    sender_id = 2    # Customer 2's ID
    amount = float(request.form['amount'])

    # Same IP and MAC for sender and receiver
    mac_address = "00:11:22:33:44:55"
    ip_address = "192.168.1.100"
    date = datetime.datetime.now()
    transaction_id = str(random.randint(100000, 999999))  # Simple random ID

    # Prepare the transaction for prediction
    transaction_data = pd.DataFrame([{
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'amount': amount,
        'sender_ip': int(ipaddress.IPv4Address(ip_address)),
        'receiver_ip': int(ipaddress.IPv4Address(ip_address)),
        'sender_mac': int(mac_address.replace(':', ''), 16),
        'receiver_mac': int(mac_address.replace(':', ''), 16)
    }])
    
    # Predict using the model
    prediction = model.predict(transaction_data)[0]  # 0: Success, 1: Blocked
    status = "Blocked" if prediction == 1 else "Success"
    
    # Save transaction to database
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO transactions (id, sender_id, receiver_id, amount, date, sender_ip_address, 
        sender_mac_address, receiver_ip_address, receiver_mac_address, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (transaction_id, sender_id, receiver_id, amount, date, ip_address, mac_address, ip_address, mac_address, status))
    connection.commit()
    cursor.close()
    connection.close()
    
    # Render result in hacker.html
    return render_template("hacker.html", status=status)

if __name__ == '__main__':
    app.run(debug=True)
