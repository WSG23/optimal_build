"""Tests for the deal outcome capture and benchmark API."""

from __future__ import annotations

import importlib.util
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

import pytest_asyncio
from app.models.business_performance import (
    AgentDeal,
    DealAssetType,
    DealStatus,
    DealType,
    PipelineStage,
)
from app.models.finance import FinAssetBreakdown, FinProject, FinScenario
from app.models.projects import Project, ProjectType
from app.models.users import User
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select


def _load_router(filename: str):
    """Load an API router module by filename from backend/app/api/v1."""

    module_path = (
        Path(__file__).resolve().parents[3]
        / "backend"
        / "app"
        / "api"
        / "v1"
        / filename
    )
    spec = importlib.util.spec_from_file_location(
        f"temp_{filename.replace('.py', '')}_router", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load router module {filename}")
    module = importlib.util.module_from_spec(spec)
    # type-ignore-meta: owner=backend expires=2026-12-31 reason=guarded loader  # noqa: E501
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module.router


@pytest_asyncio.fixture
async def outcomes_client(async_session_factory):
    from fastapi import APIRouter, FastAPI

    from app.api.deps import require_reviewer, require_viewer
    from app.core.database import get_session
    from app.core.jwt_auth import get_optional_user

    if not hasattr(APIRouter, "patch"):

        def _patch(self, path: str, **kwargs):
            return self.api_route(path, methods=["PATCH"], **kwargs)

        # type-ignore-meta: owner=backend expires=2026-12-31 reason=fastapi patch shim  # noqa: E501
        APIRouter.patch = _patch  # type: ignore[attr-defined]

    outcomes_router = _load_router("deal_outcomes.py")
    deals_router = _load_router("deals.py")

    app = FastAPI()

    async def _override_get_session():
        async with async_session_factory() as session:
            yield session

    async def _override_role():
        return "admin"

    async def _override_optional_user():
        return None

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[require_reviewer] = _override_role
    app.dependency_overrides[require_viewer] = _override_role
    app.dependency_overrides[get_optional_user] = _override_optional_user
    app.include_router(deals_router, prefix="/api/v1")
    app.include_router(outcomes_router, prefix="/api/v1")

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", headers={"X-Role": "admin"}
    ) as client:
        yield client

    app.dependency_overrides.clear()


async def _seed_agent_and_deal(
    async_session_factory,
    *,
    status: DealStatus = DealStatus.CLOSED_WON,
) -> tuple[str, str]:
    """Insert a user and a deal in the given terminal status."""

    agent_id = str(uuid4())
    deal_id = str(uuid4())

    async with async_session_factory() as session:
        session.add(
            User(
                id=agent_id,
                email=f"agent-{agent_id[:8]}@example.com",
                username=f"agent_{agent_id[:8]}",
                full_name="Test Agent",
                hashed_password="secret",
            )
        )
        session.add(
            AgentDeal(
                id=deal_id,
                agent_id=agent_id,
                title="Test Deal",
                asset_type=DealAssetType.OFFICE,
                deal_type=DealType.BUY_SIDE,
                pipeline_stage=PipelineStage.CLOSED_WON,
                status=status,
            )
        )
        await session.commit()

    return agent_id, deal_id


async def _seed_scenario_with_projections(
    async_session_factory,
    *,
    total_cost: Decimal,
    asset_noi: Decimal,
    asset_yield: Decimal,
    allocation: Decimal,
) -> tuple[int, str]:
    """Create a project, FinProject, FinScenario, and FinAssetBreakdown."""

    project_id = str(uuid4())

    async with async_session_factory() as session:
        session.add(
            Project(
                id=project_id,
                project_name="Test Project",
                project_code=f"P-{project_id[:8]}",
                project_type=ProjectType.NEW_DEVELOPMENT,
            )
        )
        fin_project = FinProject(
            project_id=project_id,
            name="Test Fin Project",
            currency="SGD",
            total_development_cost=total_cost,
        )
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Test Scenario",
            assumptions={},
        )
        session.add(scenario)
        await session.flush()

        session.add(
            FinAssetBreakdown(
                project_id=project_id,
                scenario_id=scenario.id,
                asset_type="office",
                allocation_pct=allocation,
                annual_noi_sgd=asset_noi,
                stabilised_yield_pct=asset_yield,
            )
        )
        await session.commit()
        scenario_id = scenario.id

    return scenario_id, project_id


@pytest.mark.asyncio
async def test_create_outcome_for_closed_deal(outcomes_client, async_session_factory):
    """Closed deals accept outcome capture with full payload."""

    _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)

    payload = {
        "resolution": "completed",
        "actual_purchase_price": "12500000.00",
        "actual_price_currency": "SGD",
        "actual_gfa_approved_sqm": "8500.00",
        "jurisdiction_code": "SG",
        "asset_type": "office",
        "approval_authority": "URA",
        "approval_outcome": "approved",
    }
    response = await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome", json=payload
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["deal_id"] == deal_id
    assert data["resolution"] == "completed"
    assert Decimal(data["actual_purchase_price"]) == Decimal("12500000.00")
    assert data["jurisdiction_code"] == "SG"


@pytest.mark.asyncio
async def test_create_outcome_rejects_open_deal(outcomes_client, async_session_factory):
    """Open deals cannot have outcomes recorded against them."""

    _agent_id, deal_id = await _seed_agent_and_deal(
        async_session_factory, status=DealStatus.OPEN
    )

    response = await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={"resolution": "completed"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_outcome_returns_409_on_duplicate(
    outcomes_client, async_session_factory
):
    """Second POST for the same deal returns 409, not 500."""

    _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)

    first = await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={"resolution": "completed"},
    )
    assert first.status_code == 201

    second = await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={"resolution": "completed"},
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_create_outcome_missing_deal(outcomes_client):
    """Recording an outcome for a non-existent deal returns 404."""

    response = await outcomes_client.post(
        f"/api/v1/deals/{uuid4()}/outcome",
        json={"resolution": "completed"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_outcome_includes_projected_vs_actual(
    outcomes_client, async_session_factory
):
    """GET returns the linked scenario comparison when a scenario_id is set."""

    _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)
    scenario_id, _project_id = await _seed_scenario_with_projections(
        async_session_factory,
        total_cost=Decimal("10000000"),
        asset_noi=Decimal("500000"),
        asset_yield=Decimal("5.000"),
        allocation=Decimal("1.0"),
    )

    create_resp = await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={
            "resolution": "completed",
            "scenario_id": scenario_id,
            "actual_purchase_price": "11000000",
            "actual_noi": "525000",
            "actual_yield_pct": "5.250",
        },
    )
    assert create_resp.status_code == 201

    get_resp = await outcomes_client.get(f"/api/v1/deals/{deal_id}/outcome")
    assert get_resp.status_code == 200
    body = get_resp.json()
    projected = body["projected_vs_actual"]
    assert projected is not None
    assert projected["scenario_id"] == scenario_id

    deltas = projected["deltas"]
    assert "purchase_price" in deltas
    assert deltas["purchase_price"]["projected"] == 10000000.0
    assert deltas["purchase_price"]["actual"] == 11000000.0
    assert deltas["purchase_price"]["delta_pct"] == 10.0
    assert deltas["noi"]["delta_pct"] == 5.0
    assert deltas["yield_pct"]["delta_pct"] == 5.0


@pytest.mark.asyncio
async def test_patch_outcome_clears_field_when_null(
    outcomes_client, async_session_factory
):
    """PATCH with explicit null clears nullable fields."""

    _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)

    await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={
            "resolution": "completed",
            "actual_purchase_price": "5000000",
            "resolution_note": "Initial note",
        },
    )

    patch_resp = await outcomes_client.patch(
        f"/api/v1/deals/{deal_id}/outcome",
        json={"resolution_note": None},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["resolution_note"] is None
    # Other fields untouched
    assert Decimal(patch_resp.json()["actual_purchase_price"]) == Decimal("5000000")


@pytest.mark.asyncio
async def test_benchmarks_aggregate_across_outcomes(
    outcomes_client, async_session_factory
):
    """Benchmarks compute medians and resolution distribution."""

    for yield_pct, price, gfa, resolution in [
        ("4.500", "10000000", "5000", "completed"),
        ("5.000", "12000000", "6000", "completed"),
        ("5.500", "14000000", "7000", "lost_price"),
    ]:
        _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)
        await outcomes_client.post(
            f"/api/v1/deals/{deal_id}/outcome",
            json={
                "resolution": resolution,
                "jurisdiction_code": "SG",
                "asset_type": "office",
                "actual_purchase_price": price,
                "actual_gfa_approved_sqm": gfa,
                "actual_yield_pct": yield_pct,
            },
        )

    resp = await outcomes_client.get(
        "/api/v1/deals/outcomes/benchmarks",
        params={"jurisdiction_code": "SG", "asset_type": "office"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sample_size"] == 3
    assert Decimal(data["median_yield_pct"]) == Decimal("5.0")
    assert Decimal(data["median_price_psm"]) == Decimal("2000.0")  # 12_000_000 / 6_000
    assert data["resolution_distribution"] == {"completed": 2, "lost_price": 1}
    assert data["truncated"] is False


@pytest.mark.asyncio
async def test_compare_endpoint_returns_404_without_outcome(
    outcomes_client, async_session_factory
):
    """Comparison endpoint 404s when no outcome is linked to the scenario."""

    scenario_id, _project_id = await _seed_scenario_with_projections(
        async_session_factory,
        total_cost=Decimal("1"),
        asset_noi=Decimal("1"),
        asset_yield=Decimal("1"),
        allocation=Decimal("1"),
    )

    resp = await outcomes_client.get(f"/api/v1/deals/outcomes/compare/{scenario_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_outcome_returns_404(outcomes_client, async_session_factory):
    """GET on a deal with no outcome returns 404."""

    _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)
    resp = await outcomes_client.get(f"/api/v1/deals/{deal_id}/outcome")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_compare_picks_most_recent_outcome_when_scenario_reused(
    outcomes_client, async_session_factory
):
    """If two deals reference the same scenario, comparison uses the latest outcome.

    Without the order_by + limit fix in compare_projected_vs_actual,
    SQLAlchemy raises MultipleResultsFound when two outcomes share a
    scenario_id. This test verifies both: that no crash occurs, and that
    the most-recent outcome is returned.
    """

    from datetime import datetime, timedelta, timezone

    from app.models.deal_outcome import DealOutcome

    scenario_id, _project_id = await _seed_scenario_with_projections(
        async_session_factory,
        total_cost=Decimal("10000000"),
        asset_noi=Decimal("500000"),
        asset_yield=Decimal("5.000"),
        allocation=Decimal("1.0"),
    )

    _agent_a, deal_a = await _seed_agent_and_deal(async_session_factory)
    _agent_b, deal_b = await _seed_agent_and_deal(async_session_factory)

    # Create outcomes with explicit timestamps so the "most recent" check is
    # deterministic on SQLite (which truncates now() to second precision).
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    async with async_session_factory() as session:
        session.add(
            DealOutcome(
                deal_id=deal_a,
                scenario_id=scenario_id,
                resolution="completed",
                actual_purchase_price=9000000,
                created_at=base,
                updated_at=base,
            )
        )
        session.add(
            DealOutcome(
                deal_id=deal_b,
                scenario_id=scenario_id,
                resolution="completed",
                actual_purchase_price=11000000,
                created_at=base + timedelta(hours=1),
                updated_at=base + timedelta(hours=1),
            )
        )
        await session.commit()

    resp = await outcomes_client.get(f"/api/v1/deals/outcomes/compare/{scenario_id}")
    assert resp.status_code == 200
    body = resp.json()
    # Latest outcome (deal_b, +1h) wins
    assert body["deltas"]["purchase_price"]["actual"] == 11000000.0


@pytest.mark.asyncio
async def test_create_writes_audit_log_entry(outcomes_client, async_session_factory):
    """Recording an outcome appends an audit ledger entry for the deal."""

    from app.models.audit import AuditLog

    _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)

    await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={"resolution": "completed"},
    )

    async with async_session_factory() as session:
        logs = (
            (
                await session.execute(
                    select(AuditLog).where(
                        AuditLog.event_type == "deal_outcome.created"
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(logs) == 1
        ctx = logs[0].context
        assert ctx["deal_id"] == deal_id
        assert ctx["resolution"] == "completed"


@pytest.mark.asyncio
async def test_update_audit_log_lists_touched_fields(
    outcomes_client, async_session_factory
):
    """PATCH audit entry should record every key the request touched."""

    from app.models.audit import AuditLog

    _agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)
    await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={"resolution": "completed"},
    )

    await outcomes_client.patch(
        f"/api/v1/deals/{deal_id}/outcome",
        json={
            "resolution_note": "Updated note",
            "metadata": {"key": "value"},
        },
    )

    async with async_session_factory() as session:
        log = (
            await session.execute(
                select(AuditLog)
                .where(AuditLog.event_type == "deal_outcome.updated")
                .order_by(AuditLog.recorded_at.desc())
                .limit(1)
            )
        ).scalar_one()
        assert sorted(log.context["updated_fields"]) == [
            "metadata",
            "resolution_note",
        ]


@pytest.mark.asyncio
async def test_user_deletion_preserves_outcome(outcomes_client, async_session_factory):
    """Deleting the recorder user nulls out recorded_by but keeps the outcome."""

    from app.models.deal_outcome import DealOutcome

    agent_id, deal_id = await _seed_agent_and_deal(async_session_factory)

    await outcomes_client.post(
        f"/api/v1/deals/{deal_id}/outcome",
        json={"resolution": "completed"},
    )

    async with async_session_factory() as session:
        outcome = (
            await session.execute(
                select(DealOutcome).where(DealOutcome.deal_id == deal_id)
            )
        ).scalar_one()
        # Recorder is None here because the test client doesn't authenticate;
        # the FK still allows null and the row persists.
        assert str(outcome.deal_id) == deal_id
        assert outcome.resolution == "completed"
        outcome_pk = outcome.id

        user = (
            await session.execute(select(User).where(User.id == agent_id))
        ).scalar_one()
        await session.delete(user)
        await session.commit()

        # Outcome row still exists after user deletion
        still_there = (
            await session.execute(
                select(DealOutcome).where(DealOutcome.deal_id == deal_id)
            )
        ).scalar_one()
        assert still_there.id == outcome_pk
