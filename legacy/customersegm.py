from flask import Flask, render_template, request
import mysql.connector
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

app = Flask(__name__)

# Database connection details
def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='IAMVENU123',
        database='cbss'
    )

# Fetch customer data by ID for clustering
def get_customer_data_by_id(customer_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT age, annual_income, credit_score, debt_to_income_ratio, bank_balance
        FROM customers
        WHERE id = %s;
    """
    cursor.execute(query, (customer_id,))
    customer_data = cursor.fetchone()
    cursor.close()
    connection.close()

    if customer_data:
        return pd.DataFrame([customer_data])
    else:
        return None

# Fetch all customer data
def get_all_customer_data():
    connection = get_connection()
    query = "SELECT age, annual_income, credit_score, debt_to_income_ratio, bank_balance FROM customers;"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

# Fit K-Means model on customer data
def fit_kmeans(full_data):
    features = full_data[['age', 'annual_income', 'credit_score', 'debt_to_income_ratio', 'bank_balance']]
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    optimal_k = 4  # Number of clusters
    kmeans = KMeans(n_clusters=optimal_k, random_state=42)
    full_data['cluster'] = kmeans.fit_predict(features_scaled)

    return full_data, kmeans, scaler

# Get cluster assignment for a specific customer
def get_customer_cluster(kmeans, scaler, customer_data):
    features = customer_data[['age', 'annual_income', 'credit_score', 'debt_to_income_ratio', 'bank_balance']]
    input_scaled = scaler.transform(features)
    cluster = kmeans.predict(input_scaled)
    return cluster[0]

# Define cluster descriptions
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

        # Fetch customer data and perform clustering
        customer_data = get_customer_data_by_id(customer_id)

        if customer_data is not None:
            # Load the full dataset to fit the KMeans model
            full_data = get_all_customer_data()
            segmented_data, kmeans, scaler = fit_kmeans(full_data)

            # Predict the cluster for the customer
            cluster = get_customer_cluster(kmeans, scaler, customer_data)

            # Get the cluster description
            result_description = cluster_descriptions[cluster]
            return render_template('segm.html', results=result_description)

        return render_template('segm.html', results="Customer ID not found.")

    return render_template('segm.html', results="")

if __name__ == '__main__':
    app.run(debug=True)
