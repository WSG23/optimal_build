"""Service helpers for managing commission records and adjustments."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional
from uuid import UUID

from backend._compat.datetime import UTC

from app.core.audit.ledger import append_event
from app.models.audit import AuditLog
from app.models.business_performance import (
    AgentCommissionAdjustment,
    AgentCommissionRecord,
    AgentDeal,
    CommissionAdjustmentType,
    CommissionStatus,
    CommissionType,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .utils import audit_project_key


class AgentCommissionService:
    """Create and manage commission ledger entries for agent deals."""

    _STATUS_TIMESTAMPS: dict[CommissionStatus, str] = {
        CommissionStatus.PENDING: "introduced_at",
        CommissionStatus.CONFIRMED: "confirmed_at",
        CommissionStatus.INVOICED: "invoiced_at",
        CommissionStatus.PAID: "paid_at",
        CommissionStatus.DISPUTED: "disputed_at",
        CommissionStatus.WRITTEN_OFF: "resolved_at",
    }

    async def list_commissions(
        self,
        *,
        session: AsyncSession,
        deal_id: UUID,
        statuses: Optional[Iterable[CommissionStatus]] = None,
    ) -> list[AgentCommissionRecord]:
        stmt = select(AgentCommissionRecord).where(
            AgentCommissionRecord.deal_id == str(deal_id)
        )
        if statuses:
            stmt = stmt.where(AgentCommissionRecord.status.in_(list(statuses)))
        stmt = stmt.options(selectinload(AgentCommissionRecord.adjustments))
        result = await session.execute(stmt)
        return list(result.scalars().unique())

    async def create_commission(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        agent_id: UUID,
        commission_type: CommissionType,
        status: CommissionStatus = CommissionStatus.PENDING,
        basis_amount: float | None = None,
        basis_currency: str = "SGD",
        commission_rate: float | None = None,
        commission_amount: float | None = None,
        introduced_at: datetime | None = None,
        metadata: Optional[dict] = None,
        actor_id: UUID | None = None,
    ) -> AgentCommissionRecord:
        record = AgentCommissionRecord(
            deal_id=deal.id,
            agent_id=str(agent_id),
            commission_type=commission_type,
            status=status,
            basis_amount=basis_amount,
            basis_currency=basis_currency,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            introduced_at=introduced_at or datetime.now(UTC),
        )
        if status in self._STATUS_TIMESTAMPS:
            field = self._STATUS_TIMESTAMPS.get(status)
            if field and getattr(record, field, None) is None:
                setattr(record, field, record.introduced_at)
        if metadata:
            record.metadata = metadata  # type: ignore[assignment,has-type]

        session.add(record)
        await session.flush()

        audit_log = await self._append_audit(
            session=session,
            deal=deal,
            record=record,
            event_type="deal_commission_created",
            actor_id=actor_id,
        )
        if audit_log is not None:
            record.audit_log_id = audit_log.id

        await session.commit()
        await session.refresh(record)
        return record

    async def update_status(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        record: AgentCommissionRecord,
        status: CommissionStatus,
        occurred_at: datetime | None = None,
        metadata: Optional[dict] = None,
        actor_id: UUID | None = None,
    ) -> AgentCommissionRecord:
        record.status = status
        timestamp_field = self._STATUS_TIMESTAMPS.get(status)
        if timestamp_field:
            setattr(record, timestamp_field, occurred_at or datetime.now(UTC))
        if metadata is not None:
            record.metadata = metadata  # type: ignore[assignment,has-type]

        audit_log = await self._append_audit(
            session=session,
            deal=deal,
            record=record,
            event_type="deal_commission_status_change",
            actor_id=actor_id,
            extra={"status": status.value},
        )
        if audit_log is not None:
            record.audit_log_id = audit_log.id

        await session.commit()
        await session.refresh(record)
        return record

    async def create_adjustment(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        record: AgentCommissionRecord,
        adjustment_type: CommissionAdjustmentType,
        amount: float | None = None,
        currency: str = "SGD",
        note: str | None = None,
        metadata: Optional[dict] = None,
        actor_id: UUID | None = None,
        recorded_at: datetime | None = None,
    ) -> AgentCommissionAdjustment:
        adjustment = AgentCommissionAdjustment(
            commission_id=record.id,
            adjustment_type=adjustment_type,
            amount=amount,
            currency=currency,
            note=note,
            recorded_by=str(actor_id) if actor_id else None,
            recorded_at=recorded_at or datetime.now(UTC),
        )
        if metadata:
            adjustment.metadata = metadata  # type: ignore[assignment,has-type]

        session.add(adjustment)
        await session.flush()

        audit_log = await self._append_audit(
            session=session,
            deal=deal,
            record=record,
            event_type="deal_commission_adjustment",
            actor_id=actor_id,
            extra={
                "adjustment_id": adjustment.id,
                "adjustment_type": adjustment.adjustment_type.value,
            },
        )
        if audit_log is not None:
            adjustment.audit_log_id = audit_log.id

        await session.commit()
        await session.refresh(adjustment)
        await session.refresh(record)
        return adjustment

    async def get_commission(
        self,
        *,
        session: AsyncSession,
        commission_id: UUID,
    ) -> AgentCommissionRecord | None:
        stmt = (
            select(AgentCommissionRecord)
            .where(AgentCommissionRecord.id == str(commission_id))
            .options(selectinload(AgentCommissionRecord.adjustments))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def _append_audit(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        record: AgentCommissionRecord,
        event_type: str,
        actor_id: UUID | None,
        extra: Optional[dict] = None,
    ) -> Optional[AuditLog]:
        project_key = audit_project_key(deal)
        if project_key is None:
            return None

        context: dict[str, object] = {
            "deal_id": str(deal.id),
            "commission_id": str(record.id),
            "commission_type": record.commission_type.value,
            "status": record.status.value,
            "agent_id": str(record.agent_id),
            "amount": (
                float(record.commission_amount) if record.commission_amount else None
            ),
            "basis_amount": float(record.basis_amount) if record.basis_amount else None,
            "actor_id": str(actor_id) if actor_id else None,
        }
        if extra:
            context.update(extra)

        return await append_event(
            session,
            project_id=project_key,
            event_type=event_type,
            context=context,
        )
