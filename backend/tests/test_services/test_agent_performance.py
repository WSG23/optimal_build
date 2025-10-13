from __future__ import annotations

from importlib import import_module
from uuid import uuid4

import pytest

import pytest_asyncio
from app.models.business_performance import (
    AgentDeal,
    CommissionStatus,
    CommissionType,
    DealAssetType,
    DealStatus,
    DealType,
    PipelineStage,
)
from app.models.users import User
from app.services.deals import AgentCommissionService, AgentDealService
from app.services.deals.performance import AgentPerformanceService


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
async def test_compute_snapshot(async_session_factory):
    deal_service = AgentDealService()
    commission_service = AgentCommissionService()
    performance_service = AgentPerformanceService()

    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="snapshot-agent@example.com",
                username="snapshot_agent",
                full_name="Snapshot Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        closed_deal = await deal_service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Closed Tower Sale",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.SELL_SIDE,
            estimated_value_amount=1_000_000.0,
            confidence=0.5,
            created_by=agent_id,
        )
        await deal_service.change_stage(
            session=session,
            deal=closed_deal,
            to_stage=closed_deal.pipeline_stage.CLOSED_WON,  # type: ignore[attr-defined]
            changed_by=agent_id,
        )

        open_deal = await deal_service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Open Retail Prospect",
            asset_type=DealAssetType.RETAIL,
            deal_type=DealType.LEASE,
            estimated_value_amount=500_000.0,
            confidence=0.2,
            created_by=agent_id,
        )
        open_deal.metadata = {
            "roi_metrics": {
                "project_id": 101,
                "iterations": 6,
                "total_suggestions": 18,
                "decided_suggestions": 12,
                "accepted_suggestions": 9,
                "acceptance_rate": 0.75,
                "review_hours_saved": 14.5,
                "automation_score": 0.62,
                "savings_percent": 62,
                "payback_weeks": 3,
                "baseline_hours": 22.0,
                "actual_hours": 7.5,
            }
        }
        session.add(open_deal)
        await session.commit()

        commission = await commission_service.create_commission(
            session=session,
            deal=closed_deal,
            agent_id=agent_id,
            commission_type=CommissionType.EXCLUSIVE,
            basis_amount=100_000.0,
            commission_rate=0.05,
            commission_amount=5_000.0,
        )
        await commission_service.update_status(
            session=session,
            deal=closed_deal,
            record=commission,
            status=CommissionStatus.CONFIRMED,
        )

        snapshot = await performance_service.compute_snapshot(
            session=session,
            agent_id=agent_id,
        )

        assert str(snapshot.agent_id) == str(agent_id)
        assert snapshot.deals_open == 1
        assert snapshot.deals_closed_won == 1
        assert snapshot.deals_closed_lost == 0
        assert float(snapshot.gross_pipeline_value or 0.0) == pytest.approx(1_500_000.0)
        assert float(snapshot.weighted_pipeline_value or 0.0) == pytest.approx(
            1_000_000.0 * 0.5 + 500_000.0 * 0.2
        )
        assert float(snapshot.confirmed_commission_amount or 0.0) == pytest.approx(
            5_000.0
        )
        assert snapshot.disputed_commission_amount in (None, 0.0)
        assert snapshot.conversion_rate is not None
        assert snapshot.roi_metrics
        summary = snapshot.roi_metrics.get("summary", {})
        assert summary.get("project_count") == 1
        projects = snapshot.roi_metrics.get("projects", [])
        assert projects and projects[0]["project_id"] == 101

        snapshots = await performance_service.list_snapshots(
            session=session, agent_id=agent_id
        )
        assert len(snapshots) == 1

        generated = await performance_service.generate_daily_snapshots(
            session=session,
            agent_ids=[agent_id],
        )
        assert len(generated) == 1
        assert str(generated[0].agent_id) == str(agent_id)


@pytest.mark.asyncio
async def test_seed_benchmarks(async_session_factory):
    performance_service = AgentPerformanceService()

    async with async_session_factory() as session:
        seeds = [
            {
                "metric_key": "conversion_rate",
                "asset_type": "office",
                "deal_type": "sell_side",
                "cohort": "industry_avg",
                "value_numeric": 0.33,
                "source": "test",
                "effective_date": "2024-02-01",
            }
        ]

        count = await performance_service.seed_default_benchmarks(
            session=session, seeds=seeds
        )
        assert count == 1

        benchmarks = await performance_service.list_benchmarks(
            session=session,
            metric_key="conversion_rate",
            asset_type="office",
            deal_type="sell_side",
        )
        assert len(benchmarks) >= 1
        assert float(benchmarks[0].value_numeric or 0.0) == pytest.approx(0.33)


@pytest.mark.asyncio
async def test_generate_skips_invalid_agent_ids(async_session_factory):
    performance_service = AgentPerformanceService()

    async with async_session_factory() as session:
        # Insert a valid deal
        deal_service = AgentDealService()
        agent_id = uuid4()
        await deal_service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Valid Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.SELL_SIDE,
            created_by=agent_id,
        )

        # Simulate legacy/truncated data
        session.add(
            AgentDeal(
                agent_id="f",
                title="Bad Deal",
                asset_type=DealAssetType.OFFICE,
                deal_type=DealType.SELL_SIDE,
                pipeline_stage=PipelineStage.LEAD_CAPTURED,
                status=DealStatus.OPEN,
            )
        )
        await session.commit()

        snapshots = await performance_service.generate_daily_snapshots(
            session=session,
            as_of=None,
        )
        assert len(snapshots) == 1
        assert str(snapshots[0].agent_id) == str(agent_id)
