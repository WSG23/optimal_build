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


@pytest.mark.asyncio
async def test_decide_overlay_updates_existing_decision(client, monkeypatch):
    """Test that existing decision gets updated instead of creating new one."""
    suggestion = _make_suggestion(include_decision=True)

    async def _get_session():
        yield _StubSession(suggestion)

    app.dependency_overrides[overlay_api.get_session] = _get_session
    monkeypatch.setattr(overlay_api, "append_event", AsyncMock(return_value=None))

    response = await client.post(
        "/api/v1/overlay/1/decision",
        json={
            "suggestion_id": 1,
            "decision": "reject",
            "decided_by": "reviewer",
            "notes": "Updated note",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["item"]["status"] == "rejected"


@pytest.mark.asyncio
async def test_decide_overlay_not_found(client, monkeypatch):
    """Test 404 when suggestion not found."""

    class _EmptyResult:
        def scalars(self):
            return self

        def unique(self):
            return self

        def all(self):
            return []

        def scalar_one_or_none(self):
            return None

    class _EmptySession:
        async def execute(self, stmt):
            return _EmptyResult()

        def add(self, obj):
            pass

        async def commit(self):
            pass

        async def refresh(self, obj):
            pass

    async def _get_session():
        yield _EmptySession()

    app.dependency_overrides[overlay_api.get_session] = _get_session
    monkeypatch.setattr(overlay_api, "append_event", AsyncMock(return_value=None))

    response = await client.post(
        "/api/v1/overlay/1/decision",
        json={"suggestion_id": 999, "decision": "approve", "decided_by": "qa"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_decide_overlay_wrong_project(client, monkeypatch):
    """Test 404 when suggestion belongs to different project."""
    suggestion = _make_suggestion(include_decision=False)
    suggestion.project_id = 999  # Different from request project_id

    async def _get_session():
        yield _StubSession(suggestion)

    app.dependency_overrides[overlay_api.get_session] = _get_session

    response = await client.post(
        "/api/v1/overlay/1/decision",
        json={"suggestion_id": 1, "decision": "approve", "decided_by": "qa"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_run_overlay_with_job_result(client, monkeypatch):
    """Test run_overlay returns job dispatch result when available."""
    from types import SimpleNamespace

    mock_dispatch = SimpleNamespace(
        result={"status": "completed", "project_id": "1", "created": 5},
        task_id="job-123",
    )
    monkeypatch.setattr(
        overlay_api.job_queue,
        "enqueue",
        AsyncMock(return_value=mock_dispatch),
    )

    response = await client.post("/api/v1/overlay/1/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["project_id"] == 1  # Converted to int


@pytest.mark.asyncio
async def test_run_overlay_fallback_no_result(client, monkeypatch):
    """Test run_overlay falls back to direct execution when no job result."""
    from types import SimpleNamespace

    mock_dispatch = SimpleNamespace(result=None, task_id="job-456")
    monkeypatch.setattr(
        overlay_api.job_queue,
        "enqueue",
        AsyncMock(return_value=mock_dispatch),
    )

    # Mock the fallback function
    mock_fallback_result = SimpleNamespace(
        status="completed",
        evaluated=1,
        created=0,
        updated=0,
    )
    mock_fallback_result.as_dict = lambda: {"evaluated": 1, "created": 0, "updated": 0}

    monkeypatch.setattr(
        overlay_api,
        "run_overlay_for_project",
        AsyncMock(return_value=mock_fallback_result),
    )

    response = await client.post("/api/v1/overlay/1/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["job_id"] == "job-456"


@pytest.mark.asyncio
async def test_list_project_overlays_empty(client):
    """Test listing overlays when none exist."""

    class _EmptyResult:
        def scalars(self):
            return self

        def unique(self):
            return self

        def all(self):
            return []

    class _EmptySession:
        async def execute(self, stmt):
            return _EmptyResult()

    async def _get_session():
        yield _EmptySession()

    app.dependency_overrides[overlay_api.get_session] = _get_session

    response = await client.get("/api/v1/overlay/1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0
    assert payload["items"] == []


def test_as_utc_with_none():
    """Test _as_utc returns None for None input."""
    result = overlay_api._as_utc(None)
    assert result is None


def test_as_utc_with_naive_datetime():
    """Test _as_utc adds UTC to naive datetime."""
    naive = datetime(2024, 1, 1, 12, 0, 0)
    result = overlay_api._as_utc(naive)
    assert result is not None
    assert result.tzinfo == UTC
    assert result.year == 2024


def test_as_utc_with_utc_datetime():
    """Test _as_utc preserves UTC datetime."""
    utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    result = overlay_api._as_utc(utc_dt)
    assert result == utc_dt


def test_as_utc_with_different_timezone():
    """Test _as_utc converts other timezones to UTC."""
    # Create a datetime in a different timezone (UTC+8)
    other_tz = timezone(timedelta(hours=8))
    dt = datetime(2024, 1, 1, 20, 0, 0, tzinfo=other_tz)
    result = overlay_api._as_utc(dt)
    assert result is not None
    assert result.tzinfo == UTC
    # 20:00 UTC+8 = 12:00 UTC
    assert result.hour == 12


def test_serialise_suggestion_without_decision():
    """Test _serialise_suggestion when decision is None."""
    from app.schemas.overlay import OverlaySuggestion as OverlaySuggestionSchema

    suggestion = _make_suggestion(include_decision=False)
    schema = OverlaySuggestionSchema.model_validate(suggestion, from_attributes=True)
    result = overlay_api._serialise_suggestion(schema)
    assert isinstance(result, dict)
    assert result["decision"] is None


def test_serialise_suggestion_with_dict_decision():
    """Test _serialise_suggestion when decision is already a dict."""
    from app.schemas.overlay import OverlaySuggestion as OverlaySuggestionSchema

    suggestion = _make_suggestion(include_decision=True)
    schema = OverlaySuggestionSchema.model_validate(suggestion, from_attributes=True)
    result = overlay_api._serialise_suggestion(schema)
    assert isinstance(result, dict)
    # Decision should be serialized properly
    assert "decision" in result


def test_normalise_decision_approved_variations():
    """Test _normalise_decision_value handles approved variations."""
    assert overlay_api._normalise_decision_value("approve") == "approved"
    assert overlay_api._normalise_decision_value("APPROVE") == "approved"
    assert overlay_api._normalise_decision_value("  approved  ") == "approved"
    assert overlay_api._normalise_decision_value("Approved") == "approved"


def test_normalise_decision_rejected_variations():
    """Test _normalise_decision_value handles rejected variations."""
    assert overlay_api._normalise_decision_value("reject") == "rejected"
    assert overlay_api._normalise_decision_value("REJECT") == "rejected"
    assert overlay_api._normalise_decision_value("  rejected  ") == "rejected"
    assert overlay_api._normalise_decision_value("Rejected") == "rejected"
