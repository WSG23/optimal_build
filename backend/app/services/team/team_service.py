"""Service for managing project teams and invitations."""

import secrets
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.team import InvitationStatus, TeamInvitation, TeamMember
from app.models.users import User, UserRole
from sqlalchemy import select
from sqlalchemy.orm import joinedload

if TYPE_CHECKING:
    from app.services.notification import NotificationService


class TeamService:
    """Service for managing team members and invitations."""

    def __init__(
        self,
        db_session,
        notification_service: Optional["NotificationService"] = None,
    ):
        self.db = db_session
        self.notification_service = notification_service

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

        query = (
            select(TeamInvitation)
            .options(joinedload(TeamInvitation.project))
            .where(TeamInvitation.token == token)
        )
        result = await self.db.execute(query)
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise ValueError("Invalid invitation token")

        if not invitation.is_valid():
            raise ValueError("Invitation is expired or invalid")

        # Get the user accepting the invitation
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        accepting_user = user_result.scalar_one_or_none()

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

        # Send notifications to existing team members about new member
        if self.notification_service and accepting_user:
            await self._notify_team_member_joined(
                project_id=invitation.project_id,
                project_name=(
                    invitation.project.project_name
                    if invitation.project
                    else "Unknown Project"
                ),
                new_member_name=accepting_user.full_name,
                new_member_id=user_id,
            )

        return member

    async def _notify_team_member_joined(
        self,
        project_id: UUID,
        project_name: str,
        new_member_name: str,
        new_member_id: UUID,
    ) -> None:
        """Notify existing team members when a new member joins."""
        if not self.notification_service:
            return

        # Get all active team members except the new one
        members = await self.get_team_members(project_id)
        for member in members:
            if member.user_id != new_member_id:
                await self.notification_service.notify_team_member_joined(
                    user_id=member.user_id,
                    project_id=project_id,
                    project_name=project_name,
                    new_member_name=new_member_name,
                )

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
