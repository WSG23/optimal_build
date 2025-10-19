from __future__ import annotations

from importlib import import_module
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.business_performance import (
    CommissionAdjustmentType,
    CommissionStatus,
    CommissionType,
    DealAssetType,
    DealType,
)
from app.models.users import User
from app.services.deals import AgentCommissionService, AgentDealService


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
async def test_commission_lifecycle(async_session_factory):
    deal_service = AgentDealService()
    commission_service = AgentCommissionService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="agent@example.com",
                username="agent_user",
                full_name="Commission Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await deal_service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Citylink Sale",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.SELL_SIDE,
            created_by=agent_id,
        )
        await session.refresh(deal)

        record = await commission_service.create_commission(
            session=session,
            deal=deal,
            agent_id=agent_id,
            commission_type=CommissionType.EXCLUSIVE,
            basis_amount=250000.0,
            commission_rate=0.02,
            commission_amount=5000.0,
        )
        assert record.status == CommissionStatus.PENDING
        assert record.audit_log_id is not None

        result = await session.execute(
            select(AuditLog).where(AuditLog.id == record.audit_log_id)
        )
        log = result.scalar_one()
        assert log.event_type == "deal_commission_created"
        assert log.context.get("commission_id") == str(record.id)

        updated = await commission_service.update_status(
            session=session,
            deal=deal,
            record=record,
            status=CommissionStatus.CONFIRMED,
        )
        assert updated.status == CommissionStatus.CONFIRMED
        assert updated.confirmed_at is not None

        adjustment = await commission_service.create_adjustment(
            session=session,
            deal=deal,
            record=updated,
            adjustment_type=CommissionAdjustmentType.BONUS,
            amount=1000.0,
            note="Performance bonus",
        )
        assert adjustment.adjustment_type == CommissionAdjustmentType.BONUS
        assert adjustment.audit_log_id is not None

        await session.refresh(updated, attribute_names=["adjustments"])
        assert len(updated.adjustments) == 1
