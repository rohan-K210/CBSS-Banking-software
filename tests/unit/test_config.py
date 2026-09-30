"""Tests for shared.config module."""

import os
import pytest


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    def test_mysql_connector_kwargs(self):
        from shared.config import DatabaseConfig
        cfg = DatabaseConfig(host="db.example.com", port=3307, user="admin", password="secret", database="mydb")
        kwargs = cfg.mysql_connector_kwargs
        assert kwargs["host"] == "db.example.com"
        assert kwargs["port"] == 3307
        assert kwargs["user"] == "admin"
        assert kwargs["password"] == "secret"
        assert kwargs["database"] == "mydb"

    def test_sqlalchemy_url(self):
        from shared.config import DatabaseConfig
        cfg = DatabaseConfig(user="root", password="pw", host="localhost", database="cbss")
        url = cfg.sqlalchemy_url
        assert url == "mysql+pymysql://root:pw@localhost:3306/cbss"

    def test_defaults(self):
        from shared.config import DatabaseConfig
        cfg = DatabaseConfig()
        assert cfg.host == "localhost"
        assert cfg.port == 3306
        assert cfg.pool_size == 5


class TestAppConfig:
    """Tests for AppConfig dataclass."""

    def test_defaults(self):
        from shared.config import AppConfig
        cfg = AppConfig(name="test")
        assert cfg.name == "test"
        assert cfg.port == 5000
        assert cfg.debug is False


class TestSettings:
    """Tests for load_settings with env vars."""

    def test_load_settings_defaults(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        monkeypatch.delenv("DB_NAME", raising=False)

        from shared.config import load_settings
        settings = load_settings()
        assert settings.secret_key == "test-key"
        assert settings.database.host == "localhost"
        assert settings.admin_app.port == 5000
        assert settings.client_app.port == 5001

    def test_custom_ports(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("ADMIN_PORT", "8000")
        monkeypatch.setenv("CLIENT_PORT", "8001")

        from shared.config import load_settings
        settings = load_settings()
        assert settings.admin_app.port == 8000
        assert settings.client_app.port == 8001
