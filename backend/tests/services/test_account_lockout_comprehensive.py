"""Comprehensive tests for account lockout service.

Tests cover:
- Failed attempt tracking
- Account locking behavior
- Lockout expiration
- Successful login clearing
- Admin manual unlock
- Edge cases and timing
"""

from __future__ import annotations

import time


from app.services.account_lockout import (
    AccountLockoutService,
    AttemptRecord,
    LockoutConfig,
    get_lockout_service,
    reset_lockout_service,
)


class TestLockoutConfig:
    """Tests for LockoutConfig dataclass."""

    def test_default_values(self) -> None:
        """Default config should have sensible values."""
        config = LockoutConfig()
        assert config.max_attempts == 5
        assert config.lockout_duration_seconds == 900  # 15 minutes
        assert config.attempt_window_seconds == 300  # 5 minutes

    def test_custom_values(self) -> None:
        """Custom values should be accepted."""
        config = LockoutConfig(
            max_attempts=3,
            lockout_duration_seconds=60,
            attempt_window_seconds=30,
        )
        assert config.max_attempts == 3
        assert config.lockout_duration_seconds == 60
        assert config.attempt_window_seconds == 30


class TestAttemptRecord:
    """Tests for AttemptRecord dataclass."""

    def test_default_values(self) -> None:
        """Default record should have empty attempts and no lockout."""
        record = AttemptRecord()
        assert record.attempts == []
        assert record.locked_until is None

    def test_custom_attempts(self) -> None:
        """Custom attempts list should be accepted."""
        record = AttemptRecord(attempts=[1.0, 2.0, 3.0], locked_until=100.0)
        assert len(record.attempts) == 3
        assert record.locked_until == 100.0


class TestIsLocked:
    """Tests for is_locked method."""

    def test_unlocked_account_returns_false(self) -> None:
        """Unlocked account should return False."""
        service = AccountLockoutService()
        assert service.is_locked("test@example.com") is False

    def test_unknown_account_returns_false(self) -> None:
        """Unknown account should return False."""
        service = AccountLockoutService()
        assert service.is_locked("unknown@example.com") is False

    def test_locked_account_returns_true(self) -> None:
        """Locked account should return True."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        # Lock the account
        service.record_failed_attempt(email)
        service.record_failed_attempt(email)

        assert service.is_locked(email) is True

    def test_expired_lockout_returns_false(self) -> None:
        """Expired lockout should return False."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=1, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        # Lock the account
        service.record_failed_attempt(email)
        service.record_failed_attempt(email)

        # Wait for lockout to expire
        time.sleep(1.5)

        assert service.is_locked(email) is False

    def test_expired_lockout_clears_attempts(self) -> None:
        """Expired lockout should clear attempt history."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=1, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        # Lock the account
        service.record_failed_attempt(email)
        service.record_failed_attempt(email)

        # Wait for lockout to expire
        time.sleep(1.5)

        # Check that is_locked cleared the state
        service.is_locked(email)
        assert service.get_attempt_count(email) == 0


class TestGetLockoutRemainingSeconds:
    """Tests for get_lockout_remaining_seconds method."""

    def test_unlocked_account_returns_zero(self) -> None:
        """Unlocked account should return 0."""
        service = AccountLockoutService()
        assert service.get_lockout_remaining_seconds("test@example.com") == 0

    def test_unknown_account_returns_zero(self) -> None:
        """Unknown account should return 0."""
        service = AccountLockoutService()
        assert service.get_lockout_remaining_seconds("unknown@example.com") == 0

    def test_locked_account_returns_positive_seconds(self) -> None:
        """Locked account should return positive seconds."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        service.record_failed_attempt(email)
        service.record_failed_attempt(email)

        remaining = service.get_lockout_remaining_seconds(email)
        assert 55 <= remaining <= 60

    def test_expired_lockout_returns_zero(self) -> None:
        """Expired lockout should return 0."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=1, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        service.record_failed_attempt(email)
        service.record_failed_attempt(email)

        time.sleep(1.5)

        assert service.get_lockout_remaining_seconds(email) == 0


class TestRecordFailedAttempt:
    """Tests for record_failed_attempt method."""

    def test_first_attempt_not_locked(self) -> None:
        """First failed attempt should not lock account."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=3, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        result = service.record_failed_attempt(email)

        assert result is False
        assert service.get_attempt_count(email) == 1

    def test_increments_attempt_count(self) -> None:
        """Each attempt should increment count."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=5, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        for i in range(3):
            service.record_failed_attempt(email)
            assert service.get_attempt_count(email) == i + 1

    def test_locks_after_max_attempts(self) -> None:
        """Account should lock after max_attempts."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=3, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        for _i in range(2):
            result = service.record_failed_attempt(email)
            assert result is False

        # Third attempt should lock
        result = service.record_failed_attempt(email)
        assert result is True
        assert service.is_locked(email) is True

    def test_already_locked_returns_true(self) -> None:
        """Attempting on locked account should return True."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        service.record_failed_attempt(email)
        service.record_failed_attempt(email)  # Now locked

        # Further attempts should return True (still locked)
        result = service.record_failed_attempt(email)
        assert result is True

    def test_old_attempts_outside_window_are_cleared(self) -> None:
        """Attempts outside window should be cleared."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=3, lockout_duration_seconds=60, attempt_window_seconds=1
            )
        )
        email = "test@example.com"

        # Record an attempt
        service.record_failed_attempt(email)
        assert service.get_attempt_count(email) == 1

        # Wait for window to expire
        time.sleep(1.5)

        # Record another attempt - old one should be cleared
        service.record_failed_attempt(email)
        assert service.get_attempt_count(email) == 1  # Only the new one

    def test_separate_accounts_tracked_independently(self) -> None:
        """Different accounts should be tracked separately."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=3, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email1 = "user1@example.com"
        email2 = "user2@example.com"

        service.record_failed_attempt(email1)
        service.record_failed_attempt(email1)
        service.record_failed_attempt(email2)

        assert service.get_attempt_count(email1) == 2
        assert service.get_attempt_count(email2) == 1


class TestRecordSuccessfulLogin:
    """Tests for record_successful_login method."""

    def test_clears_failed_attempts(self) -> None:
        """Successful login should clear failed attempts."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=5, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        service.record_failed_attempt(email)
        service.record_failed_attempt(email)
        assert service.get_attempt_count(email) == 2

        service.record_successful_login(email)
        assert service.get_attempt_count(email) == 0

    def test_unknown_account_no_error(self) -> None:
        """Successful login for unknown account should not error."""
        service = AccountLockoutService()
        service.record_successful_login("unknown@example.com")  # Should not raise

    def test_removes_record_entirely(self) -> None:
        """Successful login should remove the record."""
        service = AccountLockoutService()
        email = "test@example.com"

        service.record_failed_attempt(email)
        assert email in service._records

        service.record_successful_login(email)
        assert email not in service._records


class TestClearLockout:
    """Tests for clear_lockout method (admin action)."""

    def test_clears_locked_account(self) -> None:
        """clear_lockout should unlock locked account."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=2, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        service.record_failed_attempt(email)
        service.record_failed_attempt(email)
        assert service.is_locked(email) is True

        service.clear_lockout(email)
        assert service.is_locked(email) is False
        assert service.get_attempt_count(email) == 0

    def test_unknown_account_no_error(self) -> None:
        """clear_lockout for unknown account should not error."""
        service = AccountLockoutService()
        service.clear_lockout("unknown@example.com")  # Should not raise


class TestGetAttemptCount:
    """Tests for get_attempt_count method."""

    def test_unknown_account_returns_zero(self) -> None:
        """Unknown account should return 0."""
        service = AccountLockoutService()
        assert service.get_attempt_count("unknown@example.com") == 0

    def test_returns_attempts_in_window(self) -> None:
        """Should return only attempts within window."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=10, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        for _ in range(5):
            service.record_failed_attempt(email)

        assert service.get_attempt_count(email) == 5


class TestMaskIdentifier:
    """Tests for _mask_identifier static method."""

    def test_masks_email(self) -> None:
        """Email should be masked with first 3 chars visible."""
        result = AccountLockoutService._mask_identifier("testuser@example.com")
        assert result == "tes***@example.com"

    def test_masks_short_email(self) -> None:
        """Short email local part should still be masked."""
        result = AccountLockoutService._mask_identifier("ab@example.com")
        assert result == "ab***@example.com"

    def test_masks_username(self) -> None:
        """Username should be masked with first 3 chars visible."""
        result = AccountLockoutService._mask_identifier("johndoe")
        assert result == "joh***"

    def test_masks_short_username(self) -> None:
        """Short username should be fully masked."""
        result = AccountLockoutService._mask_identifier("ab")
        assert result == "***"


class TestGlobalService:
    """Tests for global service singleton."""

    def test_get_lockout_service_returns_singleton(self) -> None:
        """get_lockout_service should return same instance."""
        reset_lockout_service()
        service1 = get_lockout_service()
        service2 = get_lockout_service()
        assert service1 is service2

    def test_reset_lockout_service_creates_new_instance(self) -> None:
        """reset_lockout_service should create new instance."""
        reset_lockout_service()
        service1 = get_lockout_service()

        reset_lockout_service()
        service2 = get_lockout_service()

        assert service1 is not service2

    def test_reset_with_config(self) -> None:
        """reset_lockout_service should accept custom config."""
        config = LockoutConfig(
            max_attempts=10, lockout_duration_seconds=120, attempt_window_seconds=60
        )
        reset_lockout_service(config)

        service = get_lockout_service()
        assert service._config.max_attempts == 10
        assert service._config.lockout_duration_seconds == 120


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_exactly_at_max_attempts(self) -> None:
        """Account should lock at exactly max_attempts."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=3, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        # 2 attempts - not locked
        service.record_failed_attempt(email)
        service.record_failed_attempt(email)
        assert service.is_locked(email) is False

        # 3rd attempt - now locked
        service.record_failed_attempt(email)
        assert service.is_locked(email) is True

    def test_max_attempts_of_one(self) -> None:
        """max_attempts=1 should lock on first failure."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=1, lockout_duration_seconds=60, attempt_window_seconds=30
            )
        )
        email = "test@example.com"

        result = service.record_failed_attempt(email)
        assert result is True
        assert service.is_locked(email) is True

    def test_very_short_window(self) -> None:
        """Very short window should expire quickly."""
        service = AccountLockoutService(
            LockoutConfig(
                max_attempts=3, lockout_duration_seconds=60, attempt_window_seconds=0
            )
        )
        email = "test@example.com"

        # With window=0, old attempts should be cleared immediately
        service.record_failed_attempt(email)
        service.record_failed_attempt(email)

        # Sleep a tiny bit to ensure time has passed
        time.sleep(0.01)

        # Next attempt should be the only one counted
        service.record_failed_attempt(email)
        # With window=0, only the most recent attempt should count
        assert service.get_attempt_count(email) <= 1

    def test_unicode_identifier(self) -> None:
        """Unicode identifiers should work."""
        service = AccountLockoutService()
        email = "用户@example.com"

        service.record_failed_attempt(email)
        assert service.get_attempt_count(email) == 1

    def test_special_characters_in_identifier(self) -> None:
        """Special characters should work."""
        service = AccountLockoutService()
        email = "test+tag@example.com"

        service.record_failed_attempt(email)
        assert service.get_attempt_count(email) == 1
