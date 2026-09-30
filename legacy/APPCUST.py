from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'IAMVENU123',
    'database': 'cbss'
}

# Route to display the customer management page
@app.route('/cust')
def index():
    return render_template('customer.html', results=None)

# Route to handle adding a customer
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

        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Insert the customer data into the database
        query = """INSERT INTO customers (full_name, gender, age, address, contact_number, annual_income, 
                   credit_score, debt_to_income_ratio, occupation, loan_status, insurance_status, ip_address, 
                   mac_address, bank_balance, password) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (full_name, gender, age, address, contact_number, annual_income, credit_score, 
                               debt_to_income_ratio, occupation, loan_status, insurance_status, ip_address, 
                               mac_address, bank_balance, password))
        connection.commit()

        # Return success message
        results = {'message': 'Customer added successfully!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)

# Route to handle editing a customer
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

        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Update the customer data in the database
        query = """UPDATE customers SET full_name = %s, gender = %s, age = %s, address = %s, contact_number = %s,
                   annual_income = %s, credit_score = %s, debt_to_income_ratio = %s, occupation = %s, loan_status = %s,
                   insurance_status = %s, ip_address = %s, mac_address = %s, bank_balance = %s, password = %s
                   WHERE id = %s"""
        cursor.execute(query, (full_name, gender, age, address, contact_number, annual_income, credit_score, 
                               debt_to_income_ratio, occupation, loan_status, insurance_status, ip_address, 
                               mac_address, bank_balance, password, customer_id))
        connection.commit()

        # Return success message
        results = {'message': 'Customer updated successfully!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)

# Route to handle deleting a customer
@app.route('/delete_customer', methods=['POST'])
def delete_customer():
    try:
        customer_id = request.form.get('deleteCustomerID')

        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Delete the customer from the database
        query = "DELETE FROM customers WHERE id = %s"
        cursor.execute(query, (customer_id,))
        connection.commit()

        # Return success message
        results = {'message': 'Customer deleted successfully!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)

# Route to handle searching for a customer
@app.route('/search_customer', methods=['POST'])
def search_customer():
    customer_id = request.form.get('searchCustomerID')

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try:
        query = "SELECT * FROM customers WHERE id = %s"
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        if result:
            results = {
                'id': result[0],
                'full_name': result[1],
                'gender': result[2],
                'age': result[3],
                'address': result[4],
                'contact_number': result[5],
                'annual_income': result[6],
                'credit_score': result[7],
                'debt_to_income_ratio': result[8],
                'occupation': result[9],
                'loan_status': result[10],
                'insurance_status': result[11],
                'ip_address': result[12],
                'mac_address': result[13],
                'bank_balance': result[14],
                'password': result[15]
            }
        else:
            results = {'message': 'Customer not found!'}
    except Exception as e:
        results = {'error': str(e)}
    finally:
        cursor.close()
        connection.close()

    return render_template('customer.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
