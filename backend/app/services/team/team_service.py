"""Service for managing project teams and invitations."""

import secrets
from datetime import timedelta
from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.team import InvitationStatus, TeamInvitation, TeamMember
from app.models.users import UserRole

# from app.services.base import BaseService # Removed
from sqlalchemy import select
from sqlalchemy.orm import joinedload


class TeamService:
    """Service for managing team members and invitations."""

    def __init__(self, db_session):
        self.db = db_session

    async def get_team_members(self, project_id: UUID) -> list[TeamMember]:
        """List all members of a project team."""
        query = (
            select(TeamMember)
            .options(joinedload(TeamMember.user))
            .where(TeamMember.project_id == project_id)
            .where(TeamMember.is_active.is_(True))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def invite_member(
        self,
        project_id: UUID,
        email: str,
        role: UserRole,
        invited_by_id: UUID,
        expires_in_days: int = 7,
    ) -> TeamInvitation:
        """Create and send an invitation to join the team."""

        # Check if user is already a member
        # (This logic would need User lookup, but we invite by email)
        # We can implement a check if we want strict uniqueness.

        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = utcnow() + timedelta(days=expires_in_days)

        invitation = TeamInvitation(
            project_id=project_id,
            email=email,
            role=role,
            token=token,
            status=InvitationStatus.PENDING,
            invited_by_id=invited_by_id,
            expires_at=expires_at,
        )

        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        # TODO: Send email
        # email_service.send_invite(email, token, project_id)

        return invitation

    async def accept_invitation(self, token: str, user_id: UUID) -> TeamMember:
        """Accept an invitation and add user to the team."""

        query = select(TeamInvitation).where(TeamInvitation.token == token)
        result = await self.db.execute(query)
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise ValueError("Invalid invitation token")

        if not invitation.is_valid():
            raise ValueError("Invitation is expired or invalid")

        # Verify user matches email?
        # Ideally yes, but user might register with the invite email.
        # For now, we assume the user accepting has possession of the token.

        # Create membership
        member = TeamMember(
            project_id=invitation.project_id,
            user_id=user_id,
            role=invitation.role,
        )
        self.db.add(member)

        # Update invitation
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = utcnow()
        self.db.add(invitation)

        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, project_id: UUID, user_id: UUID) -> bool:
        """Remove a user from the project team."""
        query = select(TeamMember).where(
            TeamMember.project_id == project_id, TeamMember.user_id == user_id
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if member:
            member.is_active = False  # Soft delete/deactivate
            self.db.add(member)
            await self.db.commit()
            return True
        return False
