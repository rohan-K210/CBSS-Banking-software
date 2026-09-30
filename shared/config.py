"""
Centralized configuration management for the CBSS backend.

Loads settings from environment variables (.env file) with sensible defaults.
All configuration is validated at startup — missing required vars cause a clear error.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    # Look for .env in project root (parent of shared/)
    _project_root = Path(__file__).resolve().parent.parent
    load_dotenv(_project_root / ".env")
except ImportError:
    pass


def _require_env(key: str, default: str | None = None) -> str:
    """Return env var value, or default, or raise with a clear message."""
    value = os.environ.get(key, default)
    if value is None:
        print(
            f"[CONFIG ERROR] Required environment variable '{key}' is not set. "
            f"Add it to .env or set it in your shell.",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


@dataclass(frozen=True)
class DatabaseConfig:
    """MySQL database connection settings."""

    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "cbss"
    pool_size: int = 5

    @property
    def mysql_connector_kwargs(self) -> dict:
        """Return kwargs suitable for mysql.connector.connect()."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
        }

    @property
    def sqlalchemy_url(self) -> str:
        """Return SQLAlchemy connection URL."""
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class AppConfig:
    """Configuration for a single Flask application."""

    name: str
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False
    secret_key: str = "change-me-in-production"


@dataclass(frozen=True)
class Settings:
    """Top-level settings container."""

    database: DatabaseConfig
    secret_key: str
    debug: bool
    log_level: str

    # Individual app configs
    admin_app: AppConfig
    client_app: AppConfig
    hacker_app: AppConfig
    fraud_detector_app: AppConfig
    simple_transaction_app: AppConfig


def load_settings() -> Settings:
    """Load and validate all settings from environment variables."""
    db = DatabaseConfig(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "cbss"),
        pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
    )

    secret_key = _require_env("SECRET_KEY", "dev-secret-key-change-in-production")
    debug = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    admin_app = AppConfig(
        name="admin",
        host=os.environ.get("ADMIN_HOST", "127.0.0.1"),
        port=int(os.environ.get("ADMIN_PORT", "5000")),
        debug=debug,
        secret_key=secret_key,
    )

    client_app = AppConfig(
        name="client",
        host=os.environ.get("CLIENT_HOST", "127.0.0.1"),
        port=int(os.environ.get("CLIENT_PORT", "5001")),
        debug=debug,
        secret_key=secret_key,
    )

    hacker_app = AppConfig(
        name="hacker",
        host=os.environ.get("HACKER_HOST", "127.0.0.1"),
        port=int(os.environ.get("HACKER_PORT", "5002")),
        debug=debug,
        secret_key=secret_key,
    )

    fraud_detector_app = AppConfig(
        name="fraud_detector",
        host=os.environ.get("FRAUD_DETECTOR_HOST", "127.0.0.1"),
        port=int(os.environ.get("FRAUD_DETECTOR_PORT", "5003")),
        debug=debug,
        secret_key=secret_key,
    )

    simple_transaction_app = AppConfig(
        name="simple_transaction",
        host=os.environ.get("SIMPLE_TRANSACTION_HOST", "127.0.0.1"),
        port=int(os.environ.get("SIMPLE_TRANSACTION_PORT", "5004")),
        debug=debug,
        secret_key=secret_key,
    )

    return Settings(
        database=db,
        secret_key=secret_key,
        debug=debug,
        log_level=log_level,
        admin_app=admin_app,
        client_app=client_app,
        hacker_app=hacker_app,
        fraud_detector_app=fraud_detector_app,
        simple_transaction_app=simple_transaction_app,
    )


# Module-level singleton — imported once per process
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached settings (loads once per process)."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
