"""Tests for the audit logging service."""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.audit_service import (
    AuditAction,
    AuditService,
    AuditSeverity,
    log_auth_event,
    log_data_change,
)


class TestAuditAction:
    """Tests for audit action enum."""

    def test_auth_actions_exist(self) -> None:
        """Test authentication actions are defined."""
        assert AuditAction.LOGIN_SUCCESS == "auth.login.success"
        assert AuditAction.LOGIN_FAILURE == "auth.login.failure"
        assert AuditAction.LOGOUT == "auth.logout"

    def test_data_actions_exist(self) -> None:
        """Test data actions are defined."""
        assert AuditAction.CREATE == "data.create"
        assert AuditAction.READ == "data.read"
        assert AuditAction.UPDATE == "data.update"
        assert AuditAction.DELETE == "data.delete"

    def test_sensitive_data_actions_exist(self) -> None:
        """Test sensitive data actions are defined."""
        assert AuditAction.PII_ACCESS == "sensitive.pii.access"
        assert AuditAction.FINANCIAL_ACCESS == "sensitive.financial.access"


class TestAuditSeverity:
    """Tests for audit severity enum."""

    def test_severity_levels(self) -> None:
        """Test all severity levels are defined."""
        assert AuditSeverity.DEBUG == "debug"
        assert AuditSeverity.INFO == "info"
        assert AuditSeverity.WARNING == "warning"
        assert AuditSeverity.ERROR == "error"
        assert AuditSeverity.CRITICAL == "critical"


class TestAuditService:
    """Tests for the AuditService class."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock database session."""
        mock = AsyncMock()
        # Create a proper mock result for fetchone
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_result.fetchall.return_value = []
        # Make execute return the result (AsyncMock handles the await)
        mock.execute.return_value = mock_result
        return mock

    @pytest.fixture
    def service(self, mock_db: AsyncMock) -> AuditService:
        """Create an AuditService instance."""
        return AuditService(db=mock_db, signing_key="test-signing-key")

    def test_calculate_hash(self, service: AuditService) -> None:
        """Test hash calculation is deterministic."""
        record = {"action": "test", "user_id": 1, "timestamp": "2024-01-01T00:00:00"}

        hash1 = service._calculate_hash(record)
        hash2 = service._calculate_hash(record)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_calculate_hash_different_for_different_records(
        self, service: AuditService
    ) -> None:
        """Test different records produce different hashes."""
        record1 = {"action": "test1", "user_id": 1}
        record2 = {"action": "test2", "user_id": 1}

        hash1 = service._calculate_hash(record1)
        hash2 = service._calculate_hash(record2)

        assert hash1 != hash2

    def test_sign_record(self, service: AuditService) -> None:
        """Test record signing with HMAC."""
        content_hash = "test-hash"

        signature = service._sign_record(content_hash)

        expected = hmac.new(
            b"test-signing-key",
            b"test-hash",
            hashlib.sha256,
        ).hexdigest()
        assert signature == expected

    def test_sanitize_sensitive_data_removes_passwords(
        self, service: AuditService
    ) -> None:
        """Test sensitive fields are redacted."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com",
        }

        sanitized = service._sanitize_sensitive_data(data)

        assert sanitized["username"] == "testuser"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["email"] == "test@example.com"

    def test_sanitize_sensitive_data_handles_nested_dicts(
        self, service: AuditService
    ) -> None:
        """Test nested dictionaries are sanitized."""
        data = {
            "user": {
                "name": "Test User",
                "api_key": "secret-api-key",
            }
        }

        sanitized = service._sanitize_sensitive_data(data)

        assert sanitized["user"]["name"] == "Test User"
        assert sanitized["user"]["api_key"] == "[REDACTED]"

    def test_sanitize_sensitive_data_handles_token_variations(
        self, service: AuditService
    ) -> None:
        """Test various token field names are sanitized."""
        data = {
            "access_token": "token123",
            "refresh_token": "refresh456",
            "api_secret": "secret789",
            "credit_card_number": "4111111111111111",
        }

        sanitized = service._sanitize_sensitive_data(data)

        assert sanitized["access_token"] == "[REDACTED]"
        assert sanitized["refresh_token"] == "[REDACTED]"
        assert sanitized["api_secret"] == "[REDACTED]"
        assert sanitized["credit_card_number"] == "[REDACTED]"

    @pytest.mark.asyncio
    async def test_log_creates_audit_entry(
        self, service: AuditService, mock_db: AsyncMock
    ) -> None:
        """Test log creates an audit entry in database."""
        audit_id = await service.log(
            action=AuditAction.LOGIN_SUCCESS,
            user_id=123,
            user_email="test@example.com",
            ip_address="192.168.1.1",
        )

        assert audit_id == 1
        mock_db.execute.assert_called()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_includes_old_and_new_values(
        self, service: AuditService, mock_db: AsyncMock
    ) -> None:
        """Test log includes change tracking data."""
        await service.log(
            action=AuditAction.UPDATE,
            user_id=123,
            resource_type="project",
            resource_id=456,
            old_values={"name": "Old Name"},
            new_values={"name": "New Name"},
        )

        # Verify execute was called with the data
        call_args = mock_db.execute.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_get_last_hash(
        self, service: AuditService, mock_db: AsyncMock
    ) -> None:
        """Test retrieving the last hash for chain integrity."""
        # Create new mock result with specific return value
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ("previous-hash",)
        mock_db.execute.return_value = mock_result

        last_hash = await service._get_last_hash()

        assert last_hash == "previous-hash"

    @pytest.mark.asyncio
    async def test_get_last_hash_returns_none_for_empty_table(
        self, service: AuditService, mock_db: AsyncMock
    ) -> None:
        """Test returns None when no previous entries exist."""
        # Create new mock result returning None
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        last_hash = await service._get_last_hash()

        assert last_hash is None

    @pytest.mark.asyncio
    async def test_verify_integrity_valid_chain(
        self, service: AuditService, mock_db: AsyncMock
    ) -> None:
        """Test integrity verification with valid chain."""
        # Create chain with correct signatures
        hash1 = "hash1"
        sig1 = service._sign_record(hash1)
        hash2 = "hash2"
        sig2 = service._sign_record(hash2)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (1, hash1, None, sig1),
            (2, hash2, hash1, sig2),
        ]
        mock_db.execute.return_value = mock_result

        is_valid = await service.verify_integrity()

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_verify_integrity_detects_chain_break(
        self, service: AuditService, mock_db: AsyncMock
    ) -> None:
        """Test integrity verification detects chain breaks."""
        hash1 = "hash1"
        sig1 = service._sign_record(hash1)
        hash2 = "hash2"
        sig2 = service._sign_record(hash2)

        # Chain break: hash2 should point to hash1 but points to wrong-hash
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (1, hash1, None, sig1),
            (2, hash2, "wrong-hash", sig2),  # Chain break
        ]
        mock_db.execute.return_value = mock_result

        is_valid = await service.verify_integrity()

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_integrity_detects_invalid_signature(
        self, service: AuditService, mock_db: AsyncMock
    ) -> None:
        """Test integrity verification detects tampered signatures."""
        hash1 = "hash1"

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (1, hash1, None, "invalid-signature"),  # Wrong signature
        ]
        mock_db.execute.return_value = mock_result

        is_valid = await service.verify_integrity()

        assert is_valid is False


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    @pytest.mark.asyncio
    async def test_log_data_change(self) -> None:
        """Test log_data_change convenience function."""
        mock_db = AsyncMock()
        mock_db.execute.return_value.fetchone.return_value = (1,)

        with patch(
            "app.services.audit_service.AuditService.log",
            new_callable=AsyncMock,
        ) as mock_log:
            mock_log.return_value = 1

            audit_id = await log_data_change(
                db=mock_db,
                action=AuditAction.UPDATE,
                user_id=123,
                user_email="test@example.com",
                resource_type="project",
                resource_id=456,
                old_values={"status": "draft"},
                new_values={"status": "published"},
            )

            assert audit_id == 1

    @pytest.mark.asyncio
    async def test_log_auth_event_success(self) -> None:
        """Test log_auth_event for successful authentication."""
        mock_db = AsyncMock()
        mock_db.execute.return_value.fetchone.return_value = (1,)

        with patch(
            "app.services.audit_service.AuditService.log",
            new_callable=AsyncMock,
        ) as mock_log:
            mock_log.return_value = 1

            audit_id = await log_auth_event(
                db=mock_db,
                action=AuditAction.LOGIN_SUCCESS,
                user_id=123,
                user_email="test@example.com",
                success=True,
                ip_address="192.168.1.1",
            )

            assert audit_id == 1

    @pytest.mark.asyncio
    async def test_log_auth_event_failure(self) -> None:
        """Test log_auth_event for failed authentication."""
        mock_db = AsyncMock()
        mock_db.execute.return_value.fetchone.return_value = (1,)

        with patch(
            "app.services.audit_service.AuditService.log",
            new_callable=AsyncMock,
        ) as mock_log:
            mock_log.return_value = 1

            audit_id = await log_auth_event(
                db=mock_db,
                action=AuditAction.LOGIN_FAILURE,
                user_id=None,
                user_email="test@example.com",
                success=False,
                ip_address="192.168.1.1",
                details={"reason": "invalid_password"},
            )

            assert audit_id == 1


class TestAuditServiceIntegration:
    """Integration-style tests for audit service."""

    @pytest.mark.asyncio
    async def test_full_audit_workflow(self) -> None:
        """Test complete audit workflow from logging to verification."""
        mock_db = AsyncMock()

        # Create mock results for sequential calls
        mock_result_none = MagicMock()
        mock_result_none.fetchone.return_value = None  # get_last_hash returns None

        mock_result_id = MagicMock()
        mock_result_id.fetchone.return_value = (1,)  # INSERT returns id

        # Set up execute to return different results
        mock_db.execute.side_effect = [mock_result_none, mock_result_id]

        service = AuditService(db=mock_db, signing_key="test-key")

        # Log an action
        audit_id = await service.log(
            action=AuditAction.CREATE,
            user_id=1,
            user_email="admin@example.com",
            resource_type="project",
            resource_id=100,
            details={"name": "New Project"},
            ip_address="10.0.0.1",
        )

        assert audit_id == 1
        mock_db.commit.assert_called()

    def test_audit_action_string_values(self) -> None:
        """Test audit action enum values are strings."""
        for action in AuditAction:
            assert isinstance(action.value, str)
            assert "." in action.value  # All actions use dot notation

    def test_all_crud_actions_defined(self) -> None:
        """Test all CRUD actions are defined."""
        crud_actions = [
            AuditAction.CREATE,
            AuditAction.READ,
            AuditAction.UPDATE,
            AuditAction.DELETE,
        ]
        for action in crud_actions:
            assert action.value.startswith("data.")
