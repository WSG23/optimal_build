"""Service for managing project teams and invitations."""

import logging
import secrets
from datetime import timedelta
from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.team import InvitationStatus, TeamInvitation, TeamMember
from app.models.users import UserRole
from app.services.notification.email_service import EmailService

from sqlalchemy import select
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class TeamService:
    """Service for managing team members and invitations."""

    def __init__(self, db_session, email_service: EmailService | None = None):
        self.db = db_session
        self.email_service = email_service or EmailService()

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

        # Send invitation email
        try:
            # Get project name for the email
            from app.models.projects import Project

            project_result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project_result.scalar_one_or_none()
            project_name = project.project_name if project else f"Project {project_id}"

            # Get inviter name
            from app.models.users import User

            inviter_result = await self.db.execute(
                select(User).where(User.id == invited_by_id)
            )
            inviter = inviter_result.scalar_one_or_none()
            inviter_name = inviter.full_name if inviter else "A team member"

            self.email_service.send_team_invitation(
                to_email=email,
                inviter_name=inviter_name,
                project_name=project_name,
                role=role.value if hasattr(role, "value") else str(role),
                invitation_token=token,
            )
        except Exception as e:
            # Log but don't fail the invitation if email fails
            logger.warning(f"Failed to send invitation email to {email}: {e}")

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

    async def get_team_activity(self, project_id: UUID) -> dict:
        """Get team activity statistics for a project.

        Returns member info with activity stats (pending/completed tasks).
        """
        from app.models.users import User
        from app.models.workflow import ApprovalStep, ApprovalWorkflow

        # Get team members with user info
        query = (
            select(TeamMember)
            .options(joinedload(TeamMember.user))
            .where(TeamMember.project_id == project_id)
            .where(TeamMember.is_active.is_(True))
        )
        result = await self.db.execute(query)
        members = list(result.scalars().unique().all())

        # Build activity stats for each member
        member_activities = []
        total_pending = 0
        total_completed = 0
        active_count = 0

        for member in members:
            user: User = member.user
            if not user:
                continue

            # Count pending and completed workflow steps for this user
            pending_query = (
                select(ApprovalStep)
                .join(ApprovalWorkflow, ApprovalWorkflow.id == ApprovalStep.workflow_id)
                .where(ApprovalWorkflow.project_id == project_id)
                .where(ApprovalStep.required_user_id == member.user_id)
                .where(ApprovalStep.status.in_(["pending", "in_review"]))
            )
            pending_result = await self.db.execute(pending_query)
            pending_tasks = len(list(pending_result.scalars().all()))

            completed_query = (
                select(ApprovalStep)
                .join(ApprovalWorkflow, ApprovalWorkflow.id == ApprovalStep.workflow_id)
                .where(ApprovalWorkflow.project_id == project_id)
                .where(ApprovalStep.approved_by_id == member.user_id)
                .where(ApprovalStep.status.in_(["approved", "rejected"]))
            )
            completed_result = await self.db.execute(completed_query)
            completed_tasks = len(list(completed_result.scalars().all()))

            total_pending += pending_tasks
            total_completed += completed_tasks

            # Consider member active if they have activity in the last 24 hours
            if member.last_active_at:
                from datetime import timedelta

                if utcnow() - member.last_active_at < timedelta(hours=24):
                    active_count += 1

            member_activities.append(
                {
                    "id": member.id,
                    "user_id": member.user_id,
                    "project_id": member.project_id,
                    "role": member.role,
                    "joined_at": member.joined_at,
                    "last_active_at": member.last_active_at,
                    "name": user.full_name or user.email.split("@")[0],
                    "email": user.email,
                    "pending_tasks": pending_tasks,
                    "completed_tasks": completed_tasks,
                }
            )

        return {
            "members": member_activities,
            "total_pending_tasks": total_pending,
            "total_completed_tasks": total_completed,
            "active_members_count": active_count,
        }

    async def update_member_activity(
        self, project_id: UUID, user_id: UUID
    ) -> TeamMember | None:
        """Update a team member's last active timestamp."""
        query = select(TeamMember).where(
            TeamMember.project_id == project_id,
            TeamMember.user_id == user_id,
            TeamMember.is_active.is_(True),
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if member:
            member.last_active_at = utcnow()
            self.db.add(member)
            await self.db.commit()
            await self.db.refresh(member)
            return member
        return None
