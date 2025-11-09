from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.agents.advisory import AgentAdvisoryService


@pytest.mark.asyncio
async def test_build_summary_handles_conservation(monkeypatch):
    service = AgentAdvisoryService()
    property_id = uuid4()
    property_record = SimpleNamespace(
        id=property_id,
        property_type="historic_mixed",
        gross_floor_area_sqm=None,
        land_area_sqm=2500,
        plot_ratio=3.2,
        is_conservation=True,
        district="D11",
        units_total=40,
    )

    monkeypatch.setattr(
        service, "_get_property", AsyncMock(return_value=property_record)
    )
    monkeypatch.setattr(
        service,
        "_list_feedback",
        AsyncMock(return_value=[{"id": str(uuid4()), "notes": "Great potential"}]),
    )

    summary = await service.build_summary(property_id=property_id, session=None)
    payload = summary.to_dict()

    assert payload["asset_mix"]["notes"]  # conservation note added
    assert payload["market_positioning"]["market_tier"] == "Core Central Region"
    assert payload["absorption_forecast"]["monthly_velocity_target"] == 4
    assert payload["feedback"][0]["notes"] == "Great potential"


class _StubResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _StubSession:
    def __init__(self, property_exists=True):
        self.property_exists = property_exists
        self.added = []
        self.committed = False
        self.refreshed = []

    async def execute(self, stmt):
        return _StubResult(uuid4() if self.property_exists else None)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        obj.created_at = datetime(2025, 1, 1, 12, 0, 0)
        self.refreshed.append(obj)


@pytest.mark.asyncio
async def test_record_feedback_persists(monkeypatch):
    service = AgentAdvisoryService()
    session = _StubSession(property_exists=True)
    property_id = uuid4()

    feedback = await service.record_feedback(
        property_id=property_id,
        session=session,
        submitted_by="agent@example.com",
        sentiment="positive",
        notes="Strong investor demand",
        metadata={"channel": "call"},
    )

    assert session.added
    assert session.committed
    assert feedback["sentiment"] == "positive"
    assert "created_at" in feedback


@pytest.mark.asyncio
async def test_record_feedback_raises_when_property_missing():
    service = AgentAdvisoryService()
    session = _StubSession(property_exists=False)

    with pytest.raises(ValueError):
        await service.record_feedback(
            property_id=uuid4(),
            session=session,
            submitted_by=None,
            sentiment="neutral",
            notes="No property located",
        )
