"""
Custom exception hierarchy for the CBSS backend.

All application exceptions inherit from CBSSBaseException so they can be
caught generically at the Flask error handler level.

Exception hierarchy:
    CBSSBaseException
    ├── ValidationError
    ├── AuthenticationError
    ├── AuthorizationError
    ├── NotFoundError
    │   ├── CustomerNotFoundError
    │   ├── EmployeeNotFoundError
    │   └── TransactionNotFoundError
    ├── DatabaseError
    ├── ExternalServiceError
    ├── ConfigurationError
    └── ModelError
        ├── LoanModelError
        ├── SegmentationError
        └── FraudDetectionError
"""

from __future__ import annotations


class CBSSBaseException(Exception):
    """Base exception for all CBSS application errors."""

    def __init__(self, message: str = "An application error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class ValidationError(CBSSBaseException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Invalid input", field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


class AuthenticationError(CBSSBaseException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class AuthorizationError(CBSSBaseException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Authorization denied") -> None:
        super().__init__(message)


class NotFoundError(CBSSBaseException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", resource_id: str | int | None = None) -> None:
        self.resource = resource
        self.resource_id = resource_id
        msg = f"{resource} not found" + (f" (id={resource_id})" if resource_id else "")
        super().__init__(msg)


class CustomerNotFoundError(NotFoundError):
    """Raised when a customer is not found."""

    def __init__(self, customer_id: str | int | None = None) -> None:
        super().__init__("Customer", customer_id)


class EmployeeNotFoundError(NotFoundError):
    """Raised when an employee is not found."""

    def __init__(self, employee_id: str | int | None = None) -> None:
        super().__init__("Employee", employee_id)


class TransactionNotFoundError(NotFoundError):
    """Raised when a transaction is not found."""

    def __init__(self, transaction_id: str | None = None) -> None:
        super().__init__("Transaction", transaction_id)


class DatabaseError(CBSSBaseException):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed", original: Exception | None = None) -> None:
        self.original = original
        super().__init__(message)


class ExternalServiceError(CBSSBaseException):
    """Raised when an external service call fails."""

    def __init__(self, service: str = "external service", message: str = "Service unavailable") -> None:
        self.service = service
        super().__init__(f"{service}: {message}")


class ConfigurationError(CBSSBaseException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str = "Configuration error") -> None:
        super().__init__(message)


class ModelError(CBSSBaseException):
    """Base exception for ML model errors."""

    def __init__(self, message: str = "Model error") -> None:
        super().__init__(message)


class LoanModelError(ModelError):
    """Raised when the loan evaluation model fails."""

    def __init__(self, message: str = "Loan evaluation failed") -> None:
        super().__init__(message)


class SegmentationError(ModelError):
    """Raised when customer segmentation fails."""

    def __init__(self, message: str = "Customer segmentation failed") -> None:
        super().__init__(message)


class FraudDetectionError(ModelError):
    """Raised when fraud detection fails."""

    def __init__(self, message: str = "Fraud detection failed") -> None:
        super().__init__(message)
