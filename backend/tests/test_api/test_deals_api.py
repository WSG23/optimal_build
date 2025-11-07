from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from app.api.deps import RequestIdentity
from app.api.v1 import deals as deals_api
from app.core.jwt_auth import TokenData
from app.main import app
from app.models.business_performance import (
    DealAssetType,
    DealStatus,
    DealType,
    PipelineStage,
)


def _make_deal(**overrides):
    data = dict(
        id=uuid4(),
        agent_id=uuid4(),
        project_id=None,
        property_id=None,
        title="Sample Deal",
        description="Desc",
        asset_type=DealAssetType.OFFICE,
        deal_type=DealType.LEASE,
        pipeline_stage=PipelineStage.LEAD_CAPTURED,
        status=DealStatus.OPEN,
        lead_source="referral",
        estimated_value_amount=Decimal("1000000"),
        estimated_value_currency="SGD",
        expected_close_date=datetime.utcnow().date(),
        actual_close_date=None,
        confidence=Decimal("0.5"),
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def _make_stage_event(deal_id: UUID) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        deal_id=deal_id,
        from_stage=PipelineStage.LEAD_CAPTURED,
        to_stage=PipelineStage.NEGOTIATION,
        changed_by=uuid4(),
        note="Progressed",
        recorded_at=datetime.utcnow(),
        metadata={},
    )


def _make_token(user_id: UUID | None) -> TokenData | None:
    if user_id is None:
        return None
    return TokenData(email="agent@example.com", username="agent", user_id=str(user_id))


@pytest.fixture(autouse=True)
def override_deal_dependencies():
    async def _get_session():
        yield SimpleNamespace()

    default_agent = uuid4()
    app.dependency_overrides[deals_api.get_session] = _get_session
    app.dependency_overrides[deals_api.require_viewer] = lambda: RequestIdentity(
        role="viewer", user_id=str(default_agent), email="viewer@example.com"
    )
    app.dependency_overrides[deals_api.require_reviewer] = lambda: RequestIdentity(
        role="reviewer", user_id=str(default_agent), email="reviewer@example.com"
    )
    app.dependency_overrides[deals_api.get_optional_user] = lambda: _make_token(
        default_agent
    )
    yield
    app.dependency_overrides.pop(deals_api.get_session, None)
    app.dependency_overrides.pop(deals_api.require_viewer, None)
    app.dependency_overrides.pop(deals_api.require_reviewer, None)
    app.dependency_overrides.pop(deals_api.get_optional_user, None)


def test_resolve_agent_id_from_payload():
    agent_id = uuid4()
    resolved = deals_api._resolve_agent_id(token=None, agent_id=agent_id)
    assert resolved == agent_id


def test_resolve_agent_id_uses_token_when_missing():
    agent_id = uuid4()
    token = _make_token(agent_id)
    resolved = deals_api._resolve_agent_id(token=token, agent_id=None)
    assert resolved == agent_id


def test_resolve_agent_id_raises_when_missing():
    with pytest.raises(HTTPException):
        deals_api._resolve_agent_id(token=None, agent_id=None)


@pytest.mark.asyncio
async def test_list_deals_returns_payload(client, monkeypatch):
    deal = _make_deal()
    monkeypatch.setattr(deals_api.service, "list_deals", AsyncMock(return_value=[deal]))

    response = await client.get(
        "/api/v1/deals",
        params={"agent_id": str(deal.agent_id), "limit": 5},
    )
    assert response.status_code == 200
    assert response.json()[0]["title"] == deal.title


@pytest.mark.asyncio
async def test_create_deal_uses_authenticated_agent(client, monkeypatch):
    deal = _make_deal()
    monkeypatch.setattr(deals_api.service, "create_deal", AsyncMock(return_value=deal))

    payload = {
        "title": "New Deal",
        "asset_type": "office",
        "deal_type": "lease",
        "pipeline_stage": "lead_captured",
        "status": "open",
        "estimated_value_currency": "SGD",
    }
    response = await client.post("/api/v1/deals", json=payload)
    assert response.status_code == 201
    assert response.json()["title"] == deal.title


@pytest.mark.asyncio
async def test_get_deal_not_found(client, monkeypatch):
    monkeypatch.setattr(deals_api.service, "get_deal", AsyncMock(return_value=None))
    response = await client.get(f"/api/v1/deals/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_change_stage_returns_timeline(client, monkeypatch):
    deal = _make_deal()
    event = _make_stage_event(deal.id)
    monkeypatch.setattr(deals_api.service, "get_deal", AsyncMock(return_value=deal))
    monkeypatch.setattr(
        deals_api.service,
        "change_stage",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        deals_api.service,
        "timeline_with_audit",
        AsyncMock(return_value=([event], {"1": {"note": "audit"}})),
    )

    response = await client.post(
        f"/api/v1/deals/{deal.id}/stage",
        json={"to_stage": "negotiation"},
    )
    assert response.status_code == 200
    assert response.json()["timeline"][0]["to_stage"] == "negotiation"


@pytest.mark.asyncio
async def test_list_commissions_deal_missing(client, monkeypatch):
    monkeypatch.setattr(deals_api.service, "get_deal", AsyncMock(return_value=None))
    response = await client.get(f"/api/v1/deals/{uuid4()}/commissions")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_timeline_uses_events(client, monkeypatch):
    deal = _make_deal()
    now = datetime.utcnow()
    event1 = _make_stage_event(deal.id)
    event1.recorded_at = now
    event2 = _make_stage_event(deal.id)
    event2.recorded_at = now + timedelta(days=1)

    monkeypatch.setattr(deals_api.service, "get_deal", AsyncMock(return_value=deal))
    monkeypatch.setattr(
        deals_api.service,
        "timeline_with_audit",
        AsyncMock(return_value=([event1, event2], {})),
    )

    response = await client.get(f"/api/v1/deals/{deal.id}/timeline")
    assert response.status_code == 200
    events = response.json()
    assert events[0]["duration_seconds"] == 86400.0
