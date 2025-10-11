from __future__ import annotations

import importlib.util
import sys
from importlib import import_module
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from app.models.users import User
from httpx import AsyncClient


@pytest_asyncio.fixture
async def deals_client(async_session_factory):
    from app.core.database import get_session
    from fastapi import APIRouter, FastAPI

    if not hasattr(APIRouter, "patch"):

        def _patch(self, path: str, **kwargs):
            return self.api_route(path, methods=["PATCH"], **kwargs)

        APIRouter.patch = _patch  # type: ignore[attr-defined]

    module_path = (
        Path(__file__).resolve().parents[3]
        / "backend"
        / "app"
        / "api"
        / "v1"
        / "deals.py"
    )
    spec = importlib.util.spec_from_file_location("temp_deals_router", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load deals router module for testing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    router = module.router

    app = FastAPI()

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session
    app.include_router(router, prefix="/api/v1")

    async with AsyncClient(
        app=app, base_url="http://testserver", headers={"X-Role": "admin"}
    ) as client:
        yield client

    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture(autouse=True)
async def _override_async_session_factory(
    flow_session_factory, monkeypatch
):  # pragma: no cover - test scaffolding
    module = import_module("app.core.database")
    monkeypatch.setattr(
        module,
        "AsyncSessionLocal",
        flow_session_factory,
        raising=False,
    )
    yield


@pytest.mark.asyncio
async def test_create_and_update_deal_pipeline(deals_client, async_session_factory):
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="api-agent@example.com",
                username="api_agent",
                full_name="API Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

    create_payload = {
        "title": "Harbourfront Office Sale",
        "description": "Grade A strata office disposition",
        "asset_type": "office",
        "deal_type": "sell_side",
        "lead_source": "existing_client",
        "estimated_value_amount": "12500000.00",
        "estimated_value_currency": "SGD",
        "agent_id": str(agent_id),
        "metadata": {"priority": "medium"},
    }
    create_response = await deals_client.post("/api/v1/deals", json=create_payload)
    assert create_response.status_code == 201, create_response.json()
    data = create_response.json()
    assert data["title"] == "Harbourfront Office Sale"
    assert data["pipeline_stage"] == "lead_captured"
    deal_id = data["id"]

    stage_payload = {"to_stage": "negotiation", "note": "Term sheet issued"}
    stage_response = await deals_client.post(
        f"/api/v1/deals/{deal_id}/stage", json=stage_payload
    )
    assert stage_response.status_code == 200
    stage_data = stage_response.json()
    assert stage_data["pipeline_stage"] == "negotiation"
    assert len(stage_data["timeline"]) == 2
    assert stage_data["timeline"][-1]["note"] == "Term sheet issued"

    list_response = await deals_client.get("/api/v1/deals")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["status"] == "open"

    timeline_response = await deals_client.get(f"/api/v1/deals/{deal_id}/timeline")
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    assert len(timeline) == 2
    assert timeline[1]["to_stage"] == "negotiation"
    assert timeline[1]["note"] == "Term sheet issued"


pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="FastAPI stub lacks request dependency injection for bearer security on Python < 3.10",
)
