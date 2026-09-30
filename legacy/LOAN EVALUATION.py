from flask import Flask, render_template, request
from sqlalchemy import create_engine
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

app = Flask(__name__)

# Database connection setup using SQLAlchemy
def create_db_connection():
    engine = create_engine('mysql+pymysql://root:IAMVENU123@localhost/cbss')
    return engine

# Load data into a DataFrame
def load_data():
    engine = create_db_connection()
    query = """
    SELECT id, full_name, age, annual_income, credit_score, debt_to_income_ratio,
           occupation, loan_status, insurance_status FROM customers;
    """
    df = pd.read_sql(query, engine)
    return df

# Load the data and train the model
df = load_data()

# Map loan status and insurance status
df['loan_status'] = df['loan_status'].map({'Approved': 1, 'Pending': 0, 'Rejected': -1})
df['insurance_status'] = df['insurance_status'].map({'Insured': 1, 'Uninsured': 0})

# Select only necessary columns for training
df = df[['age', 'annual_income', 'credit_score', 'debt_to_income_ratio', 'occupation', 'insurance_status', 'loan_status']]

# One-hot encode occupation and drop the first column
df = pd.get_dummies(df, columns=['occupation'], drop_first=True)

# Define features and target
X = df.drop(['loan_status'], axis=1)
y = df['loan_status']

# Train the Decision Tree Classifier
model = DecisionTreeClassifier(random_state=42)
model.fit(X, y)

# Function to predict loan approval based on customer ID
def predict_loan_approval(customer_id):
    try:
        engine = create_db_connection()

        # Fetch the customer data from the database
        query = f"""
        SELECT age, annual_income, credit_score, debt_to_income_ratio, occupation, insurance_status 
        FROM customers WHERE id = {customer_id};
        """
        customer_data = pd.read_sql(query, engine)

        if customer_data.empty:
            return "Customer ID not found."

        # Convert necessary columns
        customer_data['insurance_status'] = 1 if customer_data['insurance_status'].values[0] == 'Insured' else 0

        # Create a DataFrame for the customer
        customer_df = pd.DataFrame([{
            'age': customer_data['age'].values[0],
            'annual_income': customer_data['annual_income'].values[0],
            'credit_score': customer_data['credit_score'].values[0],
            'debt_to_income_ratio': customer_data['debt_to_income_ratio'].values[0],
            'insurance_status': customer_data['insurance_status']
        }])

        # One-hot encode occupation
        if 'occupation' in customer_data.columns:
            customer_df['occupation'] = customer_data['occupation'].values[0]
            customer_df = pd.get_dummies(customer_df, columns=['occupation'], drop_first=True)

        # Ensure all feature columns are present
        for col in X.columns:
            if col not in customer_df.columns:
                customer_df[col] = 0  # Fill with zeros if the column is missing

        # Select only the feature columns
        features = customer_df[X.columns]

        # Make the prediction
        prediction = model.predict(features)

        # Map prediction back to loan status
        status_map = {1: "Approved", 0: "Pending", -1: "Rejected"}
        return status_map.get(prediction[0], "Unknown Status")
    except Exception as e:
        return f"Error in prediction: {e}"

# Route to render the form and display results
@app.route('/loan-valuation', methods=['GET', 'POST'])
def loan_valuation():
    result = None
    if request.method == 'POST':
        customer_id = request.form['customerId']
        result = predict_loan_approval(customer_id)
        print(f"Customer ID: {customer_id}, Result: {result}")  # Debugging line
    return render_template('loan.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
