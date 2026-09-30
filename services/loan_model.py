"""
Loan Evaluation ML Service.

Provides loan approval prediction using Gradient Boosting Classifier.
Model is trained lazily on first use from data/loan_training_data.csv
(historical loan decisions -- NOT the sample customer data shown in the UI).

Features used:
- age, annual_income, credit_score, debt_to_income_ratio
- occupation, insurance_status
- employment_years, existing_loans, collateral_value
- loan_amount, loan_purpose, has_cosigner

Output is binary: "Approved" or "Rejected" only.
"""

import logging
from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score

from shared.database import get_sqlalchemy_engine
from shared.exceptions import LoanModelError

logger = logging.getLogger(__name__)

# Module-level model cache (per-process)
_model: GradientBoostingClassifier | None = None
_feature_columns: pd.Index | None = None
_model_accuracy: float | None = None

# External training data -- historical loan decisions, NOT sample customer data
_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "loan_training_data.csv"

# Feature columns used by the model
FEATURE_COLUMNS = [
    "age", "annual_income", "credit_score", "debt_to_income_ratio",
    "occupation", "insurance_status", "employment_years", "existing_loans",
    "collateral_value", "loan_amount", "loan_purpose", "has_cosigner",
]

# Occupation encoding (must match training data encoding)
OCCUPATION_LIST = [
    "Accountant", "Architect", "Business Owner", "Chef", "Dentist",
    "Doctor", "Driver", "Electrician", "Engineer", "Freelancer",
    "Journalist", "Lawyer", "Marketing Manager", "Mechanic", "Nurse",
    "Pilot", "Pharmacist", "Plumber", "Police Officer", "Retired",
    "Software Engineer", "Student", "Teacher", "Unemployed",
]

LOAN_PURPOSE_LIST = [
    "Auto", "Business", "Debt Consolidation", "Education", "Home Improvement",
    "Home Purchase", "Medical", "Other", "Travel", "Wedding",
]


def _train_model() -> tuple[GradientBoostingClassifier, pd.Index]:
    """Train the loan approval model from historical loan data."""
    if not _CSV_PATH.exists():
        raise LoanModelError(f"Training data not found: {_CSV_PATH}")

    df = pd.read_csv(_CSV_PATH)
    logger.info("Loaded %d historical loan records from %s", len(df), _CSV_PATH.name)

    # Encode target: Approved=1, Rejected=0
    df["decision"] = df["decision"].map({"Approved": 1, "Rejected": 0})
    df = df.dropna(subset=["decision"])

    # Encode categorical features
    df["insurance_status"] = df["insurance_status"].map({"Insured": 1, "Uninsured": 0})
    df["has_cosigner"] = df["has_cosigner"].astype(int)

    # Occupation encoding
    occ_map = {name: i for i, name in enumerate(sorted(set(df["occupation"].unique())))}
    df["occupation_encoded"] = df["occupation"].map(occ_map)

    # Loan purpose encoding
    purpose_map = {name: i for i, name in enumerate(sorted(set(df["loan_purpose"].unique())))}
    df["loan_purpose_encoded"] = df["loan_purpose"].map(purpose_map)

    feature_cols = [
        "age", "annual_income", "credit_score", "debt_to_income_ratio",
        "occupation_encoded", "insurance_status", "employment_years",
        "existing_loans", "collateral_value", "loan_amount",
        "loan_purpose_encoded", "has_cosigner",
    ]

    X = df[feature_cols]
    y = df["decision"]

    # Train Gradient Boosting
    model = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        min_samples_split=10,
        random_state=42,
    )
    model.fit(X, y)

    # Cross-validation score
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    accuracy = cv_scores.mean()

    approved_count = int(y.sum())
    rejected_count = int(len(y) - approved_count)
    logger.info(
        "Loan model trained: CV accuracy=%.1f%% (+/- %.1f%%), samples=%d (approved=%d, rejected=%d)",
        accuracy * 100, cv_scores.std() * 100, len(df), approved_count, rejected_count,
    )

    # Store encoding maps for prediction
    model._occ_map = occ_map
    model._purpose_map = purpose_map

    return model, pd.Index(feature_cols), accuracy


def get_model() -> tuple[GradientBoostingClassifier, pd.Index]:
    """Return trained model, training lazily if needed."""
    global _model, _feature_columns, _model_accuracy
    if _model is None:
        try:
            _model, _feature_columns, _model_accuracy = _train_model()
        except Exception as exc:
            logger.error("Failed to train loan model: %s", exc)
            raise LoanModelError(f"Model training failed: {exc}") from exc
    return _model, _feature_columns


def get_feature_importance() -> list[dict]:
    """Return feature importances from the trained model."""
    model, feature_columns = get_model()
    importances = model.feature_importances_
    display_names = {
        "age": "Age",
        "annual_income": "Annual Income",
        "credit_score": "Credit Score",
        "debt_to_income_ratio": "Debt-to-Income Ratio",
        "occupation_encoded": "Occupation",
        "insurance_status": "Insurance Status",
        "employment_years": "Employment Years",
        "existing_loans": "Existing Loans",
        "collateral_value": "Collateral Value",
        "loan_amount": "Loan Amount",
        "loan_purpose_encoded": "Loan Purpose",
        "has_cosigner": "Has Co-signer",
    }
    pairs = sorted(
        zip(feature_columns, importances),
        key=lambda x: x[1],
        reverse=True,
    )
    results = []
    for name, imp in pairs:
        display_name = display_names.get(name, name)
        results.append({"feature": display_name, "importance": round(float(imp), 4)})
    return results


def get_model_info() -> dict:
    """Return model metadata including accuracy."""
    get_model()  # ensure trained
    return {
        "algorithm": "Gradient Boosting",
        "accuracy": round(_model_accuracy * 100, 1) if _model_accuracy else None,
        "features": len(FEATURE_COLUMNS),
        "training_data": str(_CSV_PATH.name),
    }


def _encode_occupation(occupation: str, occ_map: dict) -> int:
    """Encode occupation to integer, defaulting to 0 for unknown."""
    return occ_map.get(occupation, 0)


def _encode_purpose(purpose: str, purpose_map: dict) -> int:
    """Encode loan purpose to integer, defaulting to 0 for unknown."""
    return purpose_map.get(purpose, 0)


def predict_loan_approval(customer_id: int | str) -> dict:
    """
    Predict loan approval for a given customer ID.

    Returns a dict with:
        - result: "Approved" or "Rejected"
        - customer_id: the customer ID
        - confidence: prediction confidence (0-100)
        - factors: list of factors influencing the decision
    """
    try:
        model, feature_columns = get_model()
        engine = get_sqlalchemy_engine()

        query = """
            SELECT age, annual_income, credit_score, debt_to_income_ratio,
                   occupation, insurance_status, employment_years,
                   existing_loans, collateral_value, loan_amount,
                   loan_purpose, has_cosigner
            FROM customers WHERE id = %s;
        """
        with engine.connect() as conn:
            customer_data = pd.read_sql(query, conn, params=(customer_id,))

        if customer_data.empty:
            raise LoanModelError(f"Customer {customer_id} not found")

        row = customer_data.iloc[0]

        # Encode categorical features
        occ_map = model._occ_map
        purpose_map = model._purpose_map

        occupation_encoded = _encode_occupation(row["occupation"], occ_map)
        purpose_encoded = _encode_purpose(row.get("loan_purpose", "Other"), purpose_map)

        # Handle None/NaN values
        employment_years = int(row["employment_years"]) if pd.notna(row["employment_years"]) else 0
        existing_loans = int(row["existing_loans"]) if pd.notna(row["existing_loans"]) else 0
        collateral_value = float(row["collateral_value"]) if pd.notna(row["collateral_value"]) else 0.0
        loan_amount = float(row["loan_amount"]) if pd.notna(row["loan_amount"]) else 0.0
        has_cosigner = int(row["has_cosigner"]) if pd.notna(row["has_cosigner"]) else 0

        customer_df = pd.DataFrame([{
            "age": int(row["age"]),
            "annual_income": float(row["annual_income"]),
            "credit_score": int(row["credit_score"]),
            "debt_to_income_ratio": float(row["debt_to_income_ratio"]),
            "occupation_encoded": occupation_encoded,
            "insurance_status": 1 if row["insurance_status"] == "Insured" else 0,
            "employment_years": employment_years,
            "existing_loans": existing_loans,
            "collateral_value": collateral_value,
            "loan_amount": loan_amount,
            "loan_purpose_encoded": purpose_encoded,
            "has_cosigner": has_cosigner,
        }])

        features = customer_df[feature_columns]
        prediction = model.predict(features)[0]

        # Get probability for confidence
        proba = model.predict_proba(features)[0]
        confidence = float(max(proba)) * 100

        result = "Approved" if prediction == 1 else "Rejected"

        # Build human-readable factors
        factors = _explain_decision(row, result)

        logger.info("Loan prediction: customer_id=%s result=%s confidence=%.1f%%", customer_id, result, confidence)
        return {
            "result": result,
            "customer_id": customer_id,
            "confidence": round(confidence, 1),
            "factors": factors,
        }

    except LoanModelError:
        raise
    except Exception as exc:
        logger.error("Loan prediction error for customer %s: %s", customer_id, exc)
        raise LoanModelError(f"Prediction failed: {exc}") from exc


def _explain_decision(row, result: str) -> list[str]:
    """Generate human-readable factors explaining the decision."""
    factors = []

    # Credit score
    credit = row.get("credit_score", 0)
    if credit >= 780:
        factors.append(f"Excellent credit score ({credit})")
    elif credit >= 740:
        factors.append(f"Very good credit score ({credit})")
    elif credit >= 700:
        factors.append(f"Good credit score ({credit})")
    elif credit >= 660:
        factors.append(f"Fair credit score ({credit})")
    elif credit >= 620:
        factors.append(f"Below-average credit score ({credit})")
    else:
        factors.append(f"Poor credit score ({credit})")

    # DTI ratio
    dti = row.get("debt_to_income_ratio", 0)
    if dti <= 0.15:
        factors.append(f"Excellent debt-to-income ratio ({dti:.0%})")
    elif dti <= 0.25:
        factors.append(f"Good debt-to-income ratio ({dti:.0%})")
    elif dti <= 0.35:
        factors.append(f"Moderate debt-to-income ratio ({dti:.0%})")
    elif dti <= 0.43:
        factors.append(f"Acceptable debt-to-income ratio ({dti:.0%})")
    else:
        factors.append(f"High debt-to-income ratio ({dti:.0%})")

    # Income
    income = row.get("annual_income", 0)
    if income >= 100000:
        factors.append(f"High annual income (${income:,.0f})")
    elif income >= 50000:
        factors.append(f"Moderate annual income (${income:,.0f})")
    else:
        factors.append(f"Low annual income (${income:,.0f})")

    # Employment
    emp = row.get("employment_years", 0)
    if emp >= 10:
        factors.append(f"Strong employment history ({emp} years)")
    elif emp >= 5:
        factors.append(f"Good employment history ({emp} years)")
    elif emp >= 2:
        factors.append(f"Moderate employment history ({emp} years)")
    else:
        factors.append(f"Limited employment history ({emp} years)")

    # Existing loans
    existing = row.get("existing_loans", 0)
    if existing == 0:
        factors.append("No existing loans")
    elif existing <= 2:
        factors.append(f"{existing} existing loans (manageable)")
    else:
        factors.append(f"{existing} existing loans (high burden)")

    # Collateral
    collateral = row.get("collateral_value", 0)
    loan_amount = row.get("loan_amount", 0)
    if collateral > 0 and loan_amount > 0:
        ratio = collateral / loan_amount
        if ratio >= 1.0:
            factors.append("Fully collateralized")
        elif ratio >= 0.5:
            factors.append(f"Partially collateralized ({ratio:.0%} of loan)")
        else:
            factors.append("Insufficient collateral")
    elif loan_amount > 0:
        factors.append("No collateral offered")

    # Co-signer
    if row.get("has_cosigner"):
        factors.append("Has co-signer (reduces risk)")

    # Insurance
    if row.get("insurance_status") == "Insured":
        factors.append("Has insurance coverage")

    return factors


def retrain_model() -> None:
    """Force retraining of the loan model."""
    global _model, _feature_columns, _model_accuracy
    _model, _feature_columns, _model_accuracy = _train_model()
    logger.info("Loan model retrained successfully")
