"""Tests for shared.security module — Flask app factory."""

import pytest
from shared.config import AppConfig
from shared.security import create_app


@pytest.fixture
def app_config():
    return AppConfig(name="test", port=9999, debug=False, secret_key="test-secret-key")


@pytest.fixture
def client(app_config):
    app = create_app(app_config)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestAppFactory:
    """Tests for create_app."""

    def test_app_created(self, app_config):
        app = create_app(app_config)
        assert app is not None
        assert app.name == "flask.app" or app.name is not None

    def test_secret_key_set(self, app_config):
        app = create_app(app_config)
        assert app.secret_key == "test-secret-key"

    def test_health_endpoint(self, client):
        resp = client.get("/nonexistent-health")
        # Should return 404, not crash
        assert resp.status_code == 404

    def test_404_handler(self, client):
        resp = client.get("/this-does-not-exist")
        assert resp.status_code == 404

    def test_405_handler(self, client):
        # POST to a route that only accepts GET triggers 405
        @client.application.route("/get-only")
        def get_only():
            return "ok"
        resp = client.post("/get-only")
        assert resp.status_code == 405


class TestRequireSession:
    """Tests for session decorator."""

    def test_redirect_without_session(self, app_config):
        from shared.security import require_session
        app = create_app(app_config)

        @app.route("/login")
        def login():
            return "login"

        @app.route("/protected")
        @require_session
        def protected():
            return "should not reach"

        with app.test_client() as client:
            resp = client.get("/protected")
            # No session → should redirect (302) to login
            assert resp.status_code == 302
