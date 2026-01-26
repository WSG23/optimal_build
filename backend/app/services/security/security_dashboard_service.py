"""Security dashboard aggregation service."""

from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.project import Project
from app.models.security import SecurityTicket, SecurityTicketStatus
from app.models.user import User
from app.schemas.security import SecurityOverviewResponse, ThreatData


class SecurityDashboardService:
    """Aggregate security tickets and threat metrics for the dashboard."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get_overview(
        self, identity: deps.RequestIdentity, project_id: uuid.UUID | None
    ) -> SecurityOverviewResponse:
        project = await self._resolve_project(identity, project_id)
        facility_label = await self._resolve_facility_label(identity, project)
        resolved_project_id = project.id if project else None
        tickets = await self._list_tickets(resolved_project_id)
        threat = self._build_threat_data(tickets, resolved_project_id, identity)
        return SecurityOverviewResponse(
            facility_label=facility_label,
            project_id=resolved_project_id,
            tickets=tickets,
            threat=threat,
        )

    async def update_ticket_status(
        self, ticket_id: uuid.UUID, status: SecurityTicketStatus
    ) -> SecurityTicket:
        ticket = await self.db.get(SecurityTicket, ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")
        ticket.status = status
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def _resolve_project(
        self, identity: deps.RequestIdentity, project_id: uuid.UUID | None
    ) -> Project | None:
        if project_id:
            return await self.db.get(Project, project_id)

        user_uuid = self._safe_uuid(identity.user_id)
        if user_uuid:
            query = (
                select(Project)
                .where(Project.owner_id == user_uuid)
                .order_by(desc(Project.updated_at))
            )
            result = await self.db.execute(query)
            project = result.scalars().first()
            if project:
                return project

        if identity.email:
            query = (
                select(Project)
                .where(Project.owner_email == identity.email)
                .order_by(desc(Project.updated_at))
            )
            result = await self.db.execute(query)
            return result.scalars().first()

        return None

    async def _resolve_facility_label(
        self, identity: deps.RequestIdentity, project: Project | None
    ) -> str | None:
        if project and project.project_name:
            return project.project_name

        user = await self._resolve_user(identity)
        if user:
            for candidate in (
                user.company_name,
                user.full_name,
                user.username,
                user.email,
            ):
                if candidate and candidate.strip():
                    return candidate.strip()

        if identity.email:
            return identity.email
        return None

    async def _resolve_user(self, identity: deps.RequestIdentity) -> User | None:
        user_uuid = self._safe_uuid(identity.user_id)
        if user_uuid:
            user = await self.db.get(User, user_uuid)
            if user:
                return user

        if identity.email:
            query = select(User).where(User.email == identity.email)
            result = await self.db.execute(query)
            return result.scalars().first()

        return None

    async def _list_tickets(self, project_id: uuid.UUID | None) -> list[SecurityTicket]:
        if not project_id:
            return []
        query = (
            select(SecurityTicket)
            .where(SecurityTicket.project_id == project_id)
            .order_by(desc(SecurityTicket.created_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    def _build_threat_data(
        tickets: Iterable[SecurityTicket],
        project_id: uuid.UUID | None,
        identity: deps.RequestIdentity,
    ) -> ThreatData:
        weights = {
            SecurityTicketStatus.OPEN: 18,
            SecurityTicketStatus.LOCKED: 12,
            SecurityTicketStatus.RESOLVED_HARMFUL: 8,
            SecurityTicketStatus.RESOLVED_MALFUNCTION: 4,
            SecurityTicketStatus.RESOLVED_NORMAL: 2,
            SecurityTicketStatus.DISMISSED: 0,
        }
        score = 0
        for ticket in tickets:
            status = ticket.status
            if isinstance(status, str):
                try:
                    status = SecurityTicketStatus(status)
                except ValueError:
                    status = None
            score += weights.get(status, 0)
        score = min(100, max(0, score))

        entity_id = None
        if project_id:
            entity_id = str(project_id)
        elif identity.user_id:
            entity_id = identity.user_id
        elif identity.email:
            entity_id = identity.email

        return ThreatData(entity_id=entity_id, headline_score=score)

    @staticmethod
    def _safe_uuid(value: str | None) -> uuid.UUID | None:
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError):
            return None
