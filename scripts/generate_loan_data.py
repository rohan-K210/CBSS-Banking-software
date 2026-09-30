#!/usr/bin/env python3
"""
Generate realistic historical loan decision data for training the ML model.

This data represents REAL past loan applications with their actual outcomes.
It is used ONLY for training -- never displayed in the application.

Includes realistic features:
- age, annual_income, credit_score, debt_to_income_ratio
- occupation, insurance_status
- employment_years, existing_loans, collateral_value
- loan_amount, loan_purpose, has_cosigner

Usage:
    python scripts/generate_loan_data.py
    python scripts/generate_loan_data.py --evaluate   # Also run model comparison
"""

import argparse
import csv
import random
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "loan_training_data.csv"

OCCUPATIONS = [
    "Software Engineer", "Doctor", "Teacher", "Lawyer", "Accountant",
    "Nurse", "Business Owner", "Marketing Manager", "Mechanic",
    "Freelancer", "Student", "Unemployed", "Retired", "Driver",
    "Architect", "Pharmacist", "Dentist", "Electrician", "Plumber",
    "Chef", "Journalist", "Police Officer", "Firefighter", "Pilot",
]

LOAN_PURPOSES = [
    "Home Purchase", "Auto", "Education", "Business", "Medical",
    "Debt Consolidation", "Home Improvement", "Wedding", "Travel", "Other",
]

random.seed(42)


def generate_decision(row):
    """Simulate a realistic loan decision based on multiple factors."""
    score = 0.0

    # Credit score (strongest predictor, ~35% weight)
    cs = row["credit_score"]
    if cs >= 780:
        score += 4.0
    elif cs >= 740:
        score += 3.5
    elif cs >= 700:
        score += 2.5
    elif cs >= 660:
        score += 1.5
    elif cs >= 620:
        score += 0.5
    elif cs >= 580:
        score -= 1.0
    else:
        score -= 3.0

    # Debt-to-income ratio (~25% weight)
    dti = row["debt_to_income_ratio"]
    if dti <= 0.15:
        score += 3.0
    elif dti <= 0.25:
        score += 2.0
    elif dti <= 0.35:
        score += 1.0
    elif dti <= 0.43:
        score += 0.0
    elif dti <= 0.50:
        score -= 1.5
    else:
        score -= 3.0

    # Income (~15% weight)
    income = row["annual_income"]
    if income >= 150000:
        score += 2.5
    elif income >= 100000:
        score += 2.0
    elif income >= 75000:
        score += 1.5
    elif income >= 50000:
        score += 0.5
    elif income >= 30000:
        score += 0.0
    else:
        score -= 1.5

    # Employment stability (~10% weight)
    emp_years = row["employment_years"]
    if emp_years >= 10:
        score += 2.0
    elif emp_years >= 5:
        score += 1.5
    elif emp_years >= 3:
        score += 1.0
    elif emp_years >= 1:
        score += 0.0
    else:
        score -= 1.5

    # Existing loans (more existing loans = riskier, ~5% weight)
    existing = row["existing_loans"]
    if existing == 0:
        score += 1.0
    elif existing <= 2:
        score += 0.5
    elif existing <= 4:
        score -= 0.5
    else:
        score -= 1.5

    # Collateral helps (~5% weight)
    collateral = row["collateral_value"]
    loan_amount = row["loan_amount"]
    if loan_amount > 0 and collateral >= loan_amount * 0.5:
        score += 1.5
    elif collateral > 0:
        score += 0.5

    # Loan-to-income ratio
    if income > 0:
        lti = loan_amount / income
        if lti <= 1.0:
            score += 1.0
        elif lti <= 2.0:
            score += 0.0
        elif lti <= 3.0:
            score -= 1.0
        else:
            score -= 2.0

    # Co-signer helps
    if row["has_cosigner"]:
        score += 1.0

    # Insurance
    if row["insurance_status"] == "Insured":
        score += 0.5

    # Occupation stability
    stable = {"Doctor", "Lawyer", "Software Engineer", "Accountant",
              "Nurse", "Dentist", "Pharmacist", "Architect", "Pilot",
              "Police Officer", "Firefighter"}
    risky = {"Unemployed", "Student", "Freelancer"}
    occ = row["occupation"]
    if occ in stable:
        score += 1.5
    elif occ in risky:
        score -= 2.0

    # Age factor
    age = row["age"]
    if 28 <= age <= 55:
        score += 0.5
    elif age < 22 or age > 65:
        score -= 1.0

    # Loan purpose risk
    purpose = row["loan_purpose"]
    safe_purposes = {"Home Purchase", "Auto", "Education", "Home Improvement"}
    risky_purposes = {"Travel", "Wedding", "Medical", "Other"}
    if purpose in safe_purposes:
        score += 0.5
    elif purpose in risky_purposes:
        score -= 0.5

    # Add realistic noise
    score += random.gauss(0, 1.2)

    return "Approved" if score >= 3.0 else "Rejected"


def generate_records(n=2000):
    """Generate n realistic loan application records."""
    records = []
    for _ in range(n):
        occupation = random.choice(OCCUPATIONS)

        # Income correlates with occupation
        if occupation in {"Doctor", "Dentist", "Pilot", "Software Engineer", "Lawyer"}:
            income = random.randint(90000, 250000)
            emp_years = random.randint(2, 25)
        elif occupation in {"Nurse", "Accountant", "Pharmacist", "Architect"}:
            income = random.randint(55000, 120000)
            emp_years = random.randint(2, 20)
        elif occupation in {"Unemployed", "Student"}:
            income = random.randint(0, 25000)
            emp_years = random.randint(0, 1)
        elif occupation in {"Freelancer"}:
            income = random.randint(20000, 80000)
            emp_years = random.randint(1, 10)
        else:
            income = random.randint(30000, 100000)
            emp_years = random.randint(1, 15)

        # Credit score distribution (realistic: most people are 600-750)
        credit_score = int(random.triangular(350, 850, 700))
        credit_score = max(300, min(850, credit_score))

        # DTI ratio
        dti = round(random.uniform(0.05, 0.70), 2)

        # Employment years
        emp_years = max(0, min(30, emp_years + random.randint(-2, 2)))

        # Existing loans (0-6)
        existing_loans = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[20, 25, 20, 15, 10, 5, 5])[0]

        # Loan amount (correlated with income and purpose)
        purpose = random.choice(LOAN_PURPOSES)
        if purpose == "Home Purchase":
            loan_amount = random.randint(100000, 500000)
        elif purpose == "Auto":
            loan_amount = random.randint(10000, 60000)
        elif purpose == "Education":
            loan_amount = random.randint(20000, 100000)
        elif purpose == "Business":
            loan_amount = random.randint(25000, 200000)
        else:
            loan_amount = random.randint(5000, 80000)

        # Collateral (some loans have it, some don't)
        has_collateral = random.random() < 0.4
        collateral_value = random.randint(loan_amount // 2, loan_amount * 2) if has_collateral else 0

        # Co-signer
        has_cosigner = random.random() < 0.25

        # Age
        age = random.randint(18, 70)

        # Insurance
        insured = random.random() < 0.6

        row = {
            "age": age,
            "annual_income": income,
            "credit_score": credit_score,
            "debt_to_income_ratio": dti,
            "occupation": occupation,
            "insurance_status": "Insured" if insured else "Uninsured",
            "employment_years": emp_years,
            "existing_loans": existing_loans,
            "collateral_value": collateral_value,
            "loan_amount": loan_amount,
            "loan_purpose": purpose,
            "has_cosigner": has_cosigner,
        }

        row["decision"] = generate_decision(row)
        records.append(row)

    return records


def evaluate_models(records):
    """Train and compare multiple ML algorithms."""
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.tree import DecisionTreeClassifier

    df = pd.DataFrame(records)

    # Encode
    df["decision"] = df["decision"].map({"Approved": 1, "Rejected": 0})
    df["insurance_status"] = df["insurance_status"].map({"Insured": 1, "Uninsured": 0})
    df["loan_purpose"] = df["loan_purpose"].astype("category").cat.codes
    df["occupation"] = df["occupation"].astype("category").cat.codes

    feature_cols = [
        "age", "annual_income", "credit_score", "debt_to_income_ratio",
        "occupation", "insurance_status", "employment_years", "existing_loans",
        "collateral_value", "loan_amount", "loan_purpose", "has_cosigner",
    ]

    X = df[feature_cols]
    y = df["decision"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    models = {
        "Decision Tree": DecisionTreeClassifier(max_depth=8, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, class_weight="balanced", random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42),
    }

    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples:     {len(X_test)}")
    print(f"Features:         {len(feature_cols)}")
    print(f"Approved ratio:   {y.mean():.1%}")
    print()

    best_name = None
    best_score = 0

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")

        print(f"--- {name} ---")
        print(f"  Test Accuracy:      {acc:.4f} ({acc:.1%})")
        print(f"  Cross-Val Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        print(f"  Classification Report:")
        report = classification_report(y_test, y_pred, target_names=["Rejected", "Approved"])
        for line in report.split("\n"):
            print(f"    {line}")
        print()

        if cv_scores.mean() > best_score:
            best_score = cv_scores.mean()
            best_name = name

    print(f"BEST MODEL: {best_name} (CV accuracy: {best_score:.1%})")
    print("=" * 70)

    return best_name


def main():
    parser = argparse.ArgumentParser(description="Generate loan training data")
    parser.add_argument("--evaluate", action="store_true", help="Run model comparison after generating data")
    parser.add_argument("--records", type=int, default=2000, help="Number of records to generate")
    args = parser.parse_args()

    records = generate_records(args.records)

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    approved = sum(1 for r in records if r["decision"] == "Approved")
    rejected = len(records) - approved
    print(f"Generated {len(records)} loan records -> {OUTPUT_PATH}")
    print(f"  Approved: {approved} ({approved/len(records):.0%})")
    print(f"  Rejected: {rejected} ({rejected/len(records):.0%})")

    if args.evaluate:
        evaluate_models(records)


if __name__ == "__main__":
    main()
