"""Tests for session management and token blacklisting.

Tests cover:
- Token blacklisting/revocation
- Session creation and retrieval
- Multi-device session management
- Session expiry
"""

from datetime import datetime, timedelta, timezone

from app.core.session import (
    InMemorySessionStorage,
    SessionInfo,
    SessionManager,
    hash_token,
)


class TestHashToken:
    """Tests for token hashing."""

    def test_hash_token_consistent(self) -> None:
        """Test that hashing the same token produces same result."""
        token = "test-token-123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_inputs(self) -> None:
        """Test that different tokens produce different hashes."""
        token1 = "token-a"
        token2 = "token-b"
        assert hash_token(token1) != hash_token(token2)

    def test_hash_token_length(self) -> None:
        """Test that hash is SHA256 length (64 hex chars)."""
        token = "any-token"
        token_hash = hash_token(token)
        assert len(token_hash) == 64  # SHA256 hex digest length


class TestInMemorySessionStorage:
    """Tests for in-memory session storage."""

    def test_blacklist_token(self) -> None:
        """Test adding token to blacklist."""
        storage = InMemorySessionStorage()
        token_hash = "test-hash-123"

        storage.blacklist_token(token_hash, 3600)

        assert storage.is_token_blacklisted(token_hash) is True

    def test_blacklist_token_not_in_list(self) -> None:
        """Test non-blacklisted token returns False."""
        storage = InMemorySessionStorage()

        assert storage.is_token_blacklisted("unknown-hash") is False

    def test_create_session(self) -> None:
        """Test creating a session."""
        storage = InMemorySessionStorage()
        session = SessionInfo(
            session_id="sess-1",
            user_id="user-1",
            created_at=datetime.now(timezone.utc),
            last_active=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        storage.create_session(session)
        retrieved = storage.get_session("sess-1")

        assert retrieved is not None
        assert retrieved.session_id == "sess-1"
        assert retrieved.user_id == "user-1"

    def test_get_nonexistent_session(self) -> None:
        """Test getting a session that doesn't exist."""
        storage = InMemorySessionStorage()

        session = storage.get_session("nonexistent")

        assert session is None

    def test_delete_session(self) -> None:
        """Test deleting a session."""
        storage = InMemorySessionStorage()
        session = SessionInfo(
            session_id="sess-1",
            user_id="user-1",
            created_at=datetime.now(timezone.utc),
            last_active=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        storage.create_session(session)

        storage.delete_session("sess-1")

        assert storage.get_session("sess-1") is None

    def test_get_user_sessions(self) -> None:
        """Test getting all sessions for a user."""
        storage = InMemorySessionStorage()

        # Create multiple sessions for same user
        for i in range(3):
            session = SessionInfo(
                session_id=f"sess-{i}",
                user_id="user-1",
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            storage.create_session(session)

        sessions = storage.get_user_sessions("user-1")

        assert len(sessions) == 3

    def test_delete_user_sessions(self) -> None:
        """Test deleting all sessions for a user."""
        storage = InMemorySessionStorage()

        # Create sessions for user
        for i in range(3):
            session = SessionInfo(
                session_id=f"sess-{i}",
                user_id="user-1",
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )
            storage.create_session(session)

        count = storage.delete_user_sessions("user-1")

        assert count == 3
        assert len(storage.get_user_sessions("user-1")) == 0

    def test_expired_session_not_returned(self) -> None:
        """Test that expired sessions are not returned."""
        storage = InMemorySessionStorage()
        session = SessionInfo(
            session_id="sess-expired",
            user_id="user-1",
            created_at=datetime.now(timezone.utc) - timedelta(days=8),
            last_active=datetime.now(timezone.utc) - timedelta(days=8),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        )
        storage.create_session(session)

        retrieved = storage.get_session("sess-expired")

        assert retrieved is None


class TestSessionManager:
    """Tests for SessionManager."""

    def test_logout_blacklists_token(self) -> None:
        """Test that logout adds token to blacklist."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)
        token = "access-token-123"

        manager.logout(token)

        token_hash = hash_token(token)
        assert storage.is_token_blacklisted(token_hash) is True

    def test_is_token_revoked_after_logout(self) -> None:
        """Test that token is revoked after logout."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)
        token = "access-token-456"

        manager.logout(token)

        assert manager.is_token_revoked(token) is True

    def test_is_token_revoked_not_logged_out(self) -> None:
        """Test that active token is not revoked."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)
        token = "active-token-789"

        assert manager.is_token_revoked(token) is False

    def test_create_session(self) -> None:
        """Test creating a session through manager."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)

        session = manager.create_session(
            session_id="sess-abc",
            user_id="user-123",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
        )

        assert session.session_id == "sess-abc"
        assert session.user_id == "user-123"
        assert session.user_agent == "Mozilla/5.0"
        assert session.ip_address == "192.168.1.1"

    def test_get_active_sessions(self) -> None:
        """Test getting active sessions for user."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)

        manager.create_session(session_id="s1", user_id="u1")
        manager.create_session(session_id="s2", user_id="u1")
        manager.create_session(session_id="s3", user_id="u2")

        sessions = manager.get_active_sessions("u1")

        assert len(sessions) == 2

    def test_revoke_session(self) -> None:
        """Test revoking a specific session."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)

        manager.create_session(session_id="to-revoke", user_id="u1")

        result = manager.revoke_session("to-revoke")

        assert result is True
        assert storage.get_session("to-revoke") is None

    def test_revoke_nonexistent_session(self) -> None:
        """Test revoking session that doesn't exist."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)

        result = manager.revoke_session("nonexistent")

        assert result is False

    def test_logout_all_devices(self) -> None:
        """Test logging out from all devices."""
        storage = InMemorySessionStorage()
        manager = SessionManager(storage)

        # Create multiple sessions
        manager.create_session(session_id="s1", user_id="u1")
        manager.create_session(session_id="s2", user_id="u1")
        manager.create_session(session_id="s3", user_id="u1")

        token = "current-access-token"
        count = manager.logout_all_devices("u1", token)

        assert count == 3
        assert manager.is_token_revoked(token) is True
        assert len(manager.get_active_sessions("u1")) == 0


class TestSessionInfo:
    """Tests for SessionInfo model."""

    def test_session_info_creation(self) -> None:
        """Test creating a SessionInfo object."""
        now = datetime.now(timezone.utc)
        session = SessionInfo(
            session_id="test-session",
            user_id="test-user",
            created_at=now,
            last_active=now,
            expires_at=now + timedelta(days=7),
            user_agent="Test Agent",
            ip_address="127.0.0.1",
        )

        assert session.session_id == "test-session"
        assert session.user_id == "test-user"
        assert session.user_agent == "Test Agent"
        assert session.ip_address == "127.0.0.1"

    def test_session_info_optional_fields(self) -> None:
        """Test SessionInfo with optional fields."""
        now = datetime.now(timezone.utc)
        session = SessionInfo(
            session_id="minimal-session",
            user_id="minimal-user",
            created_at=now,
            last_active=now,
            expires_at=now + timedelta(days=7),
        )

        assert session.user_agent is None
        assert session.ip_address is None

    def test_session_info_serialization(self) -> None:
        """Test SessionInfo JSON serialization."""
        now = datetime.now(timezone.utc)
        session = SessionInfo(
            session_id="serialize-test",
            user_id="serialize-user",
            created_at=now,
            last_active=now,
            expires_at=now + timedelta(days=7),
        )

        json_str = session.model_dump_json()
        restored = SessionInfo.model_validate_json(json_str)

        assert restored.session_id == session.session_id
        assert restored.user_id == session.user_id
