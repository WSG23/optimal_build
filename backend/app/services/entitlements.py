"""Service layer for entitlement management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entitlements import (
    EntApprovalType,
    EntAuthority,
    EntEngagement,
    EntLegalInstrument,
    EntRoadmapItem,
    EntStudy,
)
from app.schemas import entitlements as schema


class EntitlementNotFoundError(Exception):
    """Raised when a requested entitlement record does not exist."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _paginate_statement(
    stmt: Select[object],
    *,
    limit: int,
    offset: int,
) -> Select[object]:
    return stmt.limit(max(limit, 0)).offset(max(offset, 0))


@dataclass
class PaginatedResult:
    """Simple container for paginated results."""

    items: Sequence[object]
    total: int


class EntitlementsService:
    """Encapsulates entitlement CRUD and sequencing rules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Authority and approval management (used by seeds/exports)
    # ------------------------------------------------------------------
    async def upsert_authority(
        self,
        *,
        code: str,
        name: str,
        jurisdiction: str = "SG",
        contact_email: Optional[str] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> EntAuthority:
        stmt = select(EntAuthority).where(EntAuthority.code == code).limit(1)
        authority = (await self.session.execute(stmt)).scalar_one_or_none()
        payload = dict(metadata or {})
        if authority:
            authority.name = name
            authority.jurisdiction = jurisdiction
            authority.contact_email = contact_email
            authority.metadata = payload
            authority.updated_at = _utcnow()
        else:
            authority = EntAuthority(
                code=code,
                name=name,
                jurisdiction=jurisdiction,
                contact_email=contact_email,
                metadata=payload,
            )
            self.session.add(authority)
        await self.session.flush()
        return authority

    async def upsert_approval_type(
        self,
        *,
        authority: EntAuthority,
        code: str,
        name: str,
        description: Optional[str] = None,
        default_lead_time_days: Optional[int] = None,
        metadata: Optional[Dict[str, object]] = None,
    ) -> EntApprovalType:
        stmt = (
            select(EntApprovalType)
            .where(EntApprovalType.authority_id == authority.id)
            .where(EntApprovalType.code == code)
            .limit(1)
        )
        approval = (await self.session.execute(stmt)).scalar_one_or_none()
        payload = dict(metadata or {})
        if approval:
            approval.name = name
            approval.description = description
            approval.default_lead_time_days = default_lead_time_days
            approval.metadata = payload
            approval.updated_at = _utcnow()
        else:
            approval = EntApprovalType(
                authority_id=authority.id,
                code=code,
                name=name,
                description=description,
                default_lead_time_days=default_lead_time_days,
                metadata=payload,
            )
            self.session.add(approval)
        await self.session.flush()
        return approval

    async def list_authorities(self) -> List[EntAuthority]:
        stmt = select(EntAuthority).order_by(EntAuthority.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_approval_types(self) -> List[EntApprovalType]:
        stmt = (
            select(EntApprovalType)
            .options(selectinload(EntApprovalType.authority))
            .order_by(EntApprovalType.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    # ------------------------------------------------------------------
    # Roadmap management
    # ------------------------------------------------------------------
    async def list_roadmap(
        self, *, project_id: int, limit: int = 50, offset: int = 0
    ) -> PaginatedResult:
        stmt = (
            select(EntRoadmapItem)
            .options(selectinload(EntRoadmapItem.approval_type))
            .where(EntRoadmapItem.project_id == project_id)
            .order_by(EntRoadmapItem.sequence, EntRoadmapItem.id)
        )
        result = await self.session.execute(_paginate_statement(stmt, limit=limit, offset=offset))
        items = list(result.scalars().unique().all())

        total = await self._count_for_project(EntRoadmapItem, project_id)
        return PaginatedResult(items=items, total=total)

    async def create_roadmap_item(
        self, *, project_id: int, payload: schema.RoadmapItemCreate
    ) -> EntRoadmapItem:
        data = payload.model_dump()
        sequence = data.pop("sequence", None)
        attachments = data.pop("attachments", [])
        metadata = data.pop("metadata", {})
        item = EntRoadmapItem(
            project_id=project_id,
            attachments=list(attachments or []),
            metadata=dict(metadata or {}),
            **data,
        )
        item.sequence = await self._next_sequence(project_id)
        self.session.add(item)
        await self.session.flush()

        if sequence is not None:
            await self._move_roadmap_sequence(project_id, item.id, sequence)
        await self.session.refresh(item)
        return item

    async def update_roadmap_item(
        self,
        *,
        project_id: int,
        item_id: int,
        payload: schema.RoadmapItemUpdate,
    ) -> EntRoadmapItem:
        item = await self._get_roadmap_item(project_id, item_id)
        data = payload.model_dump(exclude_unset=True)
        sequence = data.pop("sequence", None)

        for field, value in data.items():
            if field == "attachments" and value is not None:
                item.attachments = list(value)
            elif field == "metadata" and value is not None:
                item.metadata = dict(value)
            elif field == "approval_type_id" and value is not None:
                item.approval_type_id = value
            elif value is not None:
                setattr(item, field, value)

        item.updated_at = _utcnow()
        await self.session.flush()

        if sequence is not None:
            await self._move_roadmap_sequence(project_id, item.id, sequence)
        await self.session.refresh(item)
        return item

    async def delete_roadmap_item(self, *, project_id: int, item_id: int) -> None:
        item = await self._get_roadmap_item(project_id, item_id)
        await self.session.delete(item)
        await self.session.flush()
        await self._resequence(project_id)

    async def _get_roadmap_item(
        self, project_id: int, item_id: int
    ) -> EntRoadmapItem:
        stmt = (
            select(EntRoadmapItem)
            .options(selectinload(EntRoadmapItem.approval_type))
            .where(EntRoadmapItem.project_id == project_id)
            .where(EntRoadmapItem.id == item_id)
            .limit(1)
        )
        item = (await self.session.execute(stmt)).scalar_one_or_none()
        if not item:
            raise EntitlementNotFoundError("Roadmap item not found")
        return item

    async def _next_sequence(self, project_id: int) -> int:
        stmt = select(func.max(EntRoadmapItem.sequence)).where(
            EntRoadmapItem.project_id == project_id
        )
        result = (await self.session.execute(stmt)).scalar_one_or_none()
        if result is None:
            return 1
        return int(result) + 1

    async def _move_roadmap_sequence(
        self, project_id: int, item_id: int, target_sequence: int
    ) -> None:
        items = await self._load_roadmap_items(project_id)
        target_index = max(0, min(len(items) - 1, target_sequence - 1))
        positions = [item for item in items if item.id != item_id]
        moving = next((item for item in items if item.id == item_id), None)
        if moving is None:
            raise EntitlementNotFoundError("Roadmap item not found")
        positions.insert(target_index, moving)
        await self._apply_sequence_order(project_id, positions)

    async def _resequence(self, project_id: int) -> None:
        items = await self._load_roadmap_items(project_id)
        await self._apply_sequence_order(project_id, items)

    async def _load_roadmap_items(self, project_id: int) -> List[EntRoadmapItem]:
        stmt = (
            select(EntRoadmapItem)
            .where(EntRoadmapItem.project_id == project_id)
            .order_by(EntRoadmapItem.sequence, EntRoadmapItem.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _apply_sequence_order(
        self, project_id: int, ordered_items: Iterable[EntRoadmapItem]
    ) -> None:
        for index, item in enumerate(ordered_items, start=1):
            new_sequence = max(1, index)
            if item.sequence != new_sequence or item.project_id != project_id:
                item.sequence = new_sequence
                item.project_id = project_id
                item.updated_at = _utcnow()
        await self.session.flush()

    # ------------------------------------------------------------------
    # Studies
    # ------------------------------------------------------------------
    async def list_studies(
        self, *, project_id: int, limit: int = 50, offset: int = 0
    ) -> PaginatedResult:
        stmt = (
            select(EntStudy)
            .where(EntStudy.project_id == project_id)
            .order_by(EntStudy.submission_date.is_(None), EntStudy.submission_date, EntStudy.id)
        )
        result = await self.session.execute(_paginate_statement(stmt, limit=limit, offset=offset))
        items = list(result.scalars().all())

        total = await self._count_for_project(EntStudy, project_id)
        return PaginatedResult(items=items, total=total)

    async def create_study(
        self, *, project_id: int, payload: schema.StudyCreate
    ) -> EntStudy:
        data = payload.model_dump()
        study = EntStudy(
            project_id=project_id,
            findings=dict(data.pop("findings", {})),
            metadata=dict(data.pop("metadata", {})),
            **data,
        )
        self.session.add(study)
        await self.session.flush()
        await self.session.refresh(study)
        return study

    async def update_study(
        self,
        *,
        project_id: int,
        study_id: int,
        payload: schema.StudyUpdate,
    ) -> EntStudy:
        study = await self._get_study(project_id, study_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            if field in {"findings", "metadata"} and value is not None:
                setattr(study, field, dict(value))
            elif value is not None:
                setattr(study, field, value)
        study.updated_at = _utcnow()
        await self.session.flush()
        await self.session.refresh(study)
        return study

    async def delete_study(self, *, project_id: int, study_id: int) -> None:
        study = await self._get_study(project_id, study_id)
        await self.session.delete(study)
        await self.session.flush()

    async def _get_study(self, project_id: int, study_id: int) -> EntStudy:
        stmt = (
            select(EntStudy)
            .where(EntStudy.project_id == project_id)
            .where(EntStudy.id == study_id)
            .limit(1)
        )
        study = (await self.session.execute(stmt)).scalar_one_or_none()
        if not study:
            raise EntitlementNotFoundError("Study not found")
        return study

    # ------------------------------------------------------------------
    # Stakeholder engagements
    # ------------------------------------------------------------------
    async def list_stakeholders(
        self, *, project_id: int, limit: int = 50, offset: int = 0
    ) -> PaginatedResult:
        stmt = (
            select(EntEngagement)
            .where(EntEngagement.project_id == project_id)
            .order_by(EntEngagement.meeting_date.is_(None), EntEngagement.meeting_date, EntEngagement.id)
        )
        result = await self.session.execute(_paginate_statement(stmt, limit=limit, offset=offset))
        items = list(result.scalars().all())

        total = await self._count_for_project(EntEngagement, project_id)
        return PaginatedResult(items=items, total=total)

    async def create_stakeholder(
        self, *, project_id: int, payload: schema.StakeholderCreate
    ) -> EntEngagement:
        data = payload.model_dump()
        engagement = EntEngagement(
            project_id=project_id,
            next_steps=list(data.pop("next_steps", [])),
            metadata=dict(data.pop("metadata", {})),
            **data,
        )
        self.session.add(engagement)
        await self.session.flush()
        await self.session.refresh(engagement)
        return engagement

    async def update_stakeholder(
        self,
        *,
        project_id: int,
        stakeholder_id: int,
        payload: schema.StakeholderUpdate,
    ) -> EntEngagement:
        engagement = await self._get_stakeholder(project_id, stakeholder_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            if field == "next_steps" and value is not None:
                engagement.next_steps = list(value)
            elif field == "metadata" and value is not None:
                engagement.metadata = dict(value)
            elif value is not None:
                setattr(engagement, field, value)
        engagement.updated_at = _utcnow()
        await self.session.flush()
        await self.session.refresh(engagement)
        return engagement

    async def delete_stakeholder(
        self, *, project_id: int, stakeholder_id: int
    ) -> None:
        engagement = await self._get_stakeholder(project_id, stakeholder_id)
        await self.session.delete(engagement)
        await self.session.flush()

    async def _get_stakeholder(
        self, project_id: int, stakeholder_id: int
    ) -> EntEngagement:
        stmt = (
            select(EntEngagement)
            .where(EntEngagement.project_id == project_id)
            .where(EntEngagement.id == stakeholder_id)
            .limit(1)
        )
        engagement = (await self.session.execute(stmt)).scalar_one_or_none()
        if not engagement:
            raise EntitlementNotFoundError("Stakeholder engagement not found")
        return engagement

    # ------------------------------------------------------------------
    # Legal instruments
    # ------------------------------------------------------------------
    async def list_legal_instruments(
        self, *, project_id: int, limit: int = 50, offset: int = 0
    ) -> PaginatedResult:
        stmt = (
            select(EntLegalInstrument)
            .where(EntLegalInstrument.project_id == project_id)
            .order_by(EntLegalInstrument.effective_date.is_(None), EntLegalInstrument.effective_date, EntLegalInstrument.id)
        )
        result = await self.session.execute(_paginate_statement(stmt, limit=limit, offset=offset))
        items = list(result.scalars().all())

        total = await self._count_for_project(EntLegalInstrument, project_id)
        return PaginatedResult(items=items, total=total)

    async def create_legal_instrument(
        self, *, project_id: int, payload: schema.LegalInstrumentCreate
    ) -> EntLegalInstrument:
        data = payload.model_dump()
        instrument = EntLegalInstrument(
            project_id=project_id,
            attachments=list(data.pop("attachments", [])),
            metadata=dict(data.pop("metadata", {})),
            **data,
        )
        self.session.add(instrument)
        await self.session.flush()
        await self.session.refresh(instrument)
        return instrument

    async def update_legal_instrument(
        self,
        *,
        project_id: int,
        instrument_id: int,
        payload: schema.LegalInstrumentUpdate,
    ) -> EntLegalInstrument:
        instrument = await self._get_legal(project_id, instrument_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            if field == "attachments" and value is not None:
                instrument.attachments = list(value)
            elif field == "metadata" and value is not None:
                instrument.metadata = dict(value)
            elif value is not None:
                setattr(instrument, field, value)
        instrument.updated_at = _utcnow()
        await self.session.flush()
        await self.session.refresh(instrument)
        return instrument

    async def delete_legal_instrument(
        self, *, project_id: int, instrument_id: int
    ) -> None:
        instrument = await self._get_legal(project_id, instrument_id)
        await self.session.delete(instrument)
        await self.session.flush()

    async def _get_legal(
        self, project_id: int, instrument_id: int
    ) -> EntLegalInstrument:
        stmt = (
            select(EntLegalInstrument)
            .where(EntLegalInstrument.project_id == project_id)
            .where(EntLegalInstrument.id == instrument_id)
            .limit(1)
        )
        instrument = (await self.session.execute(stmt)).scalar_one_or_none()
        if not instrument:
            raise EntitlementNotFoundError("Legal instrument not found")
        return instrument

    # ------------------------------------------------------------------
    # Utility helpers for exports
    # ------------------------------------------------------------------
    async def snapshot_project(
        self, project_id: int
    ) -> Tuple[
        List[EntAuthority],
        List[EntApprovalType],
        List[EntRoadmapItem],
        List[EntStudy],
        List[EntEngagement],
        List[EntLegalInstrument],
    ]:
        authorities = await self.list_authorities()
        approvals = await self.list_approval_types()
        roadmap_stmt = (
            select(EntRoadmapItem)
            .options(selectinload(EntRoadmapItem.approval_type))
            .where(EntRoadmapItem.project_id == project_id)
            .order_by(EntRoadmapItem.sequence, EntRoadmapItem.id)
        )
        roadmap = list((await self.session.execute(roadmap_stmt)).scalars().unique().all())

        studies = await self._collect_for_project(EntStudy, project_id)
        stakeholders = await self._collect_for_project(EntEngagement, project_id)
        legal = await self._collect_for_project(EntLegalInstrument, project_id)
        return authorities, approvals, roadmap, studies, stakeholders, legal

    async def _collect_for_project(self, model, project_id: int) -> List[object]:
        stmt = select(model).where(model.project_id == project_id).order_by(model.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _count_for_project(self, model, project_id: int) -> int:
        stmt = select(model).where(model.project_id == project_id)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())


__all__ = [
    "EntitlementNotFoundError",
    "EntitlementsService",
    "PaginatedResult",
]
