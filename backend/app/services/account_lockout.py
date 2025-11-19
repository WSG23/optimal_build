"""Account lockout service to prevent brute force attacks.

Tracks failed login attempts and temporarily locks accounts after
exceeding the configured threshold.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)


@dataclass
class LockoutConfig:
    """Configuration for account lockout behavior."""

    max_attempts: int = 5
    lockout_duration_seconds: int = 900  # 15 minutes
    attempt_window_seconds: int = 300  # 5 minutes - window to count attempts


@dataclass
class AttemptRecord:
    """Record of login attempts for an account."""

    attempts: list[float] = field(default_factory=list)
    locked_until: Optional[float] = None


class AccountLockoutService:
    """Service to track and enforce account lockout policies.

    Uses in-memory storage by default. For production with multiple
    instances, consider using Redis-backed implementation.
    """

    def __init__(self, config: Optional[LockoutConfig] = None) -> None:
        self._config = config or LockoutConfig()
        self._records: dict[str, AttemptRecord] = defaultdict(AttemptRecord)

    def is_locked(self, identifier: str) -> bool:
        """Check if an account is currently locked.

        Args:
            identifier: Email or username to check

        Returns:
            True if account is locked, False otherwise
        """
        record = self._records.get(identifier)
        if not record or not record.locked_until:
            return False

        current_time = time.time()
        if current_time >= record.locked_until:
            # Lockout expired, clear it
            record.locked_until = None
            record.attempts = []
            log_event(
                logger,
                "account_lockout_expired",
                identifier=self._mask_identifier(identifier),
            )
            return False

        return True

    def get_lockout_remaining_seconds(self, identifier: str) -> int:
        """Get remaining lockout time in seconds.

        Args:
            identifier: Email or username to check

        Returns:
            Seconds remaining in lockout, or 0 if not locked
        """
        record = self._records.get(identifier)
        if not record or not record.locked_until:
            return 0

        remaining = record.locked_until - time.time()
        return max(0, int(remaining))

    def record_failed_attempt(self, identifier: str) -> bool:
        """Record a failed login attempt.

        Args:
            identifier: Email or username that failed login

        Returns:
            True if account is now locked, False otherwise
        """
        current_time = time.time()
        record = self._records[identifier]

        # If already locked, don't add more attempts
        if record.locked_until and current_time < record.locked_until:
            return True

        # Clean old attempts outside the window
        window_start = current_time - self._config.attempt_window_seconds
        record.attempts = [t for t in record.attempts if t > window_start]

        # Add this attempt
        record.attempts.append(current_time)

        # Check if we should lock
        if len(record.attempts) >= self._config.max_attempts:
            record.locked_until = current_time + self._config.lockout_duration_seconds
            log_event(
                logger,
                "account_locked",
                identifier=self._mask_identifier(identifier),
                attempt_count=len(record.attempts),
                lockout_duration=self._config.lockout_duration_seconds,
            )
            return True

        log_event(
            logger,
            "failed_login_attempt",
            identifier=self._mask_identifier(identifier),
            attempt_count=len(record.attempts),
            max_attempts=self._config.max_attempts,
        )
        return False

    def record_successful_login(self, identifier: str) -> None:
        """Clear failed attempts after successful login.

        Args:
            identifier: Email or username that logged in successfully
        """
        if identifier in self._records:
            del self._records[identifier]
            log_event(
                logger,
                "login_attempts_cleared",
                identifier=self._mask_identifier(identifier),
            )

    def clear_lockout(self, identifier: str) -> None:
        """Manually clear a lockout (admin action).

        Args:
            identifier: Email or username to unlock
        """
        if identifier in self._records:
            del self._records[identifier]
            log_event(
                logger,
                "lockout_manually_cleared",
                identifier=self._mask_identifier(identifier),
            )

    def get_attempt_count(self, identifier: str) -> int:
        """Get current number of failed attempts in window.

        Args:
            identifier: Email or username to check

        Returns:
            Number of failed attempts in current window
        """
        record = self._records.get(identifier)
        if not record:
            return 0

        current_time = time.time()
        window_start = current_time - self._config.attempt_window_seconds
        return len([t for t in record.attempts if t > window_start])

    @staticmethod
    def _mask_identifier(identifier: str) -> str:
        """Mask identifier for logging (privacy protection).

        Args:
            identifier: Email or username to mask

        Returns:
            Masked identifier showing only first 3 chars
        """
        if "@" in identifier:
            local, domain = identifier.split("@", 1)
            if len(local) > 3:
                return f"{local[:3]}***@{domain}"
            return f"{local}***@{domain}"
        if len(identifier) > 3:
            return f"{identifier[:3]}***"
        return "***"


# Global instance for use across the application
_lockout_service: Optional[AccountLockoutService] = None


def get_lockout_service() -> AccountLockoutService:
    """Get the global account lockout service instance.

    Returns:
        The singleton AccountLockoutService
    """
    global _lockout_service
    if _lockout_service is None:
        _lockout_service = AccountLockoutService()
    return _lockout_service


def reset_lockout_service(config: Optional[LockoutConfig] = None) -> None:
    """Reset the global lockout service (useful for testing).

    Args:
        config: Optional new configuration to use
    """
    global _lockout_service
    _lockout_service = AccountLockoutService(config)


__all__ = [
    "AccountLockoutService",
    "LockoutConfig",
    "get_lockout_service",
    "reset_lockout_service",
]
