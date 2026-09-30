from flask import Flask, request, render_template, redirect, url_for, flash, session
from sklearn.tree import DecisionTreeClassifier
import mysql.connector
import pandas as pd
import random
import datetime
import ipaddress
from sklearn.model_selection import train_test_split

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

# Train model with real and fake data
def train_model():
    # Fetch legitimate transactions where sender_id = 2 (Customer 2's real transactions)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT sender_id, receiver_id, amount, sender_ip_address, receiver_ip_address, sender_mac_address, receiver_mac_address
        FROM transactions WHERE sender_id = 2
    """)
    transactions = cursor.fetchall()
    cursor.close()
    connection.close()

    # Process legitimate transactions
    real_data = []
    for txn in transactions:
        sender_ip = txn[3] if txn[3] else "0.0.0.0"  # Default to "0.0.0.0" if None
        receiver_ip = txn[4] if txn[4] else "0.0.0.0"  # Default to "0.0.0.0" if None
        sender_mac = txn[5] if txn[5] else "00:00:00:00:00:00"  # Default to "00:00:00:00:00:00" if None
        receiver_mac = txn[6] if txn[6] else "00:00:00:00:00:00"  # Default to "00:00:00:00:00:00" if None
        real_data.append({
            'sender_id': txn[0],
            'receiver_id': txn[1],
            'amount': txn[2],
            'sender_ip': sender_ip,
            'receiver_ip': receiver_ip,
            'sender_mac': sender_mac,
            'receiver_mac': receiver_mac
        })
    
    # Now we generate fake transactions (fraud data) with altered details
    fake_data = []
    for _ in range(100):  # Generate 100 fake fraud cases to balance the classes
        sender_ip = "192.168.99.99"  # Suspicious IP
        receiver_ip = "0.0.0.0"  # Hacker IP
        sender_mac = "00:00:00:00:00:00"  # Suspicious MAC
        receiver_mac = "FF:FF:FF:FF:FF:FF"  # Fake MAC address
        amount = random.randint(100, 1000)  # Random large amount to simulate fraud
        
        fake_data.append({
            'sender_id': 2,
            'receiver_id': 0,  # Fraudulent transaction (receiver_id = 0)
            'amount': amount,
            'sender_ip': sender_ip,
            'receiver_ip': receiver_ip,
            'sender_mac': sender_mac,
            'receiver_mac': receiver_mac
        })

    # Combine real and fake data
    all_data = real_data + fake_data
    labels = [0] * len(real_data) + [1] * len(fake_data)  # 0 for real, 1 for fake

    # Convert data to DataFrame
    df = pd.DataFrame(all_data)

    # Preprocess data (convert IPs to integers and MACs to integers, etc.)
    # Add checks for None values
    df['sender_ip'] = df['sender_ip'].apply(lambda x: int(ipaddress.IPv4Address(x)) if x != "0.0.0.0" else 0)
    df['receiver_ip'] = df['receiver_ip'].apply(lambda x: int(ipaddress.IPv4Address(x)) if x != "0.0.0.0" else 0)
    df['sender_mac'] = df['sender_mac'].apply(lambda x: int(x.replace(":", ""), 16) if x != "00:00:00:00:00:00" else 0)
    df['receiver_mac'] = df['receiver_mac'].apply(lambda x: int(x.replace(":", ""), 16) if x != "00:00:00:00:00:00" else 0)

    # Features and labels
    X = df[['sender_id', 'receiver_id', 'amount', 'sender_ip', 'receiver_ip', 'sender_mac', 'receiver_mac']]
    y = labels

    # Train-test split to evaluate model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train model with balanced class weights
    model = DecisionTreeClassifier(class_weight='balanced', max_depth=5)
    model.fit(X_train, y_train)

    # Check accuracy on the test set
    accuracy = model.score(X_test, y_test)
    print(f"Model accuracy: {accuracy * 100:.2f}%")  # Print test accuracy

    return model, X.columns

model, feature_names = train_model()

@app.route("/hacker", methods=["POST"])
def attack():
    # Extract attack details from form
    receiver_id = 0  # Hacker's ID
    sender_id = 2    # Customer 2's ID
    amount = float(request.form['amount'])

    # Same IP and MAC for sender and receiver (set to null-equivalent values if receiver is hacker)
    mac_address = "00:00:00:00:00:00" if receiver_id == 0 else "00:11:22:33:44:55"
    ip_address = "0.0.0.0" if receiver_id == 0 else "192.168.1.100"
    date = datetime.datetime.now()
    transaction_id = str(random.randint(100000, 999999))  # Simple random ID

    # Prepare the transaction for prediction
    transaction_data = pd.DataFrame([{
        'sender_id': sender_id,
        'receiver_id': receiver_id if receiver_id != 0 else None,  # Use None for NULL in the database
        'amount': amount,
        'sender_ip': int(ipaddress.IPv4Address(ip_address)),
        'receiver_ip': int(ipaddress.IPv4Address(ip_address)) if receiver_id != 0 else None,
        'sender_mac': int(mac_address.replace(':', ''), 16),
        'receiver_mac': int(mac_address.replace(':', ''), 16) if receiver_id != 0 else None
    }])

    # Reorder columns to match training data
    transaction_data = transaction_data[feature_names]

    # Predict using the model
    prediction = model.predict(transaction_data)[0]  
    status = "success" if prediction == 1 else "blocked"
    
    # Save transaction to database
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('''    
        INSERT INTO transactions (id, sender_id, receiver_id, amount, date, sender_ip_address, 
        sender_mac_address, receiver_ip_address, receiver_mac_address, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (transaction_id, sender_id, receiver_id if receiver_id != 0 else None, amount, date, ip_address, mac_address, ip_address if receiver_id != 0 else None, mac_address if receiver_id != 0 else None, status))
    connection.commit()
    cursor.close()
    connection.close()
    
    # Render result in hacker.html
    return render_template("hacker.html", status=status)


@app.route("/hacker")
def hacker():
    return render_template("hacker.html")


if __name__ == '__main__':
    app.run(debug=True)
