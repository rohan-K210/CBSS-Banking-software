import random
import uuid
from datetime import datetime, timedelta
import csv
import faker

# Create a Faker instance for generating realistic data
fake = faker.Faker()

# Define a function to generate random IP and MAC addresses
def generate_ip():
    return fake.ipv4()

def generate_mac():
    return fake.mac_address()

# Define a function to generate demo transactions
def generate_transactions(num_normal=800, num_abnormal=200, output_file="demo_transactions.csv"):
    transactions = []

    # Generate normal transactions
    for _ in range(num_normal):
        transaction_id = str(uuid.uuid4())  # Unique transaction ID
        sender_id = random.randint(1, 10)  # Random sender ID
        receiver_id = random.randint(1, 10)  # Random receiver ID
        while receiver_id == sender_id:  # Ensure sender and receiver are not the same
            receiver_id = random.randint(1, 10)
        amount = round(random.uniform(10, 1000), 2)  # Reasonable amount
        date = datetime.now() - timedelta(days=random.randint(1, 30))  # Last 30 days
        sender_ip = generate_ip()
        sender_mac = generate_mac()
        receiver_ip = generate_ip()
        receiver_mac = generate_mac()
        label = "normal"  # Label for normal transactions

        transactions.append([transaction_id, sender_id, receiver_id, amount, date, sender_ip, sender_mac, receiver_ip, receiver_mac, label])

    # Generate abnormal (fraudulent) transactions
    for _ in range(num_abnormal):
        transaction_id = str(uuid.uuid4())  # Unique transaction ID
        sender_id = random.randint(1, 10)
        receiver_id = random.randint(1, 10)
        while receiver_id == sender_id:  # Ensure sender and receiver are not the same
            receiver_id = random.randint(1, 10)
        amount = round(random.uniform(1000, 10000), 2)  # Unusually high amount
        date = datetime.now() - timedelta(days=random.randint(1, 7))  # More recent
        if random.random() < 0.5:  # 50% chance of suspicious IP/MAC
            sender_ip = "192.168.1.100"
            sender_mac = "00:14:22:01:23:45"
            receiver_ip = "10.0.0.1"
            receiver_mac = "00:14:22:01:23:46"
        else:
            sender_ip = generate_ip()
            sender_mac = generate_mac()
            receiver_ip = generate_ip()
            receiver_mac = generate_mac()
        label = "abnormal"  # Label for fraudulent transactions

        transactions.append([transaction_id, sender_id, receiver_id, amount, date, sender_ip, sender_mac, receiver_ip, receiver_mac, label])

    # Write transactions to a CSV file
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Transaction ID", "Sender ID", "Receiver ID", "Amount", "Date", "Sender IP", "Sender MAC", "Receiver IP", "Receiver MAC", "Label"])
        writer.writerows(transactions)

    print(f"Generated {num_normal + num_abnormal} transactions and saved to {output_file}")

# Generate transactions and save them to a CSV file
generate_transactions()
