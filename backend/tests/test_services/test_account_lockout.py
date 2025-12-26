"""Comprehensive tests for account_lockout service.

Tests cover:
- LockoutConfig dataclass
- AttemptRecord dataclass
- AccountLockoutService class
- is_locked method
- get_lockout_remaining_seconds method
- record_failed_attempt method
- record_successful_login method
- clear_lockout method
- get_attempt_count method
- _mask_identifier static method
- get_lockout_service singleton
- reset_lockout_service function
"""

from __future__ import annotations

import time

import pytest

from app.services.account_lockout import (
    AccountLockoutService,
    LockoutConfig,
    get_lockout_service,
    reset_lockout_service,
)

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestLockoutConfig:
    """Tests for LockoutConfig dataclass."""

    def test_default_max_attempts(self) -> None:
        """Test default max_attempts is 5."""
        config = LockoutConfig()
        assert config.max_attempts == 5

    def test_default_lockout_duration(self) -> None:
        """Test default lockout_duration_seconds is 900 (15 minutes)."""
        config = LockoutConfig()
        assert config.lockout_duration_seconds == 900

    def test_default_attempt_window(self) -> None:
        """Test default attempt_window_seconds is 300 (5 minutes)."""
        config = LockoutConfig()
        assert config.attempt_window_seconds == 300

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = LockoutConfig(
            max_attempts=3,
            lockout_duration_seconds=600,
            attempt_window_seconds=120,
        )
        assert config.max_attempts == 3
        assert config.lockout_duration_seconds == 600
        assert config.attempt_window_seconds == 120


class TestAccountLockoutService:
    """Tests for AccountLockoutService class."""

    def test_init_with_default_config(self) -> None:
        """Test initialization with default config."""
        service = AccountLockoutService()
        assert service._config.max_attempts == 5

    def test_init_with_custom_config(self) -> None:
        """Test initialization with custom config."""
        config = LockoutConfig(max_attempts=3)
        service = AccountLockoutService(config)
        assert service._config.max_attempts == 3


class TestIsLocked:
    """Tests for is_locked method."""

    def test_unlocked_by_default(self) -> None:
        """Test account is not locked by default."""
        service = AccountLockoutService()
        assert service.is_locked("test@example.com") is False

    def test_locked_after_max_attempts(self) -> None:
        """Test account is locked after max attempts."""
        config = LockoutConfig(max_attempts=3)
        service = AccountLockoutService(config)
        for _ in range(3):
            service.record_failed_attempt("test@example.com")
        assert service.is_locked("test@example.com") is True

    def test_unlocked_after_lockout_expires(self) -> None:
        """Test account is unlocked after lockout expires."""
        config = LockoutConfig(max_attempts=3, lockout_duration_seconds=1)
        service = AccountLockoutService(config)
        for _ in range(3):
            service.record_failed_attempt("test@example.com")
        assert service.is_locked("test@example.com") is True
        time.sleep(1.1)
        assert service.is_locked("test@example.com") is False


class TestGetLockoutRemainingSeconds:
    """Tests for get_lockout_remaining_seconds method."""

    def test_zero_when_not_locked(self) -> None:
        """Test returns 0 when account is not locked."""
        service = AccountLockoutService()
        assert service.get_lockout_remaining_seconds("test@example.com") == 0

    def test_returns_remaining_time(self) -> None:
        """Test returns remaining lockout time."""
        config = LockoutConfig(max_attempts=2, lockout_duration_seconds=10)
        service = AccountLockoutService(config)
        service.record_failed_attempt("test@example.com")
        service.record_failed_attempt("test@example.com")
        remaining = service.get_lockout_remaining_seconds("test@example.com")
        assert 8 <= remaining <= 10


class TestRecordFailedAttempt:
    """Tests for record_failed_attempt method."""

    def test_returns_false_before_lockout(self) -> None:
        """Test returns False before reaching max attempts."""
        config = LockoutConfig(max_attempts=3)
        service = AccountLockoutService(config)
        assert service.record_failed_attempt("test@example.com") is False
        assert service.record_failed_attempt("test@example.com") is False

    def test_returns_true_on_lockout(self) -> None:
        """Test returns True when lockout is triggered."""
        config = LockoutConfig(max_attempts=3)
        service = AccountLockoutService(config)
        service.record_failed_attempt("test@example.com")
        service.record_failed_attempt("test@example.com")
        assert service.record_failed_attempt("test@example.com") is True

    def test_cleans_old_attempts(self) -> None:
        """Test old attempts outside window are cleaned."""
        config = LockoutConfig(max_attempts=3, attempt_window_seconds=1)
        service = AccountLockoutService(config)
        service.record_failed_attempt("test@example.com")
        service.record_failed_attempt("test@example.com")
        time.sleep(1.1)
        # Old attempts should be cleaned, so we start fresh
        assert service.record_failed_attempt("test@example.com") is False


class TestRecordSuccessfulLogin:
    """Tests for record_successful_login method."""

    def test_clears_failed_attempts(self) -> None:
        """Test successful login clears failed attempts."""
        service = AccountLockoutService()
        service.record_failed_attempt("test@example.com")
        service.record_failed_attempt("test@example.com")
        assert service.get_attempt_count("test@example.com") == 2
        service.record_successful_login("test@example.com")
        assert service.get_attempt_count("test@example.com") == 0

    def test_no_error_for_unknown_identifier(self) -> None:
        """Test no error when clearing unknown identifier."""
        service = AccountLockoutService()
        service.record_successful_login("unknown@example.com")  # Should not raise


class TestClearLockout:
    """Tests for clear_lockout method."""

    def test_clears_lockout(self) -> None:
        """Test clear_lockout removes lockout."""
        config = LockoutConfig(max_attempts=2)
        service = AccountLockoutService(config)
        service.record_failed_attempt("test@example.com")
        service.record_failed_attempt("test@example.com")
        assert service.is_locked("test@example.com") is True
        service.clear_lockout("test@example.com")
        assert service.is_locked("test@example.com") is False

    def test_no_error_for_unknown_identifier(self) -> None:
        """Test no error when clearing unknown identifier."""
        service = AccountLockoutService()
        service.clear_lockout("unknown@example.com")  # Should not raise


class TestGetAttemptCount:
    """Tests for get_attempt_count method."""

    def test_zero_for_new_identifier(self) -> None:
        """Test returns 0 for new identifier."""
        service = AccountLockoutService()
        assert service.get_attempt_count("test@example.com") == 0

    def test_counts_attempts(self) -> None:
        """Test correctly counts failed attempts."""
        service = AccountLockoutService()
        service.record_failed_attempt("test@example.com")
        assert service.get_attempt_count("test@example.com") == 1
        service.record_failed_attempt("test@example.com")
        assert service.get_attempt_count("test@example.com") == 2


class TestMaskIdentifier:
    """Tests for _mask_identifier static method."""

    def test_mask_email(self) -> None:
        """Test masking email address."""
        masked = AccountLockoutService._mask_identifier("test@example.com")
        assert masked == "tes***@example.com"

    def test_mask_short_email(self) -> None:
        """Test masking short email address."""
        masked = AccountLockoutService._mask_identifier("ab@example.com")
        assert masked == "ab***@example.com"

    def test_mask_username(self) -> None:
        """Test masking username."""
        masked = AccountLockoutService._mask_identifier("testuser")
        assert masked == "tes***"

    def test_mask_short_username(self) -> None:
        """Test masking short username."""
        masked = AccountLockoutService._mask_identifier("ab")
        assert masked == "***"


class TestSingletonFunctions:
    """Tests for singleton functions."""

    def test_get_lockout_service_returns_instance(self) -> None:
        """Test get_lockout_service returns an instance."""
        reset_lockout_service()
        service = get_lockout_service()
        assert isinstance(service, AccountLockoutService)

    def test_get_lockout_service_returns_same_instance(self) -> None:
        """Test get_lockout_service returns the same instance."""
        reset_lockout_service()
        service1 = get_lockout_service()
        service2 = get_lockout_service()
        assert service1 is service2

    def test_reset_lockout_service_creates_new_instance(self) -> None:
        """Test reset_lockout_service creates new instance."""
        service1 = get_lockout_service()
        reset_lockout_service()
        service2 = get_lockout_service()
        assert service1 is not service2

    def test_reset_lockout_service_with_config(self) -> None:
        """Test reset_lockout_service with custom config."""
        config = LockoutConfig(max_attempts=10)
        reset_lockout_service(config)
        service = get_lockout_service()
        assert service._config.max_attempts == 10
