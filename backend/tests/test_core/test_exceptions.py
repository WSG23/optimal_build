"""Tests for the standardized exception hierarchy.

Tests cover:
- All exception types and their default values
- Exception to response conversion
- Error response schema serialization
- Error detail handling
"""

import pytest

from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    ErrorDetail,
    ErrorResponse,
    IntegrationError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)


class TestErrorDetail:
    """Tests for ErrorDetail dataclass."""

    def test_error_detail_creation(self) -> None:
        """Test creating an error detail with all fields."""
        detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="invalid_format",
        )
        assert detail.field == "email"
        assert detail.message == "Invalid email format"
        assert detail.code == "invalid_format"

    def test_error_detail_default_code(self) -> None:
        """Test error detail default code is 'invalid'."""
        detail = ErrorDetail(field="name", message="Required")
        assert detail.code == "invalid"


class TestErrorResponse:
    """Tests for ErrorResponse dataclass."""

    def test_error_response_creation(self) -> None:
        """Test creating an error response with all fields."""
        response = ErrorResponse(
            error_code="NOT_FOUND",
            message="Resource not found",
            status_code=404,
            correlation_id="abc-123",
        )
        assert response.error_code == "NOT_FOUND"
        assert response.message == "Resource not found"
        assert response.status_code == 404
        assert response.correlation_id == "abc-123"
        assert response.details == []
        assert response.timestamp is not None

    def test_error_response_with_details(self) -> None:
        """Test error response with field-level errors."""
        details = [
            ErrorDetail("email", "Invalid format", "invalid_format"),
            ErrorDetail("password", "Too short", "min_length"),
        ]
        response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            status_code=422,
            details=details,
        )
        assert len(response.details) == 2
        assert response.details[0].field == "email"
        assert response.details[1].field == "password"

    def test_error_response_to_dict(self) -> None:
        """Test converting error response to dictionary."""
        details = [ErrorDetail("field1", "Error message", "error_code")]
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test message",
            status_code=400,
            details=details,
            correlation_id="xyz-789",
        )
        result = response.to_dict()

        assert result["error_code"] == "TEST_ERROR"
        assert result["message"] == "Test message"
        assert result["status_code"] == 400
        assert result["correlation_id"] == "xyz-789"
        assert len(result["details"]) == 1
        assert result["details"][0]["field"] == "field1"
        assert "timestamp" in result

    def test_error_response_to_dict_without_optional_fields(self) -> None:
        """Test to_dict without optional fields."""
        response = ErrorResponse(
            error_code="TEST",
            message="Test",
            status_code=400,
        )
        result = response.to_dict()

        assert "details" not in result
        assert "correlation_id" not in result


class TestAppError:
    """Tests for base AppError exception."""

    def test_app_error_defaults(self) -> None:
        """Test AppError default values."""
        error = AppError()
        assert error.message == "An unexpected error occurred"
        assert error.error_code == "INTERNAL_ERROR"
        assert error.status_code == 500
        assert error.details == []

    def test_app_error_custom_values(self) -> None:
        """Test AppError with custom values."""
        error = AppError(
            "Custom message",
            error_code="CUSTOM_ERROR",
            status_code=418,
        )
        assert error.message == "Custom message"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.status_code == 418

    def test_app_error_with_details(self) -> None:
        """Test AppError with error details."""
        details = [ErrorDetail("field", "message", "code")]
        error = AppError("Error", details=details)
        assert len(error.details) == 1
        assert error.details[0].field == "field"

    def test_app_error_to_response(self) -> None:
        """Test converting AppError to ErrorResponse."""
        error = AppError("Test error")
        response = error.to_response(correlation_id="test-id")

        assert response.error_code == "INTERNAL_ERROR"
        assert response.message == "Test error"
        assert response.status_code == 500
        assert response.correlation_id == "test-id"

    def test_app_error_is_exception(self) -> None:
        """Test that AppError can be raised and caught."""
        with pytest.raises(AppError) as exc_info:
            raise AppError("Test")
        assert str(exc_info.value) == "Test"


class TestNotFoundError:
    """Tests for NotFoundError exception."""

    def test_not_found_error_with_id(self) -> None:
        """Test NotFoundError with resource type and ID."""
        error = NotFoundError("Property", 123)
        assert error.message == "Property with id '123' not found"
        assert error.error_code == "NOT_FOUND"
        assert error.status_code == 404
        assert error.resource_type == "Property"
        assert error.resource_id == 123

    def test_not_found_error_without_id(self) -> None:
        """Test NotFoundError without resource ID."""
        error = NotFoundError("User")
        assert error.message == "User not found"
        assert error.resource_id is None

    def test_not_found_error_custom_message(self) -> None:
        """Test NotFoundError with custom message."""
        error = NotFoundError("Property", 123, "Property was deleted")
        assert error.message == "Property was deleted"


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_single_field(self) -> None:
        """Test ValidationError for single field."""
        error = ValidationError("email", "Invalid format", code="invalid_format")
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 422
        assert error.field == "email"
        assert len(error.details) == 1
        assert error.details[0].field == "email"
        assert error.details[0].code == "invalid_format"

    def test_validation_error_multiple_fields(self) -> None:
        """Test ValidationError with multiple field errors."""
        details = [
            ErrorDetail("email", "Required", "required"),
            ErrorDetail("password", "Too short", "min_length"),
        ]
        error = ValidationError(details=details)
        assert len(error.details) == 2

    def test_validation_error_default_code(self) -> None:
        """Test ValidationError default error code."""
        error = ValidationError("field", "message")
        assert error.details[0].code == "invalid"


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_authentication_error_defaults(self) -> None:
        """Test AuthenticationError default values."""
        error = AuthenticationError()
        assert error.message == "Authentication required"
        assert error.error_code == "AUTHENTICATION_FAILED"
        assert error.status_code == 401

    def test_authentication_error_custom_message(self) -> None:
        """Test AuthenticationError with custom message."""
        error = AuthenticationError("Token expired")
        assert error.message == "Token expired"

    def test_authentication_error_custom_code(self) -> None:
        """Test AuthenticationError with custom error code."""
        error = AuthenticationError("Invalid API key", error_code="INVALID_API_KEY")
        assert error.error_code == "INVALID_API_KEY"


class TestAuthorizationError:
    """Tests for AuthorizationError exception."""

    def test_authorization_error_defaults(self) -> None:
        """Test AuthorizationError default values."""
        error = AuthorizationError()
        assert error.message == "Permission denied"
        assert error.error_code == "FORBIDDEN"
        assert error.status_code == 403

    def test_authorization_error_with_required_role(self) -> None:
        """Test AuthorizationError with required role."""
        error = AuthorizationError(required_role="admin")
        assert error.message == "Role 'admin' required for this action"
        assert error.required_role == "admin"

    def test_authorization_error_with_required_permission(self) -> None:
        """Test AuthorizationError with required permission."""
        error = AuthorizationError(required_permission="delete_users")
        assert error.message == "Permission 'delete_users' required for this action"
        assert error.required_permission == "delete_users"

    def test_authorization_error_custom_message(self) -> None:
        """Test AuthorizationError with custom message overrides role message."""
        error = AuthorizationError("Only admins can delete", required_role="admin")
        assert error.message == "Only admins can delete"


class TestConflictError:
    """Tests for ConflictError exception."""

    def test_conflict_error_defaults(self) -> None:
        """Test ConflictError default values."""
        error = ConflictError()
        assert error.message == "Resource conflict"
        assert error.error_code == "CONFLICT"
        assert error.status_code == 409

    def test_conflict_error_with_resource_details(self) -> None:
        """Test ConflictError with resource type, field, and value."""
        error = ConflictError(
            resource_type="User",
            field="email",
            value="test@example.com",
        )
        assert error.message == "User with email 'test@example.com' already exists"
        assert error.resource_type == "User"
        assert error.field == "email"
        assert error.value == "test@example.com"

    def test_conflict_error_custom_message(self) -> None:
        """Test ConflictError with custom message."""
        error = ConflictError("Duplicate entry detected")
        assert error.message == "Duplicate entry detected"


class TestRateLimitError:
    """Tests for RateLimitError exception."""

    def test_rate_limit_error_defaults(self) -> None:
        """Test RateLimitError default values."""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded. Please retry later."
        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.status_code == 429
        assert error.retry_after is None

    def test_rate_limit_error_with_retry_after(self) -> None:
        """Test RateLimitError with retry_after value."""
        error = RateLimitError(retry_after=60)
        assert error.retry_after == 60


class TestIntegrationError:
    """Tests for IntegrationError exception."""

    def test_integration_error(self) -> None:
        """Test IntegrationError with service name."""
        error = IntegrationError("PropertyGuru", "API timeout")
        assert error.message == "PropertyGuru: API timeout"
        assert error.error_code == "INTEGRATION_ERROR"
        assert error.status_code == 502
        assert error.service_name == "PropertyGuru"
        assert error.retriable is False

    def test_integration_error_retriable(self) -> None:
        """Test IntegrationError with retriable flag."""
        error = IntegrationError("Stripe", "Temporary failure", retriable=True)
        assert error.retriable is True


class TestBusinessRuleError:
    """Tests for BusinessRuleError exception."""

    def test_business_rule_error(self) -> None:
        """Test BusinessRuleError with message."""
        error = BusinessRuleError("Cannot delete property with active deals")
        assert error.message == "Cannot delete property with active deals"
        assert error.error_code == "BUSINESS_RULE_VIOLATION"
        assert error.status_code == 422
        assert error.rule_code is None

    def test_business_rule_error_with_code(self) -> None:
        """Test BusinessRuleError with custom rule code."""
        error = BusinessRuleError("Budget exceeded", "BUDGET_EXCEEDED")
        assert error.error_code == "BUDGET_EXCEEDED"
        assert error.rule_code == "BUDGET_EXCEEDED"


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError exception."""

    def test_service_unavailable_error_defaults(self) -> None:
        """Test ServiceUnavailableError default values."""
        error = ServiceUnavailableError()
        assert error.message == "Service temporarily unavailable"
        assert error.error_code == "SERVICE_UNAVAILABLE"
        assert error.status_code == 503
        assert error.retry_after is None

    def test_service_unavailable_error_with_retry(self) -> None:
        """Test ServiceUnavailableError with retry_after."""
        error = ServiceUnavailableError("Maintenance in progress", retry_after=300)
        assert error.message == "Maintenance in progress"
        assert error.retry_after == 300


class TestExceptionChaining:
    """Tests for proper exception chaining with 'from'."""

    def test_exception_chaining(self) -> None:
        """Test that exceptions can be properly chained."""
        original_error = ValueError("Original error")

        try:
            try:
                raise original_error
            except ValueError as e:
                raise IntegrationError("ExternalAPI", "Failed") from e
        except IntegrationError as exc:
            assert exc.__cause__ is original_error

    def test_nested_exception_context(self) -> None:
        """Test that exception context is preserved."""
        try:
            try:
                raise NotFoundError("Resource", 1)
            except NotFoundError as e:
                raise AppError("Wrapper error") from e
        except AppError as exc:
            # __context__ is set when exception is raised during handling another
            assert exc.__context__ is not None
