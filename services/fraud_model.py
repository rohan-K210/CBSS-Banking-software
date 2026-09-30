"""Fraud Detection ML Service.

Provides fraud detection using a Decision Tree Classifier with balanced class weights.
Model is trained lazily on first use from demo_transactions.csv (800 normal + 200 fraud).
"""

import ipaddress
import logging
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from shared.exceptions import FraudDetectionError

logger = logging.getLogger(__name__)

# Module-level cache
_model: DecisionTreeClassifier | None = None
_feature_names: pd.Index | None = None

# Path to the training data CSV
_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_transactions.csv"


def _train_model() -> tuple[DecisionTreeClassifier, pd.Index]:
    """Train fraud detection model from demo_transactions.csv."""
    if not _CSV_PATH.exists():
        raise FraudDetectionError(f"Training data not found: {_CSV_PATH}")

    df = pd.read_csv(_CSV_PATH)
    logger.info("Loaded %d transactions from %s", len(df), _CSV_PATH.name)

    # Map labels: normal=0, abnormal(fraud)=1
    df["label"] = df["Label"].map({"normal": 0, "abnormal": 1})
    df = df.dropna(subset=["label"])

    # Preprocess IP and MAC addresses to integers
    df["sender_ip"] = df["Sender IP"].apply(
        lambda x: int(ipaddress.IPv4Address(x)) if pd.notnull(x) else 0
    )
    df["receiver_ip"] = df["Receiver IP"].apply(
        lambda x: int(ipaddress.IPv4Address(x)) if pd.notnull(x) else 0
    )
    df["sender_mac"] = df["Sender MAC"].apply(
        lambda x: int(str(x).replace(":", ""), 16) if pd.notnull(x) else 0
    )
    df["receiver_mac"] = df["Receiver MAC"].apply(
        lambda x: int(str(x).replace(":", ""), 16) if pd.notnull(x) else 0
    )

    feature_cols = ["Sender ID", "Receiver ID", "Amount",
                    "sender_ip", "receiver_ip", "sender_mac", "receiver_mac"]
    X = df[feature_cols]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    model = DecisionTreeClassifier(class_weight="balanced", max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    fraud_count = int(y.sum())
    normal_count = int(len(y) - fraud_count)
    logger.info(
        "Fraud model trained: accuracy=%.1f%%, samples=%d (normal=%d, fraud=%d)",
        accuracy * 100, len(df), normal_count, fraud_count,
    )

    return model, X.columns


def get_model() -> tuple[DecisionTreeClassifier, pd.Index]:
    """Return trained model, training lazily if needed."""
    global _model, _feature_names
    if _model is None:
        try:
            _model, _feature_names = _train_model()
        except Exception as exc:
            logger.error("Failed to train fraud model: %s", exc)
            raise FraudDetectionError(f"Model training failed: {exc}") from exc
    return _model, _feature_names


def predict_fraud(
    sender_id: int,
    receiver_id: int | None,
    amount: float,
    ip_address: str = "0.0.0.0",
    mac_address: str = "00:00:00:00:00:00",
) -> str:
    """
    Predict whether a transaction is fraudulent.

    Returns "success" if legitimate, "blocked" if fraudulent.
    """
    try:
        model, feature_names = get_model()

        receiver_ip = ip_address if receiver_id is not None else None
        receiver_mac = mac_address if receiver_id is not None else None

        transaction_data = pd.DataFrame([{
            "Sender ID": sender_id,
            "Receiver ID": receiver_id,
            "Amount": amount,
            "sender_ip": int(ipaddress.IPv4Address(ip_address)),
            "receiver_ip": int(ipaddress.IPv4Address(receiver_ip)) if receiver_ip else 0,
            "sender_mac": int(mac_address.replace(":", ""), 16),
            "receiver_mac": int(receiver_mac.replace(":", ""), 16) if receiver_mac else 0,
        }])

        transaction_data = transaction_data[feature_names]
        prediction = model.predict(transaction_data)[0]
        result = "success" if prediction == 1 else "blocked"

        logger.info(
            "Fraud prediction: sender=%s receiver=%s amount=%.2f result=%s",
            sender_id, receiver_id, amount, result,
        )
        return result

    except FraudDetectionError:
        raise
    except Exception as exc:
        logger.error("Fraud prediction error: %s", exc)
        raise FraudDetectionError(f"Prediction failed: {exc}") from exc


def retrain_model() -> None:
    """Force retraining of the fraud model."""
    global _model, _feature_names
    _model, _feature_names = _train_model()
    logger.info("Fraud model retrained successfully")
