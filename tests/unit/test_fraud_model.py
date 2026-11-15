"""Regression tests for fraud prediction label handling."""

import pandas as pd
import pytest

from services import fraud_model


class StubModel:
    def __init__(self, prediction):
        self.prediction = prediction

    def predict(self, _features):
        return [self.prediction]


@pytest.mark.parametrize(
    ("prediction", "expected"),
    [
        (1, "blocked"),   # abnormal / fraud
        (0, "success"),   # normal / legitimate
    ],
)
def test_prediction_label_maps_to_transaction_result(monkeypatch, prediction, expected):
    feature_names = pd.Index(
        [
            "Sender ID",
            "Receiver ID",
            "Amount",
            "sender_ip",
            "receiver_ip",
            "sender_mac",
            "receiver_mac",
        ]
    )
    monkeypatch.setattr(
        fraud_model,
        "get_model",
        lambda: (StubModel(prediction), feature_names),
    )

    result = fraud_model.predict_fraud(
        sender_id=1,
        receiver_id=2,
        amount=100.0,
    )

    assert result == expected
