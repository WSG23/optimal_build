"""Security dashboard endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.security import (
    SecurityOverviewResponse,
    SecurityTicketResponse,
    SecurityTicketUpdate,
)
from app.services.security import SecurityDashboardService

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/overview", response_model=SecurityOverviewResponse)
async def get_security_overview(
    project_id: UUID | None = None,
    db: AsyncSession = Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_viewer),
) -> SecurityOverviewResponse:
    """Return facility label, tickets, and threat score for the dashboard."""
    service = SecurityDashboardService(db)
    return await service.get_overview(identity, project_id)


@router.patch("/tickets/{ticket_id}", response_model=SecurityTicketResponse)
async def update_security_ticket(
    ticket_id: UUID,
    payload: SecurityTicketUpdate,
    db: AsyncSession = Depends(deps.get_db),
    identity: deps.RequestIdentity = Depends(deps.require_reviewer),
) -> SecurityTicketResponse:
    """Update ticket status from the dashboard."""
    service = SecurityDashboardService(db)
    try:
        ticket = await service.update_ticket_status(ticket_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SecurityTicketResponse.model_validate(ticket)
