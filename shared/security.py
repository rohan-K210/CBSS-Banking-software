"""
Security utilities and Flask application factory.

Provides:
- create_app(): factory that configures a Flask app with shared settings
- register_error_handlers(): consistent JSON/error responses
- require_session(): decorator for session-protected routes
"""

import logging
import traceback
from functools import wraps
from typing import Any, Callable

from flask import Flask, jsonify, redirect, request, session, url_for

from shared.config import AppConfig, get_settings
from shared.exceptions import (
    CBSSBaseException,
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from shared.logging_config import setup_logging

logger = logging.getLogger(__name__)


def create_app(
    config: AppConfig,
    template_folder: str | None = None,
    static_folder: str | None = None,
) -> Flask:
    """
    Create and configure a Flask application.

    Args:
        config: AppConfig dataclass with name, port, debug, etc.
        template_folder: Path to templates directory (defaults to ../templates).
        static_folder: Path to static files directory.
    """
    settings = get_settings()

    # Default template folder: ../Templates relative to this file
    from pathlib import Path
    _project_root = Path(__file__).resolve().parent.parent

    if template_folder is None:
        template_folder = str(_project_root / "templates")

    if static_folder is None:
        static_folder = str(_project_root / "static")

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )

    app.secret_key = config.secret_key
    app.config["DEBUG"] = settings.debug
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Setup logging for this service
    setup_logging(config.name, level=settings.log_level)

    # Register error handlers
    register_error_handlers(app)

    logger.info(
        "Flask app '%s' created: host=%s port=%d debug=%s",
        config.name,
        config.host,
        config.port,
        config.debug,
    )

    return app


def register_error_handlers(app: Flask) -> None:
    """Register consistent error handlers on a Flask app."""

    @app.errorhandler(404)
    def not_found(error: Any) -> tuple:
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found",
                },
            }), 404
        return f"<h1>404 - Page Not Found</h1><p>The URL '{request.path}' was not found.</p>", 404

    @app.errorhandler(405)
    def method_not_allowed(error: Any) -> tuple:
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": f"Method {request.method} not allowed",
                },
            }), 405
        return f"<h1>405 - Method Not Allowed</h1>", 405

    @app.errorhandler(500)
    def internal_error(error: Any) -> tuple:
        logger.error("Internal server error: %s", error, exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                },
            }), 500
        return "<h1>500 - Internal Server Error</h1><p>Please check the logs.</p>", 500

    @app.errorhandler(CBSSBaseException)
    def handle_app_error(error: CBSSBaseException) -> tuple:
        """Handle all custom CBSS exceptions consistently."""
        status_code = _get_status_code(error)
        logger.warning("Application error [%s]: %s", type(error).__name__, error.message)

        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": {
                    "code": type(error).__name__.upper(),
                    "message": error.message,
                },
            }), status_code

        # For HTML routes, return a simple error page
        return f"<h1>Error</h1><p>{error.message}</p>", status_code


def _get_status_code(error: CBSSBaseException) -> int:
    """Map exception type to HTTP status code."""
    mapping = {
        ValidationError: 400,
        AuthenticationError: 401,
        AuthorizationError: 403,
        NotFoundError: 404,
        DatabaseError: 500,
        ConfigurationError: 500,
    }
    for exc_type, code in mapping.items():
        if isinstance(error, exc_type):
            return code
    return 500


def require_session(f: Callable) -> Callable:
    """Decorator that redirects to login if user is not in session."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "sender_id" not in session:
            from flask import flash

            flash("You must log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function
