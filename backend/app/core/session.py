"""Session management with token blacklisting for secure logout.

Provides:
- Token blacklist for logout/revocation
- Session tracking for multi-device awareness
- Configurable session expiry

Uses Redis when available, falls back to in-memory storage for development.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Protocol

from pydantic import BaseModel

from app.core.config import settings
from app.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class SessionInfo(BaseModel):
    """Information about an active session."""

    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    expires_at: datetime


class SessionStorage(Protocol):
    """Protocol for session storage backends."""

    def blacklist_token(self, token_hash: str, expiry_seconds: int) -> None:
        """Add a token to the blacklist."""
        ...

    def is_token_blacklisted(self, token_hash: str) -> bool:
        """Check if a token is blacklisted."""
        ...

    def create_session(self, session_info: SessionInfo) -> None:
        """Store a session."""
        ...

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve a session."""
        ...

    def delete_session(self, session_id: str) -> None:
        """Remove a session."""
        ...

    def get_user_sessions(self, user_id: str) -> list[SessionInfo]:
        """Get all sessions for a user."""
        ...

    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user. Returns count of deleted sessions."""
        ...


class InMemorySessionStorage(SessionStorage):
    """In-memory session storage for development and testing."""

    def __init__(self) -> None:
        self._blacklist: dict[str, datetime] = {}
        self._sessions: dict[str, SessionInfo] = {}
        self._user_sessions: dict[str, set[str]] = {}

    def blacklist_token(self, token_hash: str, expiry_seconds: int) -> None:
        """Add a token to the blacklist with expiry."""
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)
        self._blacklist[token_hash] = expiry
        self._cleanup_expired()

    def is_token_blacklisted(self, token_hash: str) -> bool:
        """Check if a token is blacklisted and not expired."""
        self._cleanup_expired()
        if token_hash not in self._blacklist:
            return False
        return self._blacklist[token_hash] > datetime.now(timezone.utc)

    def create_session(self, session_info: SessionInfo) -> None:
        """Store a session."""
        self._sessions[session_info.session_id] = session_info
        if session_info.user_id not in self._user_sessions:
            self._user_sessions[session_info.user_id] = set()
        self._user_sessions[session_info.user_id].add(session_info.session_id)

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve a session if it exists and is not expired."""
        session = self._sessions.get(session_id)
        if session and session.expires_at < datetime.now(timezone.utc):
            self.delete_session(session_id)
            return None
        return session

    def delete_session(self, session_id: str) -> None:
        """Remove a session."""
        session = self._sessions.pop(session_id, None)
        if session and session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].discard(session_id)

    def get_user_sessions(self, user_id: str) -> list[SessionInfo]:
        """Get all active sessions for a user."""
        session_ids = self._user_sessions.get(user_id, set())
        sessions = []
        for session_id in list(session_ids):
            session = self.get_session(session_id)
            if session:
                sessions.append(session)
        return sessions

    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        session_ids = list(self._user_sessions.get(user_id, set()))
        for session_id in session_ids:
            self.delete_session(session_id)
        return len(session_ids)

    def _cleanup_expired(self) -> None:
        """Remove expired blacklist entries."""
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._blacklist.items() if v < now]
        for key in expired:
            del self._blacklist[key]


class RedisSessionStorage(SessionStorage):
    """Redis-backed session storage for production."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy initialization of Redis client."""
        if self._client is None:
            try:
                import redis

                self._client = redis.from_url(self._redis_url)
            except ImportError as e:
                raise RuntimeError("redis package not installed") from e
        return self._client

    def blacklist_token(self, token_hash: str, expiry_seconds: int) -> None:
        """Add a token to the blacklist with TTL."""
        client = self._get_client()
        client.setex(f"blacklist:{token_hash}", expiry_seconds, "1")

    def is_token_blacklisted(self, token_hash: str) -> bool:
        """Check if a token is in the blacklist."""
        client = self._get_client()
        return client.exists(f"blacklist:{token_hash}") > 0

    def create_session(self, session_info: SessionInfo) -> None:
        """Store a session in Redis."""
        client = self._get_client()
        ttl = int(
            (session_info.expires_at - datetime.now(timezone.utc)).total_seconds()
        )
        if ttl > 0:
            client.setex(
                f"session:{session_info.session_id}",
                ttl,
                session_info.model_dump_json(),
            )
            client.sadd(
                f"user_sessions:{session_info.user_id}", session_info.session_id
            )
            client.expire(f"user_sessions:{session_info.user_id}", ttl)

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve a session from Redis."""
        client = self._get_client()
        data = client.get(f"session:{session_id}")
        if data:
            return SessionInfo.model_validate_json(data)
        return None

    def delete_session(self, session_id: str) -> None:
        """Remove a session from Redis."""
        client = self._get_client()
        session = self.get_session(session_id)
        if session:
            client.srem(f"user_sessions:{session.user_id}", session_id)
        client.delete(f"session:{session_id}")

    def get_user_sessions(self, user_id: str) -> list[SessionInfo]:
        """Get all sessions for a user."""
        client = self._get_client()
        session_ids = client.smembers(f"user_sessions:{user_id}")
        sessions = []
        for session_id in session_ids:
            session = self.get_session(
                session_id.decode() if isinstance(session_id, bytes) else session_id
            )
            if session:
                sessions.append(session)
        return sessions

    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        sessions = self.get_user_sessions(user_id)
        for session in sessions:
            self.delete_session(session.session_id)
        return len(sessions)


# Singleton storage instance
_storage: Optional[SessionStorage] = None


def get_session_storage() -> SessionStorage:
    """Get the session storage singleton, creating it if necessary."""
    global _storage
    if _storage is None:
        redis_url = getattr(settings, "RATE_LIMIT_REDIS_URL", None)
        if redis_url and not redis_url.startswith("memory"):
            try:
                _storage = RedisSessionStorage(redis_url)
                log_event(logger, "session_storage_redis", url=redis_url)
            except Exception as e:
                log_event(logger, "session_storage_fallback", error=str(e))
                _storage = InMemorySessionStorage()
        else:
            _storage = InMemorySessionStorage()
            log_event(logger, "session_storage_memory")
    return _storage


def hash_token(token: str) -> str:
    """Create a hash of a token for storage.

    We don't store the full token to limit exposure if the storage is compromised.
    """
    return hashlib.sha256(token.encode()).hexdigest()


class SessionManager:
    """High-level session management operations."""

    def __init__(self, storage: Optional[SessionStorage] = None) -> None:
        self._storage = storage or get_session_storage()

    def logout(self, token: str, token_expiry_seconds: int = 30 * 60) -> None:
        """Logout by blacklisting the token.

        Args:
            token: The JWT token to invalidate
            token_expiry_seconds: How long to keep the token in blacklist (default: 30 min)
        """
        token_hash = hash_token(token)
        self._storage.blacklist_token(token_hash, token_expiry_seconds)
        log_event(logger, "user_logout", token_prefix=token[:10] + "...")

    def logout_all_devices(self, user_id: str, current_token: str) -> int:
        """Logout from all devices by invalidating all sessions.

        Args:
            user_id: The user ID to logout
            current_token: The current token to blacklist

        Returns:
            Number of sessions terminated
        """
        # Blacklist current token
        token_hash = hash_token(current_token)
        self._storage.blacklist_token(token_hash, 30 * 60)

        # Delete all sessions
        count = self._storage.delete_user_sessions(user_id)
        log_event(logger, "user_logout_all", user_id=user_id, sessions_terminated=count)
        return count

    def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked.

        Args:
            token: The JWT token to check

        Returns:
            True if the token is revoked/blacklisted
        """
        token_hash = hash_token(token)
        return self._storage.is_token_blacklisted(token_hash)

    def create_session(
        self,
        session_id: str,
        user_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_in_days: int = 7,
    ) -> SessionInfo:
        """Create a new session.

        Args:
            session_id: Unique session identifier
            user_id: User ID for the session
            user_agent: Optional browser/client user agent
            ip_address: Optional client IP address
            expires_in_days: Session validity in days (default: 7)

        Returns:
            The created session info
        """
        now = datetime.now(timezone.utc)
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_active=now,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=now + timedelta(days=expires_in_days),
        )
        self._storage.create_session(session)
        log_event(
            logger,
            "session_created",
            session_id=session_id,
            user_id=user_id,
        )
        return session

    def get_active_sessions(self, user_id: str) -> list[SessionInfo]:
        """Get all active sessions for a user.

        Args:
            user_id: The user ID to query

        Returns:
            List of active sessions
        """
        return self._storage.get_user_sessions(user_id)

    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session.

        Args:
            session_id: The session to revoke

        Returns:
            True if session was found and revoked
        """
        session = self._storage.get_session(session_id)
        if session:
            self._storage.delete_session(session_id)
            log_event(logger, "session_revoked", session_id=session_id)
            return True
        return False


# Default session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


__all__ = [
    "SessionInfo",
    "SessionStorage",
    "InMemorySessionStorage",
    "RedisSessionStorage",
    "SessionManager",
    "get_session_storage",
    "get_session_manager",
    "hash_token",
]
