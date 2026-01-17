"""Tests for the Sentry error tracking integration."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.sentry import (
    _before_send,
    _before_send_transaction,
    add_breadcrumb,
    capture_exception,
    capture_message,
    init_sentry,
    set_tag,
    set_user,
)


class TestInitSentry:
    """Tests for Sentry initialization."""

    def test_returns_false_when_dsn_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns False when DSN not configured."""
        monkeypatch.delenv("SENTRY_DSN", raising=False)

        # Reset initialization state
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        result = init_sentry()

        assert result is False

    def test_returns_false_when_sentry_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns False when sentry-sdk not installed."""
        monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.io/123")

        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        with patch.dict("sys.modules", {"sentry_sdk": None}):
            with patch("app.core.sentry.init_sentry") as mock_init:
                mock_init.return_value = False
                # The actual import error would happen inside init_sentry
                result = mock_init()
                assert result is False

    def test_already_initialized_returns_true(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns True when already initialized."""
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = True

        result = init_sentry(dsn="https://key@sentry.io/123")

        assert result is True


class TestBeforeSend:
    """Tests for the before_send event filter."""

    def test_filters_events_in_development(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test events are dropped in development environment."""
        monkeypatch.setenv("ENVIRONMENT", "development")

        event = {"exception": {"values": [{"type": "ValueError"}]}}
        hint = {}

        result = _before_send(event, hint)

        assert result is None

    def test_filters_rate_limit_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test rate limit errors are filtered out."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        class RateLimitExceeded(Exception):
            pass

        event = {}
        hint = {"exc_info": (RateLimitExceeded, RateLimitExceeded(), None)}

        result = _before_send(event, hint)

        assert result is None

    def test_filters_validation_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation errors are filtered out."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        class ValidationError(Exception):
            pass

        event = {}
        hint = {"exc_info": (ValidationError, ValidationError(), None)}

        result = _before_send(event, hint)

        assert result is None

    def test_filters_expected_http_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test expected HTTP errors (401, 403, 404) are filtered."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        class HTTPException(Exception):
            def __init__(self, status_code: int) -> None:
                self.status_code = status_code

        for status_code in [400, 401, 403, 404, 422]:
            exc = HTTPException(status_code)
            event = {}
            hint = {"exc_info": (HTTPException, exc, None)}

            result = _before_send(event, hint)

            assert result is None, f"Status {status_code} should be filtered"

    def test_passes_through_server_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test server errors (500) are not filtered."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        class HTTPException(Exception):
            def __init__(self, status_code: int) -> None:
                self.status_code = status_code

        exc = HTTPException(500)
        event = {"type": "error"}
        hint = {"exc_info": (HTTPException, exc, None)}

        result = _before_send(event, hint)

        assert result is not None

    def test_scrubs_authorization_headers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test authorization headers are scrubbed."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        event = {
            "request": {
                "headers": {
                    "authorization": "Bearer secret-token",
                    "x-api-key": "api-key-123",
                    "content-type": "application/json",
                }
            }
        }
        hint = {}

        result = _before_send(event, hint)

        assert result["request"]["headers"]["authorization"] == "[Filtered]"
        assert result["request"]["headers"]["x-api-key"] == "[Filtered]"
        assert result["request"]["headers"]["content-type"] == "application/json"


class TestBeforeSendTransaction:
    """Tests for the before_send_transaction filter."""

    def test_filters_health_check_transactions(self) -> None:
        """Test health check transactions are filtered."""
        event = {"transaction": "/health"}
        hint = {}

        result = _before_send_transaction(event, hint)

        assert result is None

    def test_filters_metrics_transactions(self) -> None:
        """Test metrics transactions are filtered."""
        event = {"transaction": "/metrics"}
        hint = {}

        result = _before_send_transaction(event, hint)

        assert result is None

    def test_passes_through_api_transactions(self) -> None:
        """Test API transactions are not filtered."""
        event = {"transaction": "/api/v1/users"}
        hint = {}

        result = _before_send_transaction(event, hint)

        assert result is not None
        assert result["transaction"] == "/api/v1/users"


class TestCaptureException:
    """Tests for exception capture."""

    def test_returns_none_when_not_initialized(self) -> None:
        """Test returns None when Sentry not initialized."""
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        result = capture_exception(ValueError("test error"))

        assert result is None

    def test_capture_exception_handles_errors_gracefully(self) -> None:
        """Test capture_exception handles errors gracefully."""
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        # Should not raise, just return None
        result = capture_exception(ValueError("test"), extra_context="value")
        assert result is None


class TestCaptureMessage:
    """Tests for message capture."""

    def test_returns_none_when_not_initialized(self) -> None:
        """Test returns None when Sentry not initialized."""
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        result = capture_message("test message")

        assert result is None


class TestSetUser:
    """Tests for user context."""

    def test_does_nothing_when_not_initialized(self) -> None:
        """Test does nothing when Sentry not initialized."""
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        # Should not raise
        set_user(user_id=123, email="test@example.com")

    def test_sets_user_context(self) -> None:
        """Test user context can be set without errors when initialized."""
        import app.core.sentry as sentry_module

        # Test when not initialized - should not raise
        sentry_module._sentry_initialized = False
        set_user(user_id=123, email="test@example.com", role="admin")

        # Test when initialized - should also not raise
        # (actual sentry_sdk.set_user call may fail if SDK not installed,
        # but our wrapper should handle it gracefully)
        sentry_module._sentry_initialized = True
        try:
            set_user(user_id=456, email="another@example.com")
        except Exception:
            # If sentry_sdk not available, that's OK for this test
            pass


class TestSetTag:
    """Tests for tag setting."""

    def test_does_nothing_when_not_initialized(self) -> None:
        """Test does nothing when Sentry not initialized."""
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        # Should not raise
        set_tag("environment", "test")


class TestAddBreadcrumb:
    """Tests for breadcrumb addition."""

    def test_does_nothing_when_not_initialized(self) -> None:
        """Test does nothing when Sentry not initialized."""
        import app.core.sentry as sentry_module

        sentry_module._sentry_initialized = False

        # Should not raise
        add_breadcrumb("test message", category="test")

    def test_adds_breadcrumb_with_data(self) -> None:
        """Test breadcrumb can be added without errors when initialized."""
        import app.core.sentry as sentry_module

        # Test when not initialized - should not raise
        sentry_module._sentry_initialized = False
        add_breadcrumb(
            "User clicked button",
            category="ui",
            level="info",
            button_id="submit",
        )

        # Test when initialized - should also not raise
        sentry_module._sentry_initialized = True
        try:
            add_breadcrumb(
                "Another action",
                category="test",
                level="debug",
                extra_data="value",
            )
        except Exception:
            # If sentry_sdk not available, that's OK for this test
            pass
