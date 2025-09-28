"""Service layer for entitlement workflows."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entitlements import (
    EntApprovalType,
    EntAuthority,
    EntEngagement,
    EntEngagementStatus,
    EntLegalInstrument,
    EntRoadmapItem,
    EntStudy,
)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def _normalise_limit(limit: int | None) -> int:
    """Clamp user supplied limits to reasonable bounds."""

    if limit is None or limit <= 0:
        return DEFAULT_PAGE_SIZE
    return min(limit, MAX_PAGE_SIZE)


def _normalise_offset(offset: int | None) -> int:
    if offset is None or offset < 0:
        return 0
    return offset


@dataclass(slots=True)
class PageResult:
    """Result bundle containing records and total count."""

    items: Sequence
    total: int


class EntitlementsService:
    """Encapsulates entitlement persistence concerns."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_authorities(
        self, *, jurisdiction: str | None = None
    ) -> list[EntAuthority]:
        stmt = select(EntAuthority).order_by(EntAuthority.name)
        if jurisdiction:
            stmt = stmt.where(EntAuthority.jurisdiction == jurisdiction)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique())

    async def get_authority_by_slug(self, slug: str) -> EntAuthority | None:
        stmt = select(EntAuthority).where(EntAuthority.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert_authority(
        self,
        *,
        jurisdiction: str,
        name: str,
        slug: str,
        website: str | None = None,
        contact_email: str | None = None,
        metadata: dict | None = None,
    ) -> EntAuthority:
        authority = await self.get_authority_by_slug(slug)
        if authority is None:
            authority = EntAuthority(
                jurisdiction=jurisdiction,
                name=name,
                slug=slug,
                website=website,
                contact_email=contact_email,
                metadata=metadata or {},
            )
            self.session.add(authority)
        else:
            authority.jurisdiction = jurisdiction
            authority.name = name
            authority.website = website
            authority.contact_email = contact_email
            if metadata is not None:
                authority.metadata = metadata
        await self.session.flush()
        return authority

    async def get_approval_type(
        self, *, authority_id: int, code: str
    ) -> EntApprovalType | None:
        stmt = select(EntApprovalType).where(
            EntApprovalType.authority_id == authority_id,
            EntApprovalType.code == code,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert_approval_type(
        self,
        *,
        authority: EntAuthority,
        code: str,
        name: str,
        category,
        description: str | None = None,
        requirements: dict | None = None,
        processing_time_days: int | None = None,
        is_mandatory: bool | None = None,
        metadata: dict | None = None,
    ) -> EntApprovalType:
        approval_type = await self.get_approval_type(
            authority_id=authority.id, code=code
        )
        if approval_type is None:
            approval_type = EntApprovalType(
                authority_id=authority.id,
                code=code,
                name=name,
                category=category,
                description=description,
                requirements=requirements or {},
                processing_time_days=processing_time_days,
                is_mandatory=is_mandatory if is_mandatory is not None else True,
                metadata=metadata or {},
            )
            self.session.add(approval_type)
        else:
            approval_type.authority_id = authority.id
            approval_type.name = name
            approval_type.category = category
            approval_type.description = description
            approval_type.processing_time_days = processing_time_days
            if requirements is not None:
                approval_type.requirements = requirements
            if is_mandatory is not None:
                approval_type.is_mandatory = is_mandatory
            if metadata is not None:
                approval_type.metadata = metadata
        await self.session.flush()
        return approval_type

    async def list_approval_types(self, *, authority_id: int) -> list[EntApprovalType]:
        stmt = (
            select(EntApprovalType)
            .where(EntApprovalType.authority_id == authority_id)
            .order_by(EntApprovalType.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique())

    async def list_roadmap_items(
        self,
        *,
        project_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PageResult:
        limit_value = _normalise_limit(limit)
        offset_value = _normalise_offset(offset)
        items = await self._load_full_roadmap(project_id)
        total = len(items)
        page_items = items[offset_value : offset_value + limit_value]
        return PageResult(items=page_items, total=total)

    async def _load_full_roadmap(self, project_id: int) -> list[EntRoadmapItem]:
        stmt = (
            select(EntRoadmapItem)
            .options(selectinload(EntRoadmapItem.approval_type))
            .where(EntRoadmapItem.project_id == project_id)
            .order_by(EntRoadmapItem.sequence_order, EntRoadmapItem.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique())

    async def all_roadmap_items(self, project_id: int) -> list[EntRoadmapItem]:
        """Return the full ordered roadmap for export routines."""

        return await self._load_full_roadmap(project_id)

    @staticmethod
    def _reindex(items: Iterable[EntRoadmapItem]) -> None:
        for index, item in enumerate(items, start=1):
            item.sequence_order = index

    async def create_roadmap_item(
        self,
        *,
        project_id: int,
        approval_type_id: int | None,
        sequence_order: int | None,
        status,
        status_changed_at: datetime | None,
        target_submission_date,
        target_decision_date,
        actual_submission_date,
        actual_decision_date,
        notes: str | None,
        metadata: dict | None,
    ) -> EntRoadmapItem:
        existing = await self._load_full_roadmap(project_id)
        insert_index = len(existing)
        if sequence_order is not None and sequence_order > 0:
            insert_index = min(sequence_order - 1, len(existing))

        item = EntRoadmapItem(
            project_id=project_id,
            approval_type_id=approval_type_id,
            sequence_order=insert_index + 1,
            status=status,
            status_changed_at=status_changed_at,
            target_submission_date=target_submission_date,
            target_decision_date=target_decision_date,
            actual_submission_date=actual_submission_date,
            actual_decision_date=actual_decision_date,
            notes=notes,
            metadata=metadata or {},
        )

        existing.insert(insert_index, item)
        self._reindex(existing)
        self.session.add(item)
        await self.session.flush()
        return item

    async def update_roadmap_item(
        self,
        *,
        item_id: int,
        project_id: int,
        **updates: Any,
    ) -> EntRoadmapItem:
        items = await self._load_full_roadmap(project_id)
        target = next((entry for entry in items if entry.id == item_id), None)
        if target is None:
            raise ValueError(
                f"Roadmap item {item_id} not found for project {project_id}"
            )

        if "approval_type_id" in updates:
            target.approval_type_id = updates["approval_type_id"]
        if "notes" in updates:
            target.notes = updates["notes"]
        if "metadata" in updates:
            target.metadata = updates["metadata"]
        if "target_submission_date" in updates:
            target.target_submission_date = updates["target_submission_date"]
        if "target_decision_date" in updates:
            target.target_decision_date = updates["target_decision_date"]
        if "actual_submission_date" in updates:
            target.actual_submission_date = updates["actual_submission_date"]
        if "actual_decision_date" in updates:
            target.actual_decision_date = updates["actual_decision_date"]
        if "status" in updates:
            new_status = updates["status"]
            if new_status is not None and target.status != new_status:
                target.status = new_status
                target.status_changed_at = datetime.now(UTC)

        if "sequence_order" in updates:
            sequence_order = updates["sequence_order"]
            if sequence_order is not None and sequence_order > 0:
                items = [entry for entry in items if entry.id != target.id]
                insert_index = min(sequence_order - 1, len(items))
                items.insert(insert_index, target)
                self._reindex(items)

        await self.session.flush()
        return target

    async def delete_roadmap_item(self, *, item_id: int, project_id: int) -> None:
        items = await self._load_full_roadmap(project_id)
        target = next((entry for entry in items if entry.id == item_id), None)
        if target is None:
            return
        items = [entry for entry in items if entry.id != item_id]
        self._reindex(items)
        await self.session.delete(target)
        await self.session.flush()

    async def list_studies(
        self,
        *,
        project_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PageResult:
        limit_value = _normalise_limit(limit)
        offset_value = _normalise_offset(offset)
        base_stmt = (
            select(EntStudy)
            .where(EntStudy.project_id == project_id)
            .order_by(EntStudy.created_at.desc())
        )
        result = await self.session.execute(base_stmt)
        all_items = list(result.scalars().unique())
        total = len(all_items)
        page_items = all_items[offset_value : offset_value + limit_value]
        return PageResult(items=page_items, total=total)

    async def create_study(self, **kwargs) -> EntStudy:
        record = EntStudy(**kwargs)
        self.session.add(record)
        await self.session.flush()
        return record

    async def update_study(
        self,
        *,
        study_id: int,
        project_id: int,
        **updates,
    ) -> EntStudy:
        stmt = select(EntStudy).where(
            EntStudy.id == study_id, EntStudy.project_id == project_id
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record is None:
            raise ValueError(f"Study {study_id} not found for project {project_id}")
        for key, value in updates.items():
            setattr(record, key, value)
        await self.session.flush()
        return record

    async def delete_study(self, *, study_id: int, project_id: int) -> None:
        stmt = select(EntStudy).where(
            EntStudy.id == study_id, EntStudy.project_id == project_id
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record is None:
            return
        await self.session.delete(record)
        await self.session.flush()

    async def list_engagements(
        self,
        *,
        project_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PageResult:
        limit_value = _normalise_limit(limit)
        offset_value = _normalise_offset(offset)
        base_stmt = (
            select(EntEngagement)
            .where(EntEngagement.project_id == project_id)
            .order_by(EntEngagement.created_at.desc())
        )
        result = await self.session.execute(base_stmt)
        all_items = list(result.scalars().unique())
        total = len(all_items)
        page_items = all_items[offset_value : offset_value + limit_value]
        return PageResult(items=page_items, total=total)

    async def create_engagement(self, **kwargs) -> EntEngagement:
        record = EntEngagement(**kwargs)
        if record.status == EntEngagementStatus.ACTIVE and not record.meetings:
            record.meetings = []
        self.session.add(record)
        await self.session.flush()
        return record

    async def update_engagement(
        self,
        *,
        engagement_id: int,
        project_id: int,
        **updates,
    ) -> EntEngagement:
        stmt = select(EntEngagement).where(
            EntEngagement.id == engagement_id,
            EntEngagement.project_id == project_id,
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record is None:
            raise ValueError(
                f"Engagement {engagement_id} not found for project {project_id}"
            )
        for key, value in updates.items():
            setattr(record, key, value)
        await self.session.flush()
        return record

    async def delete_engagement(self, *, engagement_id: int, project_id: int) -> None:
        stmt = select(EntEngagement).where(
            EntEngagement.id == engagement_id,
            EntEngagement.project_id == project_id,
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record is None:
            return
        await self.session.delete(record)
        await self.session.flush()

    async def list_legal_instruments(
        self,
        *,
        project_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PageResult:
        limit_value = _normalise_limit(limit)
        offset_value = _normalise_offset(offset)
        base_stmt = (
            select(EntLegalInstrument)
            .where(EntLegalInstrument.project_id == project_id)
            .order_by(EntLegalInstrument.created_at.desc())
        )
        result = await self.session.execute(base_stmt)
        all_items = list(result.scalars().unique())
        total = len(all_items)
        page_items = all_items[offset_value : offset_value + limit_value]
        return PageResult(items=page_items, total=total)

    async def create_legal_instrument(self, **kwargs) -> EntLegalInstrument:
        record = EntLegalInstrument(**kwargs)
        self.session.add(record)
        await self.session.flush()
        return record

    async def update_legal_instrument(
        self,
        *,
        instrument_id: int,
        project_id: int,
        **updates,
    ) -> EntLegalInstrument:
        stmt = select(EntLegalInstrument).where(
            EntLegalInstrument.id == instrument_id,
            EntLegalInstrument.project_id == project_id,
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record is None:
            raise ValueError(
                f"Legal instrument {instrument_id} not found for project {project_id}"
            )
        for key, value in updates.items():
            setattr(record, key, value)
        await self.session.flush()
        return record

    async def delete_legal_instrument(
        self,
        *,
        instrument_id: int,
        project_id: int,
    ) -> None:
        stmt = select(EntLegalInstrument).where(
            EntLegalInstrument.id == instrument_id,
            EntLegalInstrument.project_id == project_id,
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record is None:
            return
        await self.session.delete(record)
        await self.session.flush()


__all__ = ["EntitlementsService", "PageResult"]
