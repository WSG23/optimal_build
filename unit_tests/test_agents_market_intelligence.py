from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.models.property import PropertyType

from backend.app.api.v1 import agents
from backend.app.api.v1.agents import get_property_market_intelligence
from fastapi import HTTPException


class StubResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class StubSession:
    def __init__(self, value):
        self._value = value

    async def execute(self, stmt):  # noqa: ARG002
        return StubResult(self._value)


class StubReport:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


@pytest.mark.asyncio
async def test_get_property_market_intelligence_success(monkeypatch):
    property_id = uuid4()
    property_record = SimpleNamespace(
        property_type=PropertyType.OFFICE,
        district="D01",
    )
    session = StubSession(property_record)

    async def fake_generate_market_report(*args, **kwargs):  # noqa: ARG001
        return StubReport(
            {
                "property_type": PropertyType.OFFICE.value,
                "comparables_analysis": {"transaction_count": 4},
            }
        )

    monkeypatch.setattr(
        agents,
        "market_analytics",
        SimpleNamespace(generate_market_report=fake_generate_market_report),
    )

    response = await get_property_market_intelligence(
        property_id=str(property_id),
        months=6,
        db=session,
        role="developer",
    )

    assert response.property_id == property_id
    assert response.report["comparables_analysis"]["transaction_count"] == 4


@pytest.mark.asyncio
async def test_get_property_market_intelligence_not_found(monkeypatch):
    session = StubSession(None)

    async def fake_generate(*args, **kwargs):  # noqa: ARG001
        return StubReport({})

    monkeypatch.setattr(
        agents,
        "market_analytics",
        SimpleNamespace(generate_market_report=fake_generate),
    )

    with pytest.raises(HTTPException) as exc:
        await get_property_market_intelligence(
            property_id=str(uuid4()),
            months=6,
            db=session,
            role="developer",
        )
    assert exc.value.status_code == 404
