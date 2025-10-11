from __future__ import annotations

from importlib import import_module
from uuid import uuid4

import pytest
import pytest_asyncio
from app.models.audit import AuditLog
from app.models.business_performance import DealAssetType, DealType, PipelineStage
from app.models.users import User
from app.schemas.deals import DealWithTimelineSchema
from app.services.deals import AgentDealService
from app.services.deals.utils import audit_project_key
from sqlalchemy import select


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
async def test_create_deal_seeds_stage_event(async_session_factory):
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="agent@example.com",
                username="pipeline_agent",
                full_name="Pipeline Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Jurong Logistics Hub",
            asset_type=DealAssetType.INDUSTRIAL,
            deal_type=DealType.SELL_SIDE,
            lead_source="referral",
            metadata={"priority": "high"},
            created_by=agent_id,
        )
        assert deal.pipeline_stage == PipelineStage.LEAD_CAPTURED
        assert deal.metadata["priority"] == "high"

        timeline, audit_map = await service.timeline_with_audit(session=session, deal=deal)
        assert len(timeline) == 1
        event = timeline[0]
        assert event.to_stage == PipelineStage.LEAD_CAPTURED
        assert event.note == "Deal created"
        assert str(event.changed_by) == str(agent_id)
        assert event.metadata.get("audit_log_id") is not None

        project_key = audit_project_key(deal)
        result = await session.execute(
            select(AuditLog).where(AuditLog.project_id == project_key)
        )
        logs = result.scalars().all()
        assert len(logs) == 1
        assert logs[0].context.get("deal_id") == str(deal.id)
        assert logs[0].context.get("to_stage") == PipelineStage.LEAD_CAPTURED.value
        audit_log = audit_map.get(str(logs[0].id))
        assert audit_log is not None


@pytest.mark.asyncio
async def test_change_stage_updates_status(async_session_factory):
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="closer@example.com",
                username="closer_agent",
                full_name="Closer Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Marina View Portfolio",
            asset_type=DealAssetType.PORTFOLIO,
            deal_type=DealType.CAPITAL_RAISE,
            created_by=agent_id,
        )
        event = await service.change_stage(
            session=session,
            deal=deal,
            to_stage=PipelineStage.CLOSED_WON,
            changed_by=agent_id,
            note="Signed SPA",
        )
        assert event.to_stage == PipelineStage.CLOSED_WON
        assert deal.status.name == "CLOSED_WON"
        assert deal.actual_close_date is not None

        timeline, audit_map = await service.timeline_with_audit(session=session, deal=deal)
        assert len(timeline) == 2
        assert timeline[-1].note == "Signed SPA"
        assert timeline[-1].metadata.get("audit_log_id") is not None

        project_key = audit_project_key(deal)
        result = await session.execute(
            select(AuditLog)
            .where(AuditLog.project_id == project_key)
            .order_by(AuditLog.version)
        )
        logs = result.scalars().all()
        assert len(logs) == 2
        assert logs[-1].context.get("to_stage") == PipelineStage.CLOSED_WON.value

        timeline_schema = DealWithTimelineSchema.from_orm_deal(
            deal, timeline=timeline, audit_logs=audit_map
        )
        assert timeline_schema.timeline[0].duration_seconds is not None
        assert timeline_schema.timeline[0].audit_log is not None
