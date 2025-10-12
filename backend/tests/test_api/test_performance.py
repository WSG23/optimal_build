from __future__ import annotations

import importlib.util
import sys
from importlib import import_module
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from app.models.business_performance import (
    CommissionStatus,
    CommissionType,
    DealAssetType,
    DealType,
)
from app.models.users import User
from app.services.deals import AgentCommissionService, AgentDealService
from app.services.deals.performance import AgentPerformanceService
from fastapi import APIRouter, FastAPI
from httpx import AsyncClient


@pytest_asyncio.fixture
async def performance_client(async_session_factory):
    from app.api.deps import require_viewer
    from app.core.database import get_session

    module_path = (
        Path(__file__).resolve().parents[3]
        / "backend"
        / "app"
        / "api"
        / "v1"
        / "performance.py"
    )
    spec = importlib.util.spec_from_file_location("temp_performance_router", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load performance router module for testing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    router: APIRouter = module.router

    app = FastAPI()

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    async def _override_require_viewer():
        return "admin"

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[require_viewer] = _override_require_viewer
    app.include_router(router, prefix="/api/v1")

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def _override_async_session_factory(flow_session_factory, monkeypatch):
    module = import_module("app.core.database")
    monkeypatch.setattr(
        module,
        "AsyncSessionLocal",
        flow_session_factory,
        raising=False,
    )
    yield


@pytest.mark.asyncio
async def test_performance_endpoints(performance_client, async_session_factory):
    agent_id = uuid4()

    deal_service = AgentDealService()
    commission_service = AgentCommissionService()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="perf-agent@example.com",
                username="perf_agent",
                full_name="Performance Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await deal_service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Performance Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.SELL_SIDE,
            estimated_value_amount=750_000.0,
            confidence=0.4,
            created_by=agent_id,
        )
        await commission_service.create_commission(
            session=session,
            deal=deal,
            agent_id=agent_id,
            commission_type=CommissionType.INTRODUCER,
            commission_amount=3_000.0,
        )

        performance_service = AgentPerformanceService()
        await performance_service.upsert_benchmark(
            session=session,
            metric_key="conversion_rate",
            asset_type="office",
            deal_type="sell_side",
            cohort="industry_avg",
            value_numeric=0.35,
        )
        await session.commit()

    snapshot_request = {
        "agent_id": str(agent_id),
    }
    snapshot_response = await performance_client.post(
        "/api/v1/performance/snapshots", json=snapshot_request
    )
    assert snapshot_response.status_code == 200, snapshot_response.text
    data = snapshot_response.json()
    assert data["agent_id"] == str(agent_id)

    list_response = await performance_client.get(
        f"/api/v1/performance/snapshots?agent_id={agent_id}"
    )
    assert list_response.status_code == 200
    snapshots = list_response.json()
    assert len(snapshots) >= 1

    summary_response = await performance_client.get(
        f"/api/v1/performance/summary?agent_id={agent_id}"
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["agent_id"] == str(agent_id)

    # Call generate without agent_ids parameter to generate for all agents
    generate_response = await performance_client.post(
        "/api/v1/performance/snapshots/generate"
    )
    assert generate_response.status_code == 200
    generated = generate_response.json()
    assert len(generated) >= 1

    benchmarks_response = await performance_client.get(
        "/api/v1/performance/benchmarks?metric_key=conversion_rate&asset_type=office"
    )
    assert benchmarks_response.status_code == 200
    benchmarks = benchmarks_response.json()
    assert benchmarks[0]["metric_key"] == "conversion_rate"


pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="FastAPI stub lacks full dependency injection for bearer auth on Python < 3.10",
)
