"""Unit tests for request dependency helpers."""

from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from app.api import deps


@pytest.mark.no_db
class TestRequestIdentity:
    def test_from_headers_defaults_to_configured_role(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(deps.settings, "DEFAULT_ROLE", "Admin")
        identity = deps.RequestIdentity.from_headers("", " user-123 ", " user@example.com ")
        assert identity.role == "admin"
        assert identity.user_id == "user-123"
        assert identity.email == "user@example.com"

    def test_from_headers_rejects_invalid_role(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(deps.settings, "DEFAULT_ROLE", "viewer")
        with pytest.raises(HTTPException) as exc:
            deps.RequestIdentity.from_headers("evil", None, None)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.no_db
@pytest.mark.asyncio
async def test_get_identity_returns_request_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps.settings, "DEFAULT_ROLE", "reviewer")
    identity = await deps.get_identity(x_role=None, x_user_id="42", x_user_email=None)
    assert isinstance(identity, deps.RequestIdentity)
    assert identity.role == "reviewer"
    assert identity.user_id == "42"
    assert identity.email is None


@pytest.mark.no_db
@pytest.mark.asyncio
async def test_get_request_role_delegates_to_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_identity(**_: object) -> deps.RequestIdentity:
        return deps.RequestIdentity(role="admin", user_id=None, email=None)

    monkeypatch.setattr(deps, "get_identity", fake_get_identity)
    role = await deps.get_request_role(x_role="admin")
    assert role == "admin"


@pytest.mark.no_db
@pytest.mark.asyncio
async def test_require_reviewer_allows_reviewer_role(monkeypatch: pytest.MonkeyPatch) -> None:
    identity = deps.RequestIdentity(role="reviewer", user_id=None, email=None)
    result = await deps.require_reviewer(identity=identity)
    assert result is identity


@pytest.mark.no_db
@pytest.mark.asyncio
async def test_require_reviewer_rejects_viewer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps.settings, "ALLOW_VIEWER_MUTATIONS", False)
    identity = deps.RequestIdentity(role="viewer", user_id=None, email=None)
    with pytest.raises(HTTPException) as exc:
        await deps.require_reviewer(identity=identity)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.no_db
@pytest.mark.asyncio
async def test_require_reviewer_respects_viewer_mutation_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deps.settings, "ALLOW_VIEWER_MUTATIONS", True)
    identity = deps.RequestIdentity(role="viewer", user_id=None, email=None)
    result = await deps.require_reviewer(identity=identity)
    assert result is identity
