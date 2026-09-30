"""
Seed the cbss database with sample customer and employee data.

Usage:
    python scripts/seed_data.py

This inserts sample records so the app can be tested immediately.
Run only once — duplicates will cause errors on re-run.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import get_cursor
from shared.config import get_settings


SAMPLE_CUSTOMERS = [
    {
        "full_name": "John Doe",
        "gender": "Male",
        "age": 35,
        "address": "123 Main Street, New York, NY 10001",
        "contact_number": "555-0101",
        "annual_income": 75000.00,
        "credit_score": 720,
        "debt_to_income_ratio": 0.28,
        "occupation": "Software Engineer",
        "loan_status": "Approved",
        "insurance_status": "Insured",
        "ip_address": "192.168.1.10",
        "mac_address": "AA:BB:CC:DD:EE:01",
        "bank_balance": 15000.00,
        "password": "password123",
        "employment_years": 8,
        "existing_loans": 1,
        "collateral_value": 200000.00,
        "loan_amount": 150000.00,
        "loan_purpose": "Home Purchase",
        "has_cosigner": False,
    },
    {
        "full_name": "Jane Smith",
        "gender": "Female",
        "age": 28,
        "address": "456 Oak Avenue, Los Angeles, CA 90001",
        "contact_number": "555-0102",
        "annual_income": 62000.00,
        "credit_score": 680,
        "debt_to_income_ratio": 0.35,
        "occupation": "Marketing Manager",
        "loan_status": "Rejected",
        "insurance_status": "Insured",
        "ip_address": "192.168.1.11",
        "mac_address": "AA:BB:CC:DD:EE:02",
        "bank_balance": 8500.00,
        "password": "password123",
        "employment_years": 3,
        "existing_loans": 2,
        "collateral_value": 0.00,
        "loan_amount": 35000.00,
        "loan_purpose": "Auto",
        "has_cosigner": False,
    },
    {
        "full_name": "Robert Johnson",
        "gender": "Male",
        "age": 45,
        "address": "789 Pine Road, Chicago, IL 60601",
        "contact_number": "555-0103",
        "annual_income": 95000.00,
        "credit_score": 750,
        "debt_to_income_ratio": 0.20,
        "occupation": "Doctor",
        "loan_status": "Approved",
        "insurance_status": "Insured",
        "ip_address": "192.168.1.12",
        "mac_address": "AA:BB:CC:DD:EE:03",
        "bank_balance": 42000.00,
        "password": "password123",
        "employment_years": 15,
        "existing_loans": 0,
        "collateral_value": 500000.00,
        "loan_amount": 200000.00,
        "loan_purpose": "Home Purchase",
        "has_cosigner": False,
    },
    {
        "full_name": "Emily Davis",
        "gender": "Female",
        "age": 31,
        "address": "321 Elm Street, Houston, TX 77001",
        "contact_number": "555-0104",
        "annual_income": 55000.00,
        "credit_score": 620,
        "debt_to_income_ratio": 0.42,
        "occupation": "Teacher",
        "loan_status": "Rejected",
        "insurance_status": "Uninsured",
        "ip_address": "192.168.1.13",
        "mac_address": "AA:BB:CC:DD:EE:04",
        "bank_balance": 2300.00,
        "password": "password123",
        "employment_years": 4,
        "existing_loans": 3,
        "collateral_value": 0.00,
        "loan_amount": 25000.00,
        "loan_purpose": "Education",
        "has_cosigner": False,
    },
    {
        "full_name": "Michael Wilson",
        "gender": "Male",
        "age": 52,
        "address": "654 Maple Drive, Phoenix, AZ 85001",
        "contact_number": "555-0105",
        "annual_income": 120000.00,
        "credit_score": 790,
        "debt_to_income_ratio": 0.15,
        "occupation": "Business Owner",
        "loan_status": "Approved",
        "insurance_status": "Insured",
        "ip_address": "192.168.1.14",
        "mac_address": "AA:BB:CC:DD:EE:05",
        "bank_balance": 78000.00,
        "password": "password123",
        "employment_years": 20,
        "existing_loans": 1,
        "collateral_value": 800000.00,
        "loan_amount": 300000.00,
        "loan_purpose": "Business",
        "has_cosigner": True,
    },
]

SAMPLE_EMPLOYEES = [
    {
        "first_name": "Alice",
        "last_name": "Brown",
        "gender": "Female",
        "date_of_birth": "1988-03-15",
        "position": "Branch Manager",
        "department": "Management",
        "hire_date": "2018-06-01",
        "salary": 85000.00,
        "email": "alice.brown@cbss.com",
        "phone_number": "555-1001",
        "address": "100 Bank Lane, New York, NY",
        "emergency_contact": "Tom Brown",
        "emergency_contact_phone": "555-1002",
        "performance_rating": 4.50,
        "is_active": True,
    },
    {
        "first_name": "David",
        "last_name": "Martinez",
        "gender": "Male",
        "date_of_birth": "1992-07-22",
        "position": "Loan Officer",
        "department": "Lending",
        "hire_date": "2020-01-15",
        "salary": 62000.00,
        "email": "david.martinez@cbss.com",
        "phone_number": "555-1003",
        "address": "200 Finance Blvd, Los Angeles, CA",
        "emergency_contact": "Rosa Martinez",
        "emergency_contact_phone": "555-1004",
        "performance_rating": 4.20,
        "is_active": True,
    },
    {
        "first_name": "Sarah",
        "last_name": "Lee",
        "gender": "Female",
        "date_of_birth": "1995-11-08",
        "position": "Customer Service Rep",
        "department": "Support",
        "hire_date": "2022-03-20",
        "salary": 45000.00,
        "email": "sarah.lee@cbss.com",
        "phone_number": "555-1005",
        "address": "300 Service Road, Chicago, IL",
        "emergency_contact": "James Lee",
        "emergency_contact_phone": "555-1006",
        "performance_rating": 4.00,
        "is_active": True,
    },
]


def seed_customers():
    """Insert sample customers."""
    inserted = 0
    for cust in SAMPLE_CUSTOMERS:
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO customers
                       (full_name, gender, age, address, contact_number,
                        annual_income, credit_score, debt_to_income_ratio,
                        occupation, loan_status, insurance_status,
                        ip_address, mac_address, bank_balance, password,
                        employment_years, existing_loans, collateral_value,
                        loan_amount, loan_purpose, has_cosigner)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        cust["full_name"], cust["gender"], cust["age"],
                        cust["address"], cust["contact_number"],
                        cust["annual_income"], cust["credit_score"],
                        cust["debt_to_income_ratio"], cust["occupation"],
                        cust["loan_status"], cust["insurance_status"],
                        cust["ip_address"], cust["mac_address"],
                        cust["bank_balance"], cust["password"],
                        cust["employment_years"], cust["existing_loans"],
                        cust["collateral_value"], cust["loan_amount"],
                        cust["loan_purpose"], cust["has_cosigner"],
                    ),
                )
                inserted += 1
        except Exception as e:
            print(f"  [SKIP] {cust['full_name']}: {e}")
    return inserted


def seed_employees():
    """Insert sample employees."""
    inserted = 0
    for emp in SAMPLE_EMPLOYEES:
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO employees
                       (first_name, last_name, gender, date_of_birth,
                        position, department, hire_date, salary, email,
                        phone_number, address, emergency_contact,
                        emergency_contact_phone, performance_rating, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        emp["first_name"], emp["last_name"], emp["gender"],
                        emp["date_of_birth"], emp["position"], emp["department"],
                        emp["hire_date"], emp["salary"], emp["email"],
                        emp["phone_number"], emp["address"],
                        emp["emergency_contact"], emp["emergency_contact_phone"],
                        emp["performance_rating"], emp["is_active"],
                    ),
                )
                inserted += 1
        except Exception as e:
            print(f"  [SKIP] {emp['first_name']} {emp['last_name']}: {e}")
    return inserted


def main():
    settings = get_settings()
    print(f"Seeding database: {settings.database.database}@{settings.database.host}:{settings.database.port}")
    print()

    print("Inserting customers...")
    n_cust = seed_customers()
    print(f"  Inserted {n_cust} customers")

    print("Inserting employees...")
    n_emp = seed_employees()
    print(f"  Inserted {n_emp} employees")

    print()
    print("Done! You can now log in with:")
    print("  Client login (port 5001):  Customer ID 1-5 / password: password123")
    print("  Admin dashboard (port 5000): No login required")


if __name__ == "__main__":
    main()
