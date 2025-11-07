from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import entitlements as ent_service


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None

    def __iter__(self):
        return iter(self._items)


class _SessionStub:
    def __init__(self, results):
        self._results = list(results)
        self.deleted = []
        self.added = []

    async def execute(self, _stmt):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

    async def delete(self, obj):
        self.deleted.append(obj)


def _roadmap_item(item_id: int, sequence_order: int = 1):
    return SimpleNamespace(
        id=item_id,
        sequence_order=sequence_order,
        project_id=1,
        status="planned",
        status_changed_at=None,
        approval_type_id=None,
        target_submission_date=None,
        target_decision_date=None,
        actual_submission_date=None,
        actual_decision_date=None,
        notes=None,
        metadata={},
    )


@pytest.mark.asyncio
async def test_reindex_and_roadmap_updates():
    existing = [_roadmap_item(1, 1), _roadmap_item(2, 2)]
    session = _SessionStub([_ScalarsResult(existing), _ScalarsResult(existing)])
    service = ent_service.EntitlementsService(session)

    created = await service.create_roadmap_item(
        project_id=1,
        approval_type_id=None,
        sequence_order=1,
        status="planned",
        status_changed_at=None,
        target_submission_date=None,
        target_decision_date=None,
        actual_submission_date=None,
        actual_decision_date=None,
        notes="new",
        metadata=None,
    )
    assert created.sequence_order == 1
    assert session.added

    session = _SessionStub([_ScalarsResult(existing), _ScalarsResult(existing)])
    service = ent_service.EntitlementsService(session)
    updated = await service.update_roadmap_item(
        item_id=1,
        project_id=1,
        sequence_order=2,
        status="submitted",
    )
    assert updated.status == "submitted"
    assert updated.sequence_order == 2

    session = _SessionStub([_ScalarsResult(existing)])
    service = ent_service.EntitlementsService(session)
    await service.delete_roadmap_item(item_id=1, project_id=1)
    assert session.deleted


@pytest.mark.asyncio
async def test_studies_engagements_and_legal_instruments():
    study = SimpleNamespace(id=5, project_id=2, created_at=datetime.now(timezone.utc))
    session = _SessionStub([_ScalarsResult([study]), _ScalarsResult([study])])
    service = ent_service.EntitlementsService(session)

    page = await service.list_studies(project_id=2, limit=10, offset=0)
    assert page.total == 1

    created = await service.create_study(project_id=2, name="Traffic")
    assert session.added[-1] is created

    session = _SessionStub([_ScalarsResult([study])])
    service = ent_service.EntitlementsService(session)
    updated = await service.update_study(study_id=5, project_id=2, summary="done")
    assert updated.summary == "done"

    session = _SessionStub([_ScalarsResult([study])])
    service = ent_service.EntitlementsService(session)
    await service.delete_study(study_id=5, project_id=2)
    assert session.deleted

    engagement = SimpleNamespace(
        id=7, project_id=3, created_at=datetime.now(timezone.utc)
    )
    session = _SessionStub([_ScalarsResult([engagement])])
    service = ent_service.EntitlementsService(session)
    engagements_page = await service.list_engagements(project_id=3)
    assert engagements_page.total == 1

    session = _SessionStub([])
    service = ent_service.EntitlementsService(session)
    new_engagement = await service.create_engagement(project_id=3, name="URA")
    assert new_engagement.name == "URA"

    session = _SessionStub([_ScalarsResult([engagement])])
    service = ent_service.EntitlementsService(session)
    updated_engagement = await service.update_engagement(
        engagement_id=7, project_id=3, status="active"
    )
    assert updated_engagement.status == "active"

    session = _SessionStub([_ScalarsResult([engagement])])
    service = ent_service.EntitlementsService(session)
    await service.delete_engagement(engagement_id=7, project_id=3)
    assert session.deleted

    legal = SimpleNamespace(id=9, project_id=4, created_at=datetime.now(timezone.utc))
    session = _SessionStub([_ScalarsResult([legal])])
    service = ent_service.EntitlementsService(session)
    legal_page = await service.list_legal_instruments(project_id=4)
    assert legal_page.total == 1

    session = _SessionStub([])
    service = ent_service.EntitlementsService(session)
    created_legal = await service.create_legal_instrument(project_id=4, name="Lease")
    assert created_legal.name == "Lease"

    session = _SessionStub([_ScalarsResult([legal])])
    service = ent_service.EntitlementsService(session)
    updated_legal = await service.update_legal_instrument(
        instrument_id=9, project_id=4, status="executed"
    )
    assert updated_legal.status == "executed"

    session = _SessionStub([_ScalarsResult([legal])])
    service = ent_service.EntitlementsService(session)
    await service.delete_legal_instrument(instrument_id=9, project_id=4)
    assert session.deleted
