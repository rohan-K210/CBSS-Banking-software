"""
Customer Segmentation ML Service.

Provides customer cluster prediction using KMeans clustering.
Model is trained lazily on first use and cached for subsequent calls.
"""

import logging
from typing import Any

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from shared.database import get_connection, get_sqlalchemy_engine
from shared.exceptions import SegmentationError

logger = logging.getLogger(__name__)

# Module-level cache (per-process)
_kmeans: KMeans | None = None
_scaler: StandardScaler | None = None

CLUSTER_DESCRIPTIONS: dict[int, str] = {
    0: "Young, low income, high debt-to-income ratio (potentially risky customers).",
    1: "Middle-aged, high income, good credit score (financially stable customers).",
    2: "Older customers with moderate income and low debt (retirement-focused customers).",
    3: "Young professionals with good incomes but still building credit (emerging customers).",
}

FEATURE_COLUMNS = ["age", "annual_income", "credit_score", "debt_to_income_ratio", "bank_balance"]


def _fit_model() -> tuple[KMeans, StandardScaler]:
    """Fit KMeans on the full customer dataset."""
    engine = get_sqlalchemy_engine()
    query = f"SELECT {', '.join(FEATURE_COLUMNS)} FROM customers;"
    with engine.connect() as conn:
        full_data = pd.read_sql(query, conn)

    if full_data.empty:
        raise SegmentationError("No customer data available for segmentation")

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(full_data[FEATURE_COLUMNS])

    kmeans = KMeans(n_clusters=4, random_state=42)
    kmeans.fit(features_scaled)

    logger.info("Segmentation model trained: %d samples, %d clusters", len(full_data), 4)
    return kmeans, scaler


def get_models() -> tuple[KMeans, StandardScaler]:
    """Return trained models, training lazily if needed."""
    global _kmeans, _scaler
    if _kmeans is None:
        try:
            _kmeans, _scaler = _fit_model()
        except Exception as exc:
            logger.error("Failed to train segmentation model: %s", exc)
            raise SegmentationError(f"Model training failed: {exc}") from exc
    return _kmeans, _scaler


def get_customer_data_by_id(customer_id: int | str) -> pd.DataFrame | None:
    """Fetch a single customer's features for clustering."""
    with get_connection(dictionary=True) as cursor:
        cursor.execute(
            f"SELECT {', '.join(FEATURE_COLUMNS)} FROM customers WHERE id = %s;",
            (customer_id,),
        )
        customer_data = cursor.fetchone()

    return pd.DataFrame([customer_data]) if customer_data else None


def predict_cluster(customer_id: int | str) -> tuple[int, str]:
    """
    Predict the cluster for a customer.

    Returns:
        Tuple of (cluster_id, description).
    """
    try:
        customer_data = get_customer_data_by_id(customer_id)
        if customer_data is None:
            raise SegmentationError(f"Customer {customer_id} not found")

        kmeans, scaler = get_models()
        features = customer_data[FEATURE_COLUMNS]
        input_scaled = scaler.transform(features)
        cluster = kmeans.predict(input_scaled)[0]
        description = CLUSTER_DESCRIPTIONS.get(cluster, "Unknown cluster")

        logger.info("Segmentation: customer_id=%s cluster=%d", customer_id, cluster)
        return cluster, description

    except SegmentationError:
        raise
    except Exception as exc:
        logger.error("Segmentation error for customer %s: %s", customer_id, exc)
        raise SegmentationError(f"Segmentation failed: {exc}") from exc


def retrain_model() -> None:
    """Force retraining of the segmentation model."""
    global _kmeans, _scaler
    _kmeans, _scaler = _fit_model()
    logger.info("Segmentation model retrained successfully")
