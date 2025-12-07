"""Construction finance service for Phase 2G.

Handles:
- Drawdown requests (Construction Loan)
- Progress payments
- Budget reconciliation (Future integration)
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.construction import DrawdownRequest, DrawdownStatus
from app.schemas.construction import DrawdownRequestCreate, DrawdownRequestUpdate


class ConstructionFinanceService:
    """Service for managing construction finance and drawdowns."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_drawdown_request(
        self, payload: DrawdownRequestCreate
    ) -> DrawdownRequest:
        """Submit a new drawdown request."""
        request = DrawdownRequest(**payload.model_dump())
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def get_drawdown_requests(
        self, project_id: UUID, status: Optional[DrawdownStatus] = None
    ) -> List[DrawdownRequest]:
        """List drawdown requests for a project."""
        query = select(DrawdownRequest).where(DrawdownRequest.project_id == project_id)
        if status:
            query = query.where(DrawdownRequest.status == status)

        # Eager load contractor
        query = query.options(selectinload(DrawdownRequest.contractor))
        query = query.order_by(desc(DrawdownRequest.request_date))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_drawdown_request(self, request_id: UUID) -> Optional[DrawdownRequest]:
        """Get drawdown request by ID."""
        query = (
            select(DrawdownRequest)
            .where(DrawdownRequest.id == request_id)
            .options(selectinload(DrawdownRequest.contractor))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_drawdown_request(
        self, request_id: UUID, payload: DrawdownRequestUpdate
    ) -> Optional[DrawdownRequest]:
        """Update a drawdown request."""
        request = await self.get_drawdown_request(request_id)
        if not request:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(request, key, value)

        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def approve_drawdown(
        self, request_id: UUID, approved_amount: Optional[float] = None
    ) -> Optional[DrawdownRequest]:
        """Quick approval workflow step (e.g. Architect Approval)."""
        request = await self.get_drawdown_request(request_id)
        if not request:
            return None

        # Simple workflow: Draft -> Submitted -> Approved Architect -> ...
        # For this MVP, we just set to Approved Architect if it's Submitted
        if request.status == DrawdownStatus.SUBMITTED:
            request.status = DrawdownStatus.APPROVED_ARCHITECT
            if approved_amount is not None:
                request.amount_approved = approved_amount
            else:
                request.amount_approved = request.amount_requested

        await self.session.commit()
        await self.session.refresh(request)
        return request
