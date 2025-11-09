from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.api.v1 import entitlements as ent_api
from app.core.export.entitlements import EntitlementsExportFormat
from app.main import app
from app.schemas.entitlements import (
    EntEngagementCreate,
    EntEngagementStatus,
    EntEngagementType,
    EntLegalInstrumentCreate,
    EntLegalInstrumentStatus,
    EntLegalInstrumentType,
    EntLegalInstrumentUpdate,
    EntRoadmapItemCreate,
    EntRoadmapStatus,
    EntStudyCreate,
    EntStudyStatus,
    EntStudyType,
)

UTC_NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)
ROADMAP_RECORD = {
    "id": 10,
    "project_id": 42,
    "approval_type_id": None,
    "sequence_order": 1,
    "status": EntRoadmapStatus.PLANNED,
    "status_changed_at": None,
    "target_submission_date": date(2024, 6, 1),
    "target_decision_date": None,
    "actual_submission_date": None,
    "actual_decision_date": None,
    "notes": "Kick-off",
    "metadata": {},
    "created_at": UTC_NOW,
    "updated_at": UTC_NOW,
}


def _study_record(**overrides) -> SimpleNamespace:
    base = {
        "id": 1,
        "project_id": 42,
        "name": "Traffic Study",
        "study_type": EntStudyType.TRAFFIC,
        "status": EntStudyStatus.DRAFT,
        "summary": None,
        "consultant": None,
        "due_date": None,
        "completed_at": None,
        "attachments": [],
        "metadata": {},
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }
    overrides = dict(overrides)
    if "study_id" in overrides:
        overrides["id"] = overrides.pop("study_id")
    base.update(overrides)
    return SimpleNamespace(**base)


def _engagement_record(**overrides) -> SimpleNamespace:
    base = {
        "id": 1,
        "project_id": 42,
        "name": "URA",
        "organisation": "URA",
        "engagement_type": EntEngagementType.AGENCY,
        "status": EntEngagementStatus.PLANNED,
        "contact_email": None,
        "contact_phone": None,
        "meetings": [],
        "notes": None,
        "metadata": {},
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }
    overrides = dict(overrides)
    if "engagement_id" in overrides:
        overrides["id"] = overrides.pop("engagement_id")
    base.update(overrides)
    return SimpleNamespace(**base)


def _legal_record(**overrides) -> SimpleNamespace:
    base = {
        "id": 3,
        "project_id": 42,
        "name": "Lease",
        "instrument_type": EntLegalInstrumentType.AGREEMENT,
        "status": EntLegalInstrumentStatus.DRAFT,
        "notes": None,
        "metadata": {},
        "created_at": UTC_NOW,
        "updated_at": UTC_NOW,
    }
    overrides = dict(overrides)
    if "instrument_id" in overrides:
        overrides["id"] = overrides.pop("instrument_id")
    base.update(overrides)
    return SimpleNamespace(**base)


class _StubPage:
    def __init__(self, items):
        self.items = items
        self.total = len(items)


class _StubService:
    def __init__(self, session):
        self.session = session
        self.deleted: list[tuple[int, int]] = []

    async def list_roadmap_items(self, **kwargs):
        self.last_list_kwargs = kwargs
        return _StubPage([ROADMAP_RECORD])

    async def delete_roadmap_item(self, item_id: int, project_id: int):
        self.deleted.append((item_id, project_id))


class _SessionStub:
    def __init__(self):
        self.committed = False
        self.refreshed = []

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)


@pytest.fixture(autouse=True)
def override_entitlements_auth():
    app.dependency_overrides[ent_api.require_viewer] = lambda: "viewer"
    app.dependency_overrides[ent_api.require_reviewer] = lambda: "reviewer"
    yield
    app.dependency_overrides.pop(ent_api.require_viewer, None)
    app.dependency_overrides.pop(ent_api.require_reviewer, None)


def test_normalise_pagination_caps_values():
    assert ent_api._normalise_pagination(500, -10) == (200, 0)
    assert ent_api._normalise_pagination(5, 3) == (5, 3)


@pytest.mark.asyncio
async def test_entitlements_root_placeholder_returns_400(client):
    response = await client.get("/api/v1/entitlements")
    assert response.status_code == 400
    assert "project-scoped" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_roadmap_items_returns_paginated_payload(client, monkeypatch):
    stub = _StubService(session=None)
    monkeypatch.setattr(ent_api, "EntitlementsService", lambda session: stub)

    response = await client.get("/api/v1/entitlements/42/roadmap?limit=150&offset=5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 150
    assert payload["offset"] == 5
    assert payload["items"][0]["id"] == 10
    assert stub.last_list_kwargs["project_id"] == 42


@pytest.mark.asyncio
async def test_create_roadmap_item_rejects_project_mismatch(client):
    body = EntRoadmapItemCreate(
        project_id=99, sequence_order=1, status=EntRoadmapStatus.PLANNED
    )
    response = await client.post(
        "/api/v1/entitlements/42/roadmap",
        json=body.model_dump(mode="json"),
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_roadmap_item_invokes_service(client, monkeypatch):
    stub = _StubService(session=None)
    monkeypatch.setattr(ent_api, "EntitlementsService", lambda session: stub)

    response = await client.delete("/api/v1/entitlements/42/roadmap/5")
    assert response.status_code == 204
    assert stub.deleted == [(5, 42)]


@pytest.mark.asyncio
async def test_export_entitlements_streams_payload(client, monkeypatch):
    async def _fake_export(session, project_id: int, fmt: EntitlementsExportFormat):
        return b"csv,data", "text/csv", "entitlements.csv"

    monkeypatch.setattr(
        ent_api, "generate_entitlements_export", _fake_export, raising=False
    )
    response = await client.get(
        "/api/v1/entitlements/42/export?format=csv",
        headers={"accept": "text/csv"},
    )
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=entitlements.csv"
    )
    assert response.content == b"csv,data"


@pytest.mark.asyncio
async def test_list_studies_returns_collection(monkeypatch):
    class _StudyService:
        async def list_studies(self, **kwargs):
            return _StubPage([_study_record()])

    monkeypatch.setattr(ent_api, "EntitlementsService", lambda session: _StudyService())

    response = await ent_api.list_studies(
        project_id=42,
        limit=75,
        offset=5,
        session=_SessionStub(),
        _="viewer",
    )
    assert response.limit == 75
    assert response.items[0].name == "Traffic Study"


@pytest.mark.asyncio
async def test_create_and_update_study_paths(monkeypatch):
    session = _SessionStub()

    class _StudyService:
        async def create_study(self, **kwargs):
            return _study_record(**kwargs)

        async def update_study(self, **kwargs):
            return _study_record(**kwargs)

    monkeypatch.setattr(ent_api, "EntitlementsService", lambda session: _StudyService())

    payload = EntStudyCreate(
        project_id=42,
        name="ESG",
        study_type=EntStudyType.ENVIRONMENTAL,
    )
    created = await ent_api.create_study(
        project_id=42,
        payload=payload,
        session=session,
        _="reviewer",
    )
    assert created.name == "ESG"
    assert session.committed

    updated = await ent_api.update_study(
        project_id=42,
        study_id=7,
        payload=SimpleNamespace(
            model_dump=lambda exclude_unset=True: {"summary": "done"}
        ),
        session=session,
        _="reviewer",
    )
    assert updated.summary == "done"


@pytest.mark.asyncio
async def test_delete_study_invokes_service(monkeypatch):
    called = {}

    class _StudyService:
        async def delete_study(self, **kwargs):
            called["args"] = kwargs

    monkeypatch.setattr(ent_api, "EntitlementsService", lambda session: _StudyService())
    session = _SessionStub()
    await ent_api.delete_study(
        project_id=42,
        study_id=9,
        session=session,
        _="reviewer",
    )
    assert called["args"]["study_id"] == 9
    assert session.committed


@pytest.mark.asyncio
async def test_list_engagements_and_create(monkeypatch):
    class _EngagementService:
        async def list_engagements(self, **kwargs):
            return _StubPage([_engagement_record()])

        async def create_engagement(self, **kwargs):
            return _engagement_record(**kwargs)

    monkeypatch.setattr(
        ent_api, "EntitlementsService", lambda session: _EngagementService()
    )
    session = _SessionStub()
    response = await ent_api.list_engagements(
        project_id=42,
        limit=10,
        offset=0,
        session=session,
        _="viewer",
    )
    assert response.items[0].name == "URA"

    payload = EntEngagementCreate(
        project_id=42,
        name="LTA",
        engagement_type=EntEngagementType.AGENCY,
        status=EntEngagementStatus.PLANNED,
    )
    new_engagement = await ent_api.create_engagement(
        project_id=42,
        payload=payload,
        session=session,
        _="reviewer",
    )
    assert new_engagement.name == "LTA"


@pytest.mark.asyncio
async def test_update_and_delete_engagement(monkeypatch):
    class _EngagementService:
        async def update_engagement(self, **kwargs):
            return _engagement_record(**kwargs)

        async def delete_engagement(self, **kwargs):
            pass

    monkeypatch.setattr(
        ent_api, "EntitlementsService", lambda session: _EngagementService()
    )
    session = _SessionStub()
    updated = await ent_api.update_engagement(
        project_id=42,
        engagement_id=5,
        payload=SimpleNamespace(
            model_dump=lambda exclude_unset=True: {"notes": "sync"}
        ),
        session=session,
        _="reviewer",
    )
    assert updated.id == 5
    await ent_api.delete_engagement(
        project_id=42,
        engagement_id=5,
        session=session,
        _="reviewer",
    )
    assert session.committed


@pytest.mark.asyncio
async def test_legal_instrument_crud(monkeypatch):
    class _LegalService:
        async def list_legal_instruments(self, **kwargs):
            return _StubPage([_legal_record()])

        async def create_legal_instrument(self, **kwargs):
            return _legal_record(**kwargs)

        async def update_legal_instrument(self, **kwargs):
            return _legal_record(**kwargs)

        async def delete_legal_instrument(self, **kwargs):
            pass

    monkeypatch.setattr(ent_api, "EntitlementsService", lambda session: _LegalService())
    session = _SessionStub()
    collection = await ent_api.list_legal_instruments(
        project_id=42,
        limit=5,
        offset=0,
        session=session,
        _="viewer",
    )
    assert collection.items[0].name == "Lease"

    payload = EntLegalInstrumentCreate(
        project_id=42,
        name="Lease",
        instrument_type=EntLegalInstrumentType.AGREEMENT,
    )
    created = await ent_api.create_legal_instrument(
        project_id=42,
        payload=payload,
        session=session,
        _="reviewer",
    )
    assert created.name == "Lease"

    updated = await ent_api.update_legal_instrument(
        project_id=42,
        instrument_id=3,
        payload=EntLegalInstrumentUpdate(notes="updated"),
        session=session,
        _="reviewer",
    )
    assert updated.id == 3

    await ent_api.delete_legal_instrument(
        project_id=42,
        instrument_id=3,
        session=session,
        _="reviewer",
    )
    assert session.committed
