"""Service for managing project teams and invitations."""

import secrets
from datetime import timedelta
from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.projects import Project
from app.models.team import InvitationStatus, TeamInvitation, TeamMember
from app.models.users import User, UserRole
from app.services.notification import EmailService, NotificationService

# from app.services.base import BaseService # Removed
from sqlalchemy import select
from sqlalchemy.orm import joinedload


class TeamService:
    """Service for managing team members and invitations."""

    def __init__(self, db_session):
        self.db = db_session
        self.notifications = NotificationService(db_session)
        self.emails = EmailService()

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

        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        inviter_result = await self.db.execute(
            select(User).where(User.id == invited_by_id)
        )
        inviter = inviter_result.scalar_one_or_none()

        inviter_name = inviter.full_name if inviter else "A teammate"
        project_name = project.project_name if project else "a project"

        # In-app notification (only if the invited email already has a user account).
        invitee_result = await self.db.execute(select(User).where(User.email == email))
        invitee = invitee_result.scalar_one_or_none()
        if invitee and project:
            await self.notifications.notify_team_invite(
                user_id=invitee.id,
                project_name=project_name,
                inviter_name=inviter_name,
                project_id=project_id,
            )

        # Email delivery (no paid services required; disabled by default).
        subject = f"Invitation to join {project_name}"
        email_log = await self.notifications.log_email(
            recipient_email=email,
            subject=subject,
            template_name="team_invitation",
            notification_id=None,
        )
        sent = self.emails.send_team_invitation(
            to_email=email,
            inviter_name=inviter_name,
            project_name=project_name,
            role=str(role.value if hasattr(role, "value") else role),
            invitation_token=token,
        )
        await self.notifications.update_email_log_status(
            email_log_id=email_log.id,
            status="sent" if sent else "failed",
            error_message=None if sent else "Email send failed",
        )

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
