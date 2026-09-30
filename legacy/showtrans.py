from flask import Flask, render_template
from mysql.connector import connect

app = Flask(__name__)

# Route to display transaction history for a specific client (Client ID = 2)
@app.route('/show')
def transactions():
    client_id = 2  # Client ID to filter by
    
    # SQL query to get transactions where the client is either sender or receiver
    query = """
   SELECT * FROM TRANSACTIONS
    """

    # Database connection and query execution
    connection = connect(
        host="localhost",
        user="root",
        password="IAMVENU123",
        database="cbss"
    )
    cursor = connection.cursor()
    cursor.execute(query)
    transactions = cursor.fetchall()
    connection.close()

    # Pass the transactions data to the template
    return render_template('Showtransadmin.html', transactions=transactions)

# Route for the client dashboard (you can adjust this as needed)
@app.route('/admin')
def client_dashboard():
    return render_template('login1.html')

if __name__ == "__main__":
    app.run(debug=True)
