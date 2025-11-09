"""Service helpers for the agent deal pipeline foundation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Optional
from uuid import UUID

from backend._compat.datetime import UTC

from app.core.audit.ledger import append_event, serialise_log
from app.models.audit import AuditLog
from app.models.business_performance import (
    AgentDeal,
    AgentDealContact,
    AgentDealDocument,
    AgentDealStageEvent,
    DealAssetType,
    DealStatus,
    DealType,
    PipelineStage,
)
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .utils import audit_project_key


class AgentDealService:
    """Create, update and inspect agent deal pipeline records."""

    async def list_deals(
        self,
        *,
        session: AsyncSession,
        agent_ids: Iterable[UUID] | None = None,
        stages: Iterable[PipelineStage] | None = None,
        status: DealStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentDeal]:
        """Return deals filtered by the supplied parameters."""

        stmt = (
            select(AgentDeal)
            .order_by(desc(AgentDeal.created_at))
            .options(
                selectinload(AgentDeal.stage_events),
                selectinload(AgentDeal.contacts),
            )
        )

        if agent_ids:
            stmt = stmt.where(
                AgentDeal.agent_id.in_([str(agent_id) for agent_id in agent_ids])
            )
        if stages:
            stmt = stmt.where(AgentDeal.pipeline_stage.in_(list(stages)))
        if status:
            stmt = stmt.where(AgentDeal.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().unique())

    async def get_deal(
        self,
        *,
        session: AsyncSession,
        deal_id: UUID,
        with_timeline: bool = False,
    ) -> AgentDeal | None:
        """Fetch a single deal by identifier."""

        options = []
        if with_timeline:
            options.append(
                selectinload(AgentDeal.stage_events).order_by(
                    asc(AgentDealStageEvent.recorded_at)
                )
            )
            options.append(selectinload(AgentDeal.contacts))
            options.append(selectinload(AgentDeal.documents))

        return await session.get(
            AgentDeal,
            str(deal_id),
            options=options or None,
        )

    async def create_deal(
        self,
        *,
        session: AsyncSession,
        agent_id: UUID,
        title: str,
        asset_type: DealAssetType,
        deal_type: DealType,
        description: str | None = None,
        pipeline_stage: PipelineStage = PipelineStage.LEAD_CAPTURED,
        status: DealStatus = DealStatus.OPEN,
        lead_source: str | None = None,
        estimated_value_amount: float | None = None,
        estimated_value_currency: str = "SGD",
        expected_close_date: date | None = None,
        confidence: float | None = None,
        project_id: UUID | None = None,
        property_id: UUID | None = None,
        metadata: Optional[dict] = None,
        created_by: UUID | None = None,
    ) -> AgentDeal:
        """Create a new pipeline deal and seed the stage history."""

        record = AgentDeal(
            agent_id=str(agent_id),
            project_id=str(project_id) if project_id else None,
            property_id=str(property_id) if property_id else None,
            title=title,
            description=description,
            asset_type=asset_type,
            deal_type=deal_type,
            pipeline_stage=pipeline_stage,
            status=status,
            lead_source=lead_source,
            estimated_value_amount=estimated_value_amount,
            estimated_value_currency=estimated_value_currency,
            expected_close_date=expected_close_date,
            confidence=confidence,
        )
        if metadata:
            record.metadata = metadata

        session.add(record)
        await session.flush()

        event = AgentDealStageEvent(
            deal_id=record.id,
            from_stage=None,
            to_stage=pipeline_stage,
            changed_by=str(created_by) if created_by else str(agent_id),
            note="Deal created",
        )
        session.add(event)
        await session.flush()

        await self._record_stage_audit(
            session=session,
            deal=record,
            event=event,
            changed_by=str(created_by) if created_by else str(agent_id),
        )

        await session.commit()
        await session.refresh(
            record,
            attribute_names=[
                "title",
                "pipeline_stage",
                "status",
                "stage_events",
                "created_at",
                "updated_at",
            ],
        )
        return record

    async def update_deal(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        title: str | None = None,
        description: str | None = None,
        asset_type: DealAssetType | None = None,
        deal_type: DealType | None = None,
        lead_source: str | None = None,
        estimated_value_amount: float | None = None,
        estimated_value_currency: str | None = None,
        expected_close_date: date | None = None,
        actual_close_date: date | None = None,
        confidence: float | None = None,
        project_id: UUID | None = None,
        property_id: UUID | None = None,
        metadata: Optional[dict] = None,
        status: DealStatus | None = None,
    ) -> AgentDeal:
        """Mutate deal attributes and persist changes."""

        if title is not None:
            deal.title = title
        if description is not None:
            deal.description = description
        if asset_type is not None:
            deal.asset_type = asset_type
        if deal_type is not None:
            deal.deal_type = deal_type
        if lead_source is not None:
            deal.lead_source = lead_source
        if estimated_value_amount is not None:
            deal.estimated_value_amount = estimated_value_amount
        if estimated_value_currency is not None:
            deal.estimated_value_currency = estimated_value_currency
        if expected_close_date is not None:
            deal.expected_close_date = expected_close_date
        if actual_close_date is not None:
            deal.actual_close_date = actual_close_date
        if confidence is not None:
            deal.confidence = confidence
        if project_id is not None:
            deal.project_id = str(project_id)
        if property_id is not None:
            deal.property_id = str(property_id)
        if metadata is not None:
            deal.metadata = metadata
        if status is not None:
            deal.status = status

        await session.commit()
        await session.refresh(deal)
        return deal

    async def change_stage(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        to_stage: PipelineStage,
        changed_by: UUID | None,
        note: str | None = None,
        metadata: Optional[dict] = None,
        occurred_at: datetime | None = None,
    ) -> AgentDealStageEvent:
        """Transition a deal to another stage and emit a history event."""

        from_stage = deal.pipeline_stage
        deal.pipeline_stage = to_stage

        if to_stage == PipelineStage.CLOSED_WON:
            deal.status = DealStatus.CLOSED_WON
            deal.actual_close_date = deal.actual_close_date or date.today()
        elif to_stage == PipelineStage.CLOSED_LOST:
            deal.status = DealStatus.CLOSED_LOST
            deal.actual_close_date = deal.actual_close_date or date.today()
        else:
            if deal.status in {DealStatus.CLOSED_WON, DealStatus.CLOSED_LOST}:
                deal.status = DealStatus.OPEN

        event = AgentDealStageEvent(
            deal_id=deal.id,
            from_stage=from_stage,
            to_stage=to_stage,
            changed_by=str(changed_by) if changed_by else None,
            note=note,
            recorded_at=occurred_at,
        )
        if metadata:
            event.metadata = metadata

        session.add(event)
        await session.flush()

        await self._record_stage_audit(
            session=session,
            deal=deal,
            event=event,
            changed_by=str(changed_by) if changed_by else None,
        )

        await session.commit()
        await session.refresh(event)
        await session.refresh(deal)
        return event

    async def timeline(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
    ) -> list[AgentDealStageEvent]:
        """Return ordered stage events for a deal."""

        stmt = (
            select(AgentDealStageEvent)
            .where(AgentDealStageEvent.deal_id == deal.id)
            .order_by(asc(AgentDealStageEvent.recorded_at))
        )
        result = await session.execute(stmt)
        return list(result.scalars())

    async def timeline_with_audit(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
    ) -> tuple[list[AgentDealStageEvent], dict[str, dict[str, object]]]:
        """Return ordered stage events alongside their audit summaries."""

        events = await self.timeline(session=session, deal=deal)
        audit_ids: set[int] = set()
        for event in events:
            audit_id = None
            if event.metadata:
                audit_id = event.metadata.get("audit_log_id")
            if audit_id:
                try:
                    audit_ids.add(int(audit_id))
                except (TypeError, ValueError):
                    continue

        audit_map: dict[str, dict[str, object]] = {}
        if audit_ids:
            stmt = select(AuditLog).where(AuditLog.id.in_(audit_ids))
            result = await session.execute(stmt)
            for log in result.scalars().all():
                audit_map[str(log.id)] = serialise_log(log)

        return events, audit_map

    async def _record_stage_audit(
        self,
        *,
        session: AsyncSession,
        deal: AgentDeal,
        event: AgentDealStageEvent,
        changed_by: str | None,
    ) -> None:
        """Append a stage transition to the audit ledger."""

        project_key = audit_project_key(deal)
        if project_key is None:
            return

        recorded_at = event.recorded_at
        if recorded_at is None:
            recorded_at = datetime.now(UTC)

        context = {
            "deal_id": str(deal.id),
            "agent_id": str(deal.agent_id),
            "from_stage": event.from_stage.value if event.from_stage else None,
            "to_stage": event.to_stage.value,
            "status": deal.status.value,
            "note": event.note or None,
            "changed_by": str(changed_by) if changed_by else None,
            "project_ref": str(deal.project_id) if deal.project_id else None,
            "property_ref": str(deal.property_id) if deal.property_id else None,
        }

        log_entry = await append_event(
            session,
            project_id=project_key,
            event_type="deal_stage_transition",
            context=context,
            recorded_at=recorded_at,
        )
        raw_metadata = getattr(event, "metadata", None)
        if isinstance(raw_metadata, dict):
            event_metadata = dict(raw_metadata)
        else:
            event_metadata = dict(getattr(event, "metadata_json", {}) or {})
        event_metadata["audit_log_id"] = str(log_entry.id)
        event.metadata = event_metadata

    async def add_contact(
        self,
        *,
        session: AsyncSession,
        contact: AgentDealContact,
    ) -> AgentDealContact:
        """Persist a new contact entry."""

        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        return contact

    async def add_document(
        self,
        *,
        session: AsyncSession,
        document: AgentDealDocument,
    ) -> AgentDealDocument:
        """Persist a new document reference."""

        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document


__all__ = ["AgentDealService"]
