"""Tests ensuring entitlement enums persist lowercase values."""

from __future__ import annotations

from uuid import uuid4

import pytest

import sqlalchemy as sa
from app.models.entitlements import (
    EntApprovalCategory,
    EntApprovalType,
    EntAuthority,
    EntRoadmapItem,
    EntRoadmapStatus,
)
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def _create_authority(session: AsyncSession) -> EntAuthority:
    authority = EntAuthority(
        jurisdiction="SG",
        name="Urban Redevelopment Authority",
        slug=f"ura-{uuid4().hex[:6]}",
    )
    session.add(authority)
    await session.flush()
    return authority


class TestEntitlementEnums:
    """Validate that SAEnum columns use lowercase `.value` storage."""

    async def test_ent_approval_category_stores_lowercase(self, session: AsyncSession):
        authority = await _create_authority(session)
        approval = EntApprovalType(
            authority_id=authority.id,
            code="URA-PLAN",
            name="Planning Approval",
            category=EntApprovalCategory.PLANNING,
        )
        session.add(approval)
        await session.commit()
        await session.refresh(approval)

        assert approval.category == EntApprovalCategory.PLANNING

        stored_value = await session.execute(
            sa.select(sa.cast(EntApprovalType.category, sa.String)).where(
                EntApprovalType.id == approval.id
            )
        )
        assert stored_value.scalar_one() == "planning"

    async def test_ent_roadmap_status_stores_lowercase(self, session: AsyncSession):
        roadmap_item = EntRoadmapItem(
            project_id=401,
            sequence_order=1,
            status=EntRoadmapStatus.IN_PROGRESS,
        )
        session.add(roadmap_item)
        await session.commit()
        await session.refresh(roadmap_item)

        assert roadmap_item.status == EntRoadmapStatus.IN_PROGRESS

        stored_value = await session.execute(
            sa.select(sa.cast(EntRoadmapItem.status, sa.String)).where(
                EntRoadmapItem.id == roadmap_item.id
            )
        )
        assert stored_value.scalar_one() == "in_progress"
