"""Standardized exception hierarchy for the application.

This module provides a structured exception hierarchy that enables:
- Consistent error responses across all API endpoints
- Machine-readable error codes for client-side handling
- Proper exception chaining for debugging
- Centralized error logging and monitoring

Usage:
    from app.core.exceptions import NotFoundError, ValidationError

    # Raise domain-specific errors
    raise NotFoundError("Property", property_id)
    raise ValidationError("email", "Invalid email format")

    # Chain exceptions for debugging
    try:
        result = await external_api.fetch()
    except ExternalAPIError as e:
        raise IntegrationError("PropertyGuru", "Failed to sync listing") from e
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True, frozen=True)
class ErrorDetail:
    """Structured error detail for validation errors.

    Attributes:
        field: The field name that caused the error (e.g., "email", "property_id")
        message: Human-readable error message
        code: Machine-readable error code (e.g., "invalid_format", "required")
    """

    field: str
    message: str
    code: str = "invalid"


@dataclass(slots=True)
class ErrorResponse:
    """Standardized error response schema.

    This schema is used for all error responses to ensure consistency
    across the API. Clients can rely on this structure for error handling.

    Attributes:
        error_code: Machine-readable error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional list of field-level errors for validation failures
        timestamp: ISO 8601 timestamp of when the error occurred
        correlation_id: Request correlation ID for tracing (set by middleware)
    """

    error_code: str
    message: str
    status_code: int
    details: list[ErrorDetail] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "timestamp": self.timestamp,
        }
        if self.details:
            result["details"] = [
                {"field": d.field, "message": d.message, "code": d.code}
                for d in self.details
            ]
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        return result


class AppError(Exception):
    """Base exception class for all application errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and response formatting.

    Attributes:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code to return
        details: Optional list of field-level error details
    """

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or []

    def to_response(self, correlation_id: str | None = None) -> ErrorResponse:
        """Convert exception to standardized error response."""
        return ErrorResponse(
            error_code=self.error_code,
            message=self.message,
            status_code=self.status_code,
            details=self.details,
            correlation_id=correlation_id,
        )


class NotFoundError(AppError):
    """Raised when a requested resource does not exist.

    Usage:
        raise NotFoundError("Property", property_id)
        raise NotFoundError("User", user_id, "User account not found")
    """

    error_code = "NOT_FOUND"
    status_code = 404

    def __init__(
        self,
        resource_type: str,
        resource_id: str | int | None = None,
        message: str | None = None,
    ) -> None:
        if message is None:
            if resource_id is not None:
                message = f"{resource_type} with id '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"
        super().__init__(message)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(AppError):
    """Raised when request data fails validation.

    Usage:
        raise ValidationError("email", "Invalid email format")
        raise ValidationError(details=[
            ErrorDetail("email", "Required field", "required"),
            ErrorDetail("password", "Too short", "min_length"),
        ])
    """

    error_code = "VALIDATION_ERROR"
    status_code = 422

    def __init__(
        self,
        field: str | None = None,
        message: str = "Validation failed",
        *,
        code: str = "invalid",
        details: list[ErrorDetail] | None = None,
    ) -> None:
        if details is None and field is not None:
            details = [ErrorDetail(field=field, message=message, code=code)]
        super().__init__(message, details=details)
        self.field = field


class AuthenticationError(AppError):
    """Raised when authentication fails or credentials are invalid.

    Usage:
        raise AuthenticationError()  # Generic auth failure
        raise AuthenticationError("Token expired")
        raise AuthenticationError("Invalid API key", error_code="INVALID_API_KEY")
    """

    error_code = "AUTHENTICATION_FAILED"
    status_code = 401

    def __init__(
        self,
        message: str = "Authentication required",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code)


class AuthorizationError(AppError):
    """Raised when user lacks permission for the requested action.

    Usage:
        raise AuthorizationError()  # Generic permission denied
        raise AuthorizationError("Only admins can delete users")
        raise AuthorizationError(required_role="reviewer")
    """

    error_code = "FORBIDDEN"
    status_code = 403

    def __init__(
        self,
        message: str = "Permission denied",
        *,
        required_role: str | None = None,
        required_permission: str | None = None,
    ) -> None:
        if required_role and message == "Permission denied":
            message = f"Role '{required_role}' required for this action"
        if required_permission and message == "Permission denied":
            message = f"Permission '{required_permission}' required for this action"
        super().__init__(message)
        self.required_role = required_role
        self.required_permission = required_permission


class ConflictError(AppError):
    """Raised when an action conflicts with existing state.

    Usage:
        raise ConflictError("User with this email already exists")
        raise ConflictError("Property", "address", "123 Main St")
    """

    error_code = "CONFLICT"
    status_code = 409

    def __init__(
        self,
        message: str = "Resource conflict",
        resource_type: str | None = None,
        field: str | None = None,
        value: str | None = None,
    ) -> None:
        if resource_type and field and value:
            message = f"{resource_type} with {field} '{value}' already exists"
        super().__init__(message)
        self.resource_type = resource_type
        self.field = field
        self.value = value


class RateLimitError(AppError):
    """Raised when rate limit is exceeded.

    Usage:
        raise RateLimitError()
        raise RateLimitError(retry_after=60)
    """

    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry later.",
        *,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class IntegrationError(AppError):
    """Raised when an external service integration fails.

    Usage:
        raise IntegrationError("PropertyGuru", "Failed to sync listing")
        raise IntegrationError("Stripe", "Payment processing failed", retriable=True)
    """

    error_code = "INTEGRATION_ERROR"
    status_code = 502

    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        *,
        retriable: bool = False,
    ) -> None:
        full_message = f"{service_name}: {message}"
        super().__init__(full_message)
        self.service_name = service_name
        self.retriable = retriable


class BusinessRuleError(AppError):
    """Raised when a business rule or invariant is violated.

    Usage:
        raise BusinessRuleError("Cannot delete property with active deals")
        raise BusinessRuleError("Scenario budget exceeds project limit", "BUDGET_EXCEEDED")
    """

    error_code = "BUSINESS_RULE_VIOLATION"
    status_code = 422

    def __init__(
        self,
        message: str,
        rule_code: str | None = None,
    ) -> None:
        error_code = rule_code if rule_code else "BUSINESS_RULE_VIOLATION"
        super().__init__(message, error_code=error_code)
        self.rule_code = rule_code


class ServiceUnavailableError(AppError):
    """Raised when a service is temporarily unavailable.

    Usage:
        raise ServiceUnavailableError()
        raise ServiceUnavailableError("Database maintenance in progress", retry_after=300)
    """

    error_code = "SERVICE_UNAVAILABLE"
    status_code = 503

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        *,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


__all__ = [
    "AppError",
    "AuthenticationError",
    "AuthorizationError",
    "BusinessRuleError",
    "ConflictError",
    "ErrorDetail",
    "ErrorResponse",
    "IntegrationError",
    "NotFoundError",
    "RateLimitError",
    "ServiceUnavailableError",
    "ValidationError",
]
