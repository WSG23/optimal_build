from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock

from app.api.v1 import agents as agents_api
from app.main import app
from app.models.property import PropertyType


class _StubResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _StubSession:
    def __init__(self, result):
        self._result = result

    async def execute(self, stmt):
        return _StubResult(self._result)

    async def commit(self):
        return None

    async def rollback(self):
        return None


@pytest.fixture
def fake_property():
    return SimpleNamespace(
        id=uuid4(),
        district="D05",
        property_type=PropertyType.OFFICE,
    )


@pytest.mark.asyncio
async def test_get_property_market_intelligence_success(
    client, monkeypatch, fake_property
):
    session = _StubSession(fake_property)

    async def override_get_session():
        yield session

    app.dependency_overrides[agents_api.get_session] = override_get_session
    try:

        class DummyReport:
            def to_dict(self):
                return {"summary": "ok"}

        monkeypatch.setattr(
            agents_api.market_analytics,
            "generate_market_report",
            AsyncMock(return_value=DummyReport()),
        )

        response = await client.get(
            f"/api/v1/agents/commercial-property/properties/{fake_property.id}/market-intelligence",
            params={"months": 6},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["property_id"] == str(fake_property.id)
        assert payload["report"]["summary"] == "ok"
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_get_property_market_intelligence_404(client, monkeypatch):
    session = _StubSession(None)

    async def override_get_session():
        yield session

    app.dependency_overrides[agents_api.get_session] = override_get_session
    try:
        response = await client.get(
            f"/api/v1/agents/commercial-property/properties/{uuid4()}/market-intelligence"
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_get_property_advisory_summary(client, monkeypatch, fake_property):
    async def override_get_session():
        yield _StubSession(None)

    app.dependency_overrides[agents_api.get_session] = override_get_session

    summary = SimpleNamespace(
        asset_mix={
            "property_id": str(fake_property.id),
            "mix_recommendations": [
                {
                    "use": "office",
                    "allocation_pct": 60.0,
                    "target_gfa_sqm": 1200.0,
                    "rationale": "Test rationale",
                }
            ],
            "notes": ["Note"],
        },
        market_positioning={
            "market_tier": "Prime CBD",
            "pricing_guidance": {
                "sale_psf": {"target_min": 2500, "target_max": 2800},
                "rent_psm_monthly": {"target_min": 10, "target_max": 12},
            },
            "target_segments": [],
            "messaging": ["Message"],
        },
        absorption_forecast={
            "expected_months_to_stabilize": 12,
            "monthly_velocity_target": 4,
            "confidence": "medium",
            "timeline": [
                {
                    "milestone": "Launch",
                    "month": 3,
                    "expected_absorption_pct": 30.0,
                }
            ],
        },
        feedback=[
            {
                "id": str(uuid4()),
                "property_id": str(fake_property.id),
                "sentiment": "positive",
                "notes": "Great response",
                "created_at": datetime.utcnow().isoformat(),
            }
        ],
    )

    monkeypatch.setattr(
        agents_api.advisory_service, "build_summary", AsyncMock(return_value=summary)
    )

    try:
        response = await client.get(
            f"/api/v1/agents/commercial-property/properties/{fake_property.id}/advisory"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["asset_mix"]["property_id"] == str(fake_property.id)
        assert payload["feedback"][0]["sentiment"] == "positive"
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_get_property_market_intelligence_uses_fallback(
    client, monkeypatch, fake_property
):
    session = _StubSession(fake_property)

    async def override_get_session():
        yield session

    app.dependency_overrides[agents_api.get_session] = override_get_session
    monkeypatch.setattr(
        agents_api.market_analytics,
        "generate_market_report",
        AsyncMock(side_effect=RuntimeError("analytics offline")),
    )
    try:
        response = await client.get(
            f"/api/v1/agents/commercial-property/properties/{fake_property.id}/market-intelligence",
            params={"months": 3},
        )

        assert response.status_code == 200
        payload = response.json()["report"]
        assert payload["location"] == fake_property.district
        assert payload["comparables_analysis"]["transaction_count"] == 14
        assert payload["rental_snapshot"]["trend"] == "stable"
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_list_property_advisory_feedback(client, monkeypatch):
    property_id = uuid4()

    async def override_get_session():
        yield _StubSession(None)

    app.dependency_overrides[agents_api.get_session] = override_get_session
    feedback_items = [
        {
            "id": str(uuid4()),
            "property_id": str(property_id),
            "sentiment": "neutral",
            "notes": "Observation",
            "created_at": datetime.utcnow().isoformat(),
        }
    ]
    monkeypatch.setattr(
        agents_api.advisory_service,
        "list_feedback",
        AsyncMock(return_value=feedback_items),
    )

    try:
        response = await client.get(
            f"/api/v1/agents/commercial-property/properties/{property_id}/advisory/feedback"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload[0]["notes"] == "Observation"
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_submit_property_advisory_feedback(client, monkeypatch):
    property_id = uuid4()

    async def override_get_session():
        yield _StubSession(None)

    app.dependency_overrides[agents_api.get_session] = override_get_session
    stored_feedback = {
        "id": uuid4(),
        "property_id": property_id,
        "sentiment": "negative",
        "notes": "Needs work",
        "channel": "email",
        "context": {},
        "created_at": datetime.utcnow().isoformat(),
    }
    monkeypatch.setattr(
        agents_api.advisory_service,
        "record_feedback",
        AsyncMock(return_value=stored_feedback),
    )

    try:
        response = await client.post(
            f"/api/v1/agents/commercial-property/properties/{property_id}/advisory/feedback",
            json={"sentiment": "negative", "notes": "Needs work"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["notes"] == "Needs work"
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)
