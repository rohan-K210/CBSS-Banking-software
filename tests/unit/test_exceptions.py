"""Tests for shared.exceptions module."""

from shared.exceptions import (
    CBSSBaseException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    CustomerNotFoundError,
    EmployeeNotFoundError,
    TransactionNotFoundError,
    DatabaseError,
    ConfigurationError,
    LoanModelError,
    SegmentationError,
    FraudDetectionError,
)


class TestExceptionHierarchy:
    """Verify exception inheritance and messages."""

    def test_base_exception(self):
        exc = CBSSBaseException("test error")
        assert str(exc) == "test error"
        assert exc.message == "test error"
        assert isinstance(exc, Exception)

    def test_validation_error(self):
        exc = ValidationError("bad input", field="email")
        assert exc.field == "email"
        assert "bad input" in str(exc)
        assert isinstance(exc, CBSSBaseException)

    def test_authentication_error(self):
        exc = AuthenticationError()
        assert "Authentication failed" in str(exc)
        assert isinstance(exc, CBSSBaseException)

    def test_authorization_error(self):
        exc = AuthorizationError("denied")
        assert exc.message == "denied"
        assert isinstance(exc, CBSSBaseException)

    def test_not_found_error(self):
        exc = NotFoundError("User", 42)
        assert "User not found" in str(exc)
        assert exc.resource == "User"
        assert exc.resource_id == 42

    def test_customer_not_found(self):
        exc = CustomerNotFoundError(99)
        assert "Customer" in str(exc)
        assert exc.resource_id == 99
        assert isinstance(exc, NotFoundError)

    def test_employee_not_found(self):
        exc = EmployeeNotFoundError()
        assert "Employee" in str(exc)

    def test_transaction_not_found(self):
        exc = TransactionNotFoundError("abc-123")
        assert "Transaction" in str(exc)

    def test_database_error(self):
        orig = ConnectionError("timeout")
        exc = DatabaseError("conn failed", original=orig)
        assert exc.original is orig
        assert isinstance(exc, CBSSBaseException)

    def test_configuration_error(self):
        exc = ConfigurationError("missing DB_HOST")
        assert isinstance(exc, CBSSBaseException)

    def test_loan_model_error(self):
        exc = LoanModelError("no data")
        assert isinstance(exc, CBSSBaseException)

    def test_segmentation_error(self):
        exc = SegmentationError("cluster fail")
        assert isinstance(exc, CBSSBaseException)

    def test_fraud_detection_error(self):
        exc = FraudDetectionError("model fail")
        assert isinstance(exc, CBSSBaseException)
