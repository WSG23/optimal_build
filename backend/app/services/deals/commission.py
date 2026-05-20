"""Service helpers for managing commission records and adjustments."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Iterable, Optional
from uuid import UUID

from backend._compat.datetime import UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.services.analytics_capture import (
    capture_lifecycle_event,
    capture_status_transition,
    capture_success,
)

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

    @staticmethod
    def _actor_identity(actor_id: UUID | None) -> object | None:
        if actor_id is None:
            return None
        return SimpleNamespace(user_id=str(actor_id))

    @staticmethod
    def _enum_value(value: object) -> object:
        return value.value if hasattr(value, "value") else value

    def _commission_payload(self, record: AgentCommissionRecord) -> dict[str, object]:
        return {
            "id": str(record.id),
            "deal_id": str(record.deal_id),
            "agent_id": str(record.agent_id),
            "commission_type": self._enum_value(record.commission_type),
            "status": self._enum_value(record.status),
            "basis_amount": (
                float(record.basis_amount) if record.basis_amount is not None else None
            ),
            "basis_currency": record.basis_currency,
            "commission_rate": (
                float(record.commission_rate)
                if record.commission_rate is not None
                else None
            ),
            "commission_amount": (
                float(record.commission_amount)
                if record.commission_amount is not None
                else None
            ),
            "introduced_at": (
                record.introduced_at.isoformat() if record.introduced_at else None
            ),
            "audit_log_id": record.audit_log_id,
            "metadata": getattr(record, "metadata", None),
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
            record.metadata = metadata

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
        actor = self._actor_identity(actor_id)
        await capture_lifecycle_event(
            session,
            entity_type="agent_commission",
            entity_id=str(record.id),
            action="create",
            identity=actor,
            after_payload=self._commission_payload(record),
            metadata={"deal_id": str(deal.id), "audit_log_id": record.audit_log_id},
        )
        await capture_status_transition(
            session,
            entity_type="agent_commission",
            entity_id=str(record.id),
            status_field="status",
            from_status=None,
            to_status=str(self._enum_value(status)),
            reason="commission_created",
            identity=actor,
            metadata={"deal_id": str(deal.id)},
        )
        await capture_success(
            session,
            source="deal_commission.create",
            operation="create",
            entity_type="agent_commission",
            entity_id=str(record.id),
            raw_payload=self._commission_payload(record),
            metadata={"deal_id": str(deal.id)},
        )

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
        previous_status = record.status
        before_payload = self._commission_payload(record)
        record.status = status
        timestamp_field = self._STATUS_TIMESTAMPS.get(status)
        if timestamp_field:
            setattr(record, timestamp_field, occurred_at or datetime.now(UTC))
        if metadata is not None:
            record.metadata = metadata

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
        actor = self._actor_identity(actor_id)
        await capture_status_transition(
            session,
            entity_type="agent_commission",
            entity_id=str(record.id),
            status_field="status",
            from_status=str(self._enum_value(previous_status)),
            to_status=str(self._enum_value(status)),
            reason="commission_status_change",
            identity=actor,
            metadata={"deal_id": str(deal.id), "audit_log_id": record.audit_log_id},
        )
        await capture_lifecycle_event(
            session,
            entity_type="agent_commission",
            entity_id=str(record.id),
            action="update",
            identity=actor,
            before_payload=before_payload,
            after_payload=self._commission_payload(record),
            metadata={"updated_fields": ["status"], "deal_id": str(deal.id)},
        )
        await capture_success(
            session,
            source="deal_commission.update_status",
            operation="status_transition",
            entity_type="agent_commission",
            entity_id=str(record.id),
            raw_payload=self._commission_payload(record),
            metadata={"deal_id": str(deal.id)},
        )

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
            adjustment.metadata = metadata

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
        actor = self._actor_identity(actor_id)
        await capture_lifecycle_event(
            session,
            entity_type="agent_commission_adjustment",
            entity_id=str(adjustment.id),
            action="create",
            identity=actor,
            after_payload={
                "id": str(adjustment.id),
                "commission_id": str(adjustment.commission_id),
                "adjustment_type": self._enum_value(adjustment.adjustment_type),
                "amount": (
                    float(adjustment.amount) if adjustment.amount is not None else None
                ),
                "currency": adjustment.currency,
                "note": adjustment.note,
                "recorded_by": (
                    str(adjustment.recorded_by) if adjustment.recorded_by else None
                ),
                "recorded_at": (
                    adjustment.recorded_at.isoformat()
                    if adjustment.recorded_at
                    else None
                ),
                "audit_log_id": adjustment.audit_log_id,
                "metadata": getattr(adjustment, "metadata", None),
            },
            metadata={"deal_id": str(deal.id), "commission_id": str(record.id)},
        )
        await capture_success(
            session,
            source="deal_commission.adjustment",
            operation="create_adjustment",
            entity_type="agent_commission_adjustment",
            entity_id=str(adjustment.id),
            metadata={"deal_id": str(deal.id), "commission_id": str(record.id)},
        )

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
