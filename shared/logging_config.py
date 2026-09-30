"""
Centralized logging configuration for the CBSS backend.

Each application gets a distinct log prefix so logs from all 5 services
can be distinguished in a shared terminal or log file.

Usage:
    from shared.logging_config import setup_logging
    setup_logging("admin")  # prefix all logs with [ADMIN]
"""

import logging
import sys
from datetime import datetime, timezone


class ServiceFormatter(logging.Formatter):
    """Custom formatter that prepends a service tag and ISO timestamp."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name.upper()

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        level = record.levelname.ljust(8)
        module = record.name
        msg = record.getMessage()

        parts = [
            f"[{timestamp}]",
            f"[{self.service_name}]",
            f"[{level}]",
            f"[{module}]",
            msg,
        ]

        if record.exc_info and record.exc_info[0] is not None:
            exc_text = self.formatException(record.exc_info)
            parts.append(f"\n{exc_text}")

        return " ".join(parts)


def setup_logging(
    service_name: str,
    level: str = "INFO",
    output: int = sys.stderr,
) -> None:
    """
    Configure root logger for a specific service.

    Args:
        service_name: Name shown in log prefix (e.g., "admin", "client").
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        output: File object for output (default: stderr).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicate output
    root_logger.handlers.clear()

    handler = logging.StreamHandler(output)
    handler.setFormatter(ServiceFormatter(service_name))
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialized: service=%s level=%s", service_name, level
    )
