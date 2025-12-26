"""Comprehensive tests for API dependencies (deps.py).

Tests cover:
- RequestIdentity parsing from headers
- Role validation and defaults
- require_viewer and require_reviewer dependencies
- Edge cases and error handling
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.api.deps import (
    RequestIdentity,
    get_identity,
    get_request_role,
    require_reviewer,
    require_viewer,
)


class TestRequestIdentityFromHeaders:
    """Tests for RequestIdentity.from_headers class method."""

    def test_valid_viewer_role(self) -> None:
        """Valid viewer role should be accepted."""
        identity = RequestIdentity.from_headers(
            x_role="viewer",
            x_user_id="user-123",
            x_user_email="test@example.com",
        )
        assert identity.role == "viewer"
        assert identity.user_id == "user-123"
        assert identity.email == "test@example.com"

    def test_valid_developer_role(self) -> None:
        """Valid developer role should be accepted."""
        identity = RequestIdentity.from_headers(
            x_role="developer",
            x_user_id="user-123",
            x_user_email="dev@example.com",
        )
        assert identity.role == "developer"

    def test_valid_reviewer_role(self) -> None:
        """Valid reviewer role should be accepted."""
        identity = RequestIdentity.from_headers(
            x_role="reviewer",
            x_user_id="user-123",
            x_user_email="reviewer@example.com",
        )
        assert identity.role == "reviewer"

    def test_valid_admin_role(self) -> None:
        """Valid admin role should be accepted."""
        identity = RequestIdentity.from_headers(
            x_role="admin",
            x_user_id="user-123",
            x_user_email="admin@example.com",
        )
        assert identity.role == "admin"

    def test_case_insensitive_role(self) -> None:
        """Role should be case-insensitive."""
        identity = RequestIdentity.from_headers(
            x_role="DEVELOPER",
            x_user_id=None,
            x_user_email=None,
        )
        assert identity.role == "developer"

    def test_role_with_whitespace(self) -> None:
        """Role with whitespace should be trimmed."""
        identity = RequestIdentity.from_headers(
            x_role="  viewer  ",
            x_user_id=None,
            x_user_email=None,
        )
        assert identity.role == "viewer"

    def test_invalid_role_raises_403(self) -> None:
        """Invalid role should raise 403 Forbidden."""
        with pytest.raises(HTTPException) as exc_info:
            RequestIdentity.from_headers(
                x_role="superuser",
                x_user_id=None,
                x_user_email=None,
            )
        assert exc_info.value.status_code == 403
        assert "Invalid role" in exc_info.value.detail

    def test_none_role_uses_default(self) -> None:
        """None role should use configured default."""
        identity = RequestIdentity.from_headers(
            x_role=None,
            x_user_id=None,
            x_user_email=None,
        )
        # Default role should be a valid viewer role
        assert identity.role in ["viewer", "developer", "reviewer", "admin"]

    def test_empty_role_uses_default(self) -> None:
        """Empty role should use configured default."""
        identity = RequestIdentity.from_headers(
            x_role="",
            x_user_id=None,
            x_user_email=None,
        )
        assert identity.role in ["viewer", "developer", "reviewer", "admin"]

    def test_empty_user_id_becomes_none(self) -> None:
        """Empty user_id should become None."""
        identity = RequestIdentity.from_headers(
            x_role="viewer",
            x_user_id="",
            x_user_email="test@example.com",
        )
        assert identity.user_id is None

    def test_whitespace_user_id_becomes_none(self) -> None:
        """Whitespace-only user_id should become None."""
        identity = RequestIdentity.from_headers(
            x_role="viewer",
            x_user_id="   ",
            x_user_email="test@example.com",
        )
        assert identity.user_id is None

    def test_empty_email_becomes_none(self) -> None:
        """Empty email should become None."""
        identity = RequestIdentity.from_headers(
            x_role="viewer",
            x_user_id="user-123",
            x_user_email="",
        )
        assert identity.email is None

    def test_whitespace_email_becomes_none(self) -> None:
        """Whitespace-only email should become None."""
        identity = RequestIdentity.from_headers(
            x_role="viewer",
            x_user_id="user-123",
            x_user_email="   ",
        )
        assert identity.email is None

    def test_user_id_is_stripped(self) -> None:
        """User ID should have whitespace stripped."""
        identity = RequestIdentity.from_headers(
            x_role="viewer",
            x_user_id="  user-123  ",
            x_user_email=None,
        )
        assert identity.user_id == "user-123"

    def test_email_is_stripped(self) -> None:
        """Email should have whitespace stripped."""
        identity = RequestIdentity.from_headers(
            x_role="viewer",
            x_user_id=None,
            x_user_email="  test@example.com  ",
        )
        assert identity.email == "test@example.com"


class TestGetIdentity:
    """Tests for get_identity dependency function."""

    @pytest.mark.asyncio
    async def test_get_identity_with_all_headers(self) -> None:
        """get_identity should parse all headers."""
        identity = await get_identity(
            x_role="developer",
            x_user_id="user-456",
            x_user_email="dev@test.com",
        )
        assert identity.role == "developer"
        assert identity.user_id == "user-456"
        assert identity.email == "dev@test.com"

    @pytest.mark.asyncio
    async def test_get_identity_with_no_headers(self) -> None:
        """get_identity should handle None headers."""
        identity = await get_identity(
            x_role=None,
            x_user_id=None,
            x_user_email=None,
        )
        assert identity.role in ["viewer", "developer", "reviewer", "admin"]
        assert identity.user_id is None
        assert identity.email is None

    @pytest.mark.asyncio
    async def test_get_identity_with_invalid_role(self) -> None:
        """get_identity should raise for invalid role."""
        with pytest.raises(HTTPException) as exc_info:
            await get_identity(
                x_role="invalid_role",
                x_user_id=None,
                x_user_email=None,
            )
        assert exc_info.value.status_code == 403


class TestGetRequestRole:
    """Tests for deprecated get_request_role function."""

    @pytest.mark.asyncio
    async def test_get_request_role_returns_role(self) -> None:
        """get_request_role should return just the role."""
        role = await get_request_role(x_role="developer")
        assert role == "developer"

    @pytest.mark.asyncio
    async def test_get_request_role_with_none(self) -> None:
        """get_request_role should handle None."""
        role = await get_request_role(x_role=None)
        assert role in ["viewer", "developer", "reviewer", "admin"]


class TestRequireViewer:
    """Tests for require_viewer dependency."""

    @pytest.mark.asyncio
    async def test_viewer_allowed(self) -> None:
        """Viewer role should be allowed."""
        identity = RequestIdentity(role="viewer", user_id="123", email="v@test.com")
        result = await require_viewer(identity=identity)
        assert result.role == "viewer"

    @pytest.mark.asyncio
    async def test_developer_allowed(self) -> None:
        """Developer role should be allowed."""
        identity = RequestIdentity(role="developer", user_id="123", email="d@test.com")
        result = await require_viewer(identity=identity)
        assert result.role == "developer"

    @pytest.mark.asyncio
    async def test_reviewer_allowed(self) -> None:
        """Reviewer role should be allowed."""
        identity = RequestIdentity(role="reviewer", user_id="123", email="r@test.com")
        result = await require_viewer(identity=identity)
        assert result.role == "reviewer"

    @pytest.mark.asyncio
    async def test_admin_allowed(self) -> None:
        """Admin role should be allowed."""
        identity = RequestIdentity(role="admin", user_id="123", email="a@test.com")
        result = await require_viewer(identity=identity)
        assert result.role == "admin"


class TestRequireReviewer:
    """Tests for require_reviewer dependency."""

    @pytest.mark.asyncio
    async def test_reviewer_allowed(self) -> None:
        """Reviewer role should be allowed."""
        identity = RequestIdentity(role="reviewer", user_id="123", email="r@test.com")
        result = await require_reviewer(identity=identity)
        assert result.role == "reviewer"

    @pytest.mark.asyncio
    async def test_admin_allowed(self) -> None:
        """Admin role should be allowed."""
        identity = RequestIdentity(role="admin", user_id="123", email="a@test.com")
        result = await require_reviewer(identity=identity)
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_viewer_rejected_when_mutations_not_allowed(self) -> None:
        """Viewer role should be rejected when mutations not allowed."""
        with patch("app.api.deps.settings") as mock_settings:
            mock_settings.ALLOW_VIEWER_MUTATIONS = False
            identity = RequestIdentity(role="viewer", user_id="123", email="v@test.com")
            with pytest.raises(HTTPException) as exc_info:
                await require_reviewer(identity=identity)
            assert exc_info.value.status_code == 403
            assert "Reviewer or admin role required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_developer_rejected_when_mutations_not_allowed(self) -> None:
        """Developer role should be rejected when mutations not allowed."""
        with patch("app.api.deps.settings") as mock_settings:
            mock_settings.ALLOW_VIEWER_MUTATIONS = False
            identity = RequestIdentity(
                role="developer", user_id="123", email="d@test.com"
            )
            with pytest.raises(HTTPException) as exc_info:
                await require_reviewer(identity=identity)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_allowed_when_mutations_allowed(self) -> None:
        """Viewer should be allowed when ALLOW_VIEWER_MUTATIONS is True."""
        with patch("app.api.deps.settings") as mock_settings:
            mock_settings.ALLOW_VIEWER_MUTATIONS = True
            identity = RequestIdentity(role="viewer", user_id="123", email="v@test.com")
            result = await require_reviewer(identity=identity)
            assert result.role == "viewer"


class TestRequestIdentityDataclass:
    """Tests for RequestIdentity dataclass."""

    def test_slots_optimization(self) -> None:
        """RequestIdentity should use slots for memory efficiency."""
        identity = RequestIdentity(
            role="viewer", user_id="123", email="test@example.com"
        )
        assert not hasattr(identity, "__dict__")

    def test_all_fields_accessible(self) -> None:
        """All fields should be accessible."""
        identity = RequestIdentity(
            role="admin", user_id="user-id", email="email@test.com"
        )
        assert identity.role == "admin"
        assert identity.user_id == "user-id"
        assert identity.email == "email@test.com"

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        identity = RequestIdentity(role="viewer")
        assert identity.user_id is None
        assert identity.email is None
