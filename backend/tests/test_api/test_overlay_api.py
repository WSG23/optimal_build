from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from fastapi import HTTPException

from app.api.deps import RequestIdentity
from app.api.v1 import overlay as overlay_api
from app.main import app

UTC = timezone.utc


class _StubResult:
    def __init__(self, suggestion):
        self._suggestion = suggestion

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return [self._suggestion]

    def scalar_one_or_none(self):
        return self._suggestion


class _StubSession:
    def __init__(self, suggestion):
        self._suggestion = suggestion
        self.add_called = False

    async def execute(self, stmt):
        return _StubResult(self._suggestion)

    def add(self, obj):
        self.add_called = True
        if getattr(obj, "id", None) is None:
            obj.id = 99

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None


def _make_suggestion(include_decision: bool = False):
    decision = (
        SimpleNamespace(
            id=10,
            decision="approved",
            decided_by="user",
            decided_at=datetime.now(UTC),
            notes="ok",
        )
        if include_decision
        else None
    )
    return SimpleNamespace(
        id=1,
        project_id=1,
        source_geometry_id=999,
        code="OVR-1",
        type="constraint",
        title="Adjust setback",
        rationale="Improve daylight",
        severity="medium",
        status="pending",
        engine_version="1.0",
        engine_payload={},
        target_ids=["A"],
        props={},
        rule_refs=["RULE-1"],
        score=0.8,
        geometry_checksum="abc",
        created_at=datetime.now(UTC) - timedelta(hours=1),
        updated_at=datetime.now(UTC),
        decided_at=None,
        decided_by=None,
        decision_notes=None,
        decision=decision,
    )


@pytest.fixture(autouse=True)
def override_overlay_dependencies():
    async def _get_session():
        yield _StubSession(_make_suggestion(include_decision=True))

    app.dependency_overrides[overlay_api.get_session] = _get_session
    app.dependency_overrides[overlay_api.require_viewer] = lambda: RequestIdentity(
        role="viewer", user_id="user", email="user@example.com"
    )
    app.dependency_overrides[overlay_api.require_reviewer] = lambda: RequestIdentity(
        role="reviewer", user_id="rev", email="rev@example.com"
    )
    yield
    app.dependency_overrides.pop(overlay_api.get_session, None)
    app.dependency_overrides.pop(overlay_api.require_viewer, None)
    app.dependency_overrides.pop(overlay_api.require_reviewer, None)


@pytest.mark.asyncio
async def test_list_project_overlays_serialises_decision(client):
    suggestion = _make_suggestion(include_decision=True)

    async def _get_session():
        yield _StubSession(suggestion)

    app.dependency_overrides[overlay_api.get_session] = _get_session

    response = await client.get("/api/v1/overlay/1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["decision"]["decision"] == "approved"


def test_normalise_decision_value():
    assert overlay_api._normalise_decision_value("approve") == "approved"
    assert overlay_api._normalise_decision_value("REJECTED") == "rejected"
    with pytest.raises(HTTPException) as excinfo:
        overlay_api._normalise_decision_value("maybe")
    assert excinfo.value.status_code == 400
    assert "Decision must be approve or reject" in excinfo.value.detail


@pytest.mark.asyncio
async def test_decide_overlay_creates_decision(client, monkeypatch):
    suggestion = _make_suggestion(include_decision=False)

    async def _get_session():
        yield _StubSession(suggestion)

    app.dependency_overrides[overlay_api.get_session] = _get_session
    monkeypatch.setattr(overlay_api, "append_event", AsyncMock(return_value=None))

    response = await client.post(
        "/api/v1/overlay/1/decision",
        json={"suggestion_id": 1, "decision": "approve", "decided_by": "qa"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["item"]["status"] == "approved"
    overlay_api.append_event.assert_awaited_once()  # type: ignore[attr-defined]
