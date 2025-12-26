"""Tests for the exception handler middleware.

Tests cover:
- AppError exception handling with standardized responses
- Error response format and headers
- Correlation ID propagation
- Retry-After header for rate limit and service unavailable errors
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)
from app.middleware.exception_handler import (
    app_error_handler,
    register_exception_handlers,
)


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application with exception handlers."""
    test_app = FastAPI()
    register_exception_handlers(test_app)
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the application."""
    return TestClient(app, raise_server_exceptions=False)


class TestAppErrorHandler:
    """Tests for the app_error_handler function."""

    @pytest.mark.asyncio
    async def test_handles_not_found_error(self) -> None:
        """Test handling NotFoundError returns 404 with correct format."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.correlation_id = "test-correlation-id"
        request.url.path = "/api/v1/properties/123"
        request.method = "GET"

        error = NotFoundError("Property", 123)

        with patch("app.middleware.exception_handler.log_event"):
            response = await app_error_handler(request, error)

        assert response.status_code == 404
        body = response.body.decode()
        assert "NOT_FOUND" in body
        assert "Property" in body
        assert "test-correlation-id" in body

    @pytest.mark.asyncio
    async def test_handles_validation_error(self) -> None:
        """Test handling ValidationError returns 422 with details."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.correlation_id = None
        request.url.path = "/api/v1/users"
        request.method = "POST"

        error = ValidationError("email", "Invalid email format")

        with patch("app.middleware.exception_handler.log_event"):
            response = await app_error_handler(request, error)

        assert response.status_code == 422
        body = response.body.decode()
        assert "VALIDATION_ERROR" in body
        assert "email" in body

    @pytest.mark.asyncio
    async def test_handles_authentication_error(self) -> None:
        """Test handling AuthenticationError returns 401."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.correlation_id = None
        request.url.path = "/api/v1/me"
        request.method = "GET"

        error = AuthenticationError("Token expired")

        with patch("app.middleware.exception_handler.log_event"):
            response = await app_error_handler(request, error)

        assert response.status_code == 401
        body = response.body.decode()
        assert "AUTHENTICATION_FAILED" in body

    @pytest.mark.asyncio
    async def test_handles_authorization_error(self) -> None:
        """Test handling AuthorizationError returns 403."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.correlation_id = None
        request.url.path = "/api/v1/admin/users"
        request.method = "DELETE"

        error = AuthorizationError(required_role="admin")

        with patch("app.middleware.exception_handler.log_event"):
            response = await app_error_handler(request, error)

        assert response.status_code == 403
        body = response.body.decode()
        assert "FORBIDDEN" in body

    @pytest.mark.asyncio
    async def test_rate_limit_error_includes_retry_after_header(self) -> None:
        """Test RateLimitError includes Retry-After header."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.correlation_id = None
        request.url.path = "/api/v1/search"
        request.method = "GET"

        error = RateLimitError(retry_after=60)

        with patch("app.middleware.exception_handler.log_event"):
            response = await app_error_handler(request, error)

        assert response.status_code == 429
        assert response.headers.get("Retry-After") == "60"

    @pytest.mark.asyncio
    async def test_service_unavailable_includes_retry_after_header(self) -> None:
        """Test ServiceUnavailableError includes Retry-After header."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.correlation_id = None
        request.url.path = "/api/v1/health"
        request.method = "GET"

        error = ServiceUnavailableError("Maintenance", retry_after=300)

        with patch("app.middleware.exception_handler.log_event"):
            response = await app_error_handler(request, error)

        assert response.status_code == 503
        assert response.headers.get("Retry-After") == "300"

    @pytest.mark.asyncio
    async def test_correlation_id_in_response_header(self) -> None:
        """Test correlation ID is included in response header."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.correlation_id = "my-correlation-id"
        request.url.path = "/api/v1/test"
        request.method = "GET"

        error = AppError("Test error")

        with patch("app.middleware.exception_handler.log_event"):
            response = await app_error_handler(request, error)

        assert response.headers.get("X-Correlation-ID") == "my-correlation-id"


class TestExceptionHandlerIntegration:
    """Integration tests for exception handlers with FastAPI."""

    def test_not_found_error_integration(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test NotFoundError is handled correctly in route."""

        @app.get("/test/not-found")
        async def raise_not_found() -> None:
            raise NotFoundError("Resource", 999)

        response = client.get("/test/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "NOT_FOUND"
        assert "Resource" in data["message"]
        assert "timestamp" in data

    def test_validation_error_integration(
        self, app: FastAPI, client: TestClient
    ) -> None:
        """Test ValidationError is handled correctly in route."""

        @app.post("/test/validate")
        async def raise_validation() -> None:
            raise ValidationError("field", "Invalid value")

        response = client.post("/test/validate")
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "details" in data
        assert len(data["details"]) == 1

    def test_auth_error_integration(self, app: FastAPI, client: TestClient) -> None:
        """Test AuthenticationError is handled correctly in route."""

        @app.get("/test/auth")
        async def raise_auth() -> None:
            raise AuthenticationError()

        response = client.get("/test/auth")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "AUTHENTICATION_FAILED"

    def test_error_response_format(self, app: FastAPI, client: TestClient) -> None:
        """Test that error response follows the standard format."""

        @app.get("/test/error")
        async def raise_error() -> None:
            raise AppError("Test error", error_code="TEST_ERROR", status_code=400)

        response = client.get("/test/error")
        data = response.json()

        # Verify all expected fields are present
        assert "error_code" in data
        assert "message" in data
        assert "status_code" in data
        assert "timestamp" in data

        # Verify field values
        assert data["error_code"] == "TEST_ERROR"
        assert data["message"] == "Test error"
        assert data["status_code"] == 400


class TestRegisterExceptionHandlers:
    """Tests for the register_exception_handlers function."""

    def test_registers_app_error_handler(self) -> None:
        """Test that AppError handler is registered."""
        test_app = FastAPI()
        register_exception_handlers(test_app)

        # Check that handler is registered
        assert AppError in test_app.exception_handlers

    def test_handles_subclasses(self, app: FastAPI, client: TestClient) -> None:
        """Test that all AppError subclasses are handled."""

        @app.get("/test/subclass")
        async def raise_subclass() -> None:
            raise NotFoundError("Test", 1)

        response = client.get("/test/subclass")
        assert response.status_code == 404
        # NotFoundError should be caught by AppError handler
        assert "NOT_FOUND" in response.json()["error_code"]
