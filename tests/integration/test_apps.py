"""Integration tests for all 5 CBSS Flask applications."""

import pytest
from shared.config import AppConfig
from shared.security import create_app


# ---------------------------------------------------------------------------
# Admin App
# ---------------------------------------------------------------------------
class TestAdminApp:
    """Tests for the Admin Dashboard app."""

    @pytest.fixture
    def client(self):
        from apps.admin import create_admin_app
        app = create_admin_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_root_route(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_admin_route(self, client):
        resp = client.get("/admin")
        assert resp.status_code == 200

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "admin"

    def test_cust_route(self, client):
        resp = client.get("/cust")
        assert resp.status_code == 200

    def test_emp_route(self, client):
        resp = client.get("/emp")
        assert resp.status_code == 200

    def test_loan_valuation_get(self, client):
        resp = client.get("/loan-valuation")
        assert resp.status_code == 200

    def test_segm_get(self, client):
        resp = client.get("/segm")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Client App
# ---------------------------------------------------------------------------
class TestClientApp:
    """Tests for the Client Transaction app."""

    @pytest.fixture
    def client(self):
        from apps.client import create_client_app
        app = create_client_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_login_page(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "client"

    def test_add_requires_session(self, client):
        resp = client.get("/add")
        # Should redirect to login (302)
        assert resp.status_code == 302

    def test_client_requires_session(self, client):
        resp = client.get("/client")
        assert resp.status_code == 302

    def test_show_requires_session(self, client):
        resp = client.get("/show")
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Hacker App
# ---------------------------------------------------------------------------
class TestHackerApp:
    """Tests for the Hacker Attack Simulator app."""

    @pytest.fixture
    def client(self):
        from apps.hacker import create_hacker_app
        app = create_hacker_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_home(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "hacker"


# ---------------------------------------------------------------------------
# Fraud Detector App
# ---------------------------------------------------------------------------
class TestFraudDetectorApp:
    """Tests for the Fraud Detector app."""

    @pytest.fixture
    def client(self):
        from apps.fraud_detector import create_fraud_detector_app
        app = create_fraud_detector_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_hacker_get(self, client):
        resp = client.get("/hacker")
        assert resp.status_code == 200

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "fraud_detector"


# ---------------------------------------------------------------------------
# Simple Transaction App
# ---------------------------------------------------------------------------
class TestSimpleTransactionApp:
    """Tests for the Simple Transaction app."""

    @pytest.fixture
    def client(self):
        from apps.simple_transaction import create_simple_transaction_app
        app = create_simple_transaction_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_login_page(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "simple_transaction"

    def test_add_requires_session(self, client):
        resp = client.get("/add")
        assert resp.status_code == 302

    def test_client_requires_session(self, client):
        resp = client.get("/client")
        assert resp.status_code == 302
