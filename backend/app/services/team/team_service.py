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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class TeamService:
    """Service for managing team members and invitations."""

    def __init__(
        self, db_session: AsyncSession, email_service: EmailService | None = None
    ) -> None:
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
        member_activities: list[dict] = []
        member_entries: dict[UUID, dict] = {}
        role_index: dict[str, list[UUID]] = {}
        active_count = 0

        for member in members:
            user: User = member.user
            if not user:
                continue

            role_value = (
                member.role.value if hasattr(member.role, "value") else str(member.role)
            )
            role_key = role_value.strip().lower()
            role_index.setdefault(role_key, []).append(member.user_id)

            if member.last_active_at:
                from datetime import timedelta

                if utcnow() - member.last_active_at < timedelta(hours=24):
                    active_count += 1

            entry = {
                "id": member.id,
                "user_id": member.user_id,
                "project_id": member.project_id,
                "role": role_value,
                "joined_at": member.joined_at,
                "last_active_at": member.last_active_at,
                "name": user.full_name or user.email.split("@")[0],
                "email": user.email,
                "pending_tasks": 0,
                "completed_tasks": 0,
            }
            member_entries[member.user_id] = entry
            member_activities.append(entry)

        step_query = (
            select(ApprovalStep)
            .join(ApprovalWorkflow, ApprovalWorkflow.id == ApprovalStep.workflow_id)
            .where(ApprovalWorkflow.project_id == project_id)
        )
        steps_result = await self.db.execute(step_query)
        steps = list(steps_result.scalars().all())

        user_ids: set[UUID] = set()
        for step in steps:
            if step.required_user_id and step.required_user_id not in member_entries:
                user_ids.add(step.required_user_id)
            if step.approved_by_id and step.approved_by_id not in member_entries:
                user_ids.add(step.approved_by_id)

        user_lookup: dict[UUID, User] = {}
        if user_ids:
            users_result = await self.db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            user_lookup = {user.id: user for user in users_result.scalars().all()}

        ghost_entries: dict[UUID, dict] = {}
        role_entries: dict[str, dict] = {}

        def normalise_role(value: str | None) -> str:
            if not value:
                return ""
            if hasattr(value, "value"):
                value = value.value  # type: ignore[assignment]
            return str(value).strip().lower()

        def role_display(value: str | None) -> str:
            if not value:
                return "Unassigned"
            if hasattr(value, "value"):
                value = value.value  # type: ignore[assignment]
            return str(value).replace("_", " ").title()

        def get_user_entry(user_id: UUID, role_hint: str | None) -> dict:
            if user_id in member_entries:
                return member_entries[user_id]
            if user_id in ghost_entries:
                return ghost_entries[user_id]

            user = user_lookup.get(user_id)
            role_value = None
            if user and user.role:
                role_value = (
                    user.role.value if hasattr(user.role, "value") else str(user.role)
                )
            if not role_value:
                role_value = (
                    role_hint.value
                    if hasattr(role_hint, "value")
                    else str(role_hint) if role_hint else "viewer"
                )

            name = None
            email = ""
            if user:
                name = user.full_name or user.email.split("@")[0]
                email = user.email
            if not name:
                name = role_display(role_value)

            entry = {
                "id": str(user_id),
                "user_id": user_id,
                "project_id": project_id,
                "role": role_value,
                "joined_at": None,
                "last_active_at": None,
                "name": name,
                "email": email,
                "pending_tasks": 0,
                "completed_tasks": 0,
            }
            ghost_entries[user_id] = entry
            return entry

        def get_role_entry(role_value: str | None) -> dict:
            role_key = normalise_role(role_value)
            entry = role_entries.get(role_key)
            if entry:
                return entry
            entry = {
                "id": f"role:{role_key or 'unassigned'}",
                "user_id": None,
                "project_id": project_id,
                "role": role_value or "unassigned",
                "joined_at": None,
                "last_active_at": None,
                "name": role_display(role_value),
                "email": "",
                "pending_tasks": 0,
                "completed_tasks": 0,
            }
            role_entries[role_key] = entry
            return entry

        for step in steps:
            status_value = (
                step.status.value if hasattr(step.status, "value") else step.status
            )
            status_label = str(status_value or "").lower()
            role_hint = step.required_role
            role_key = normalise_role(role_hint)
            role_members = role_index.get(role_key, [])

            if status_label in ("pending", "in_review"):
                if step.required_user_id:
                    entry = get_user_entry(step.required_user_id, role_hint)
                    entry["pending_tasks"] += 1
                elif role_hint:
                    if len(role_members) == 1:
                        entry = member_entries[role_members[0]]
                    else:
                        entry = get_role_entry(role_hint)
                    entry["pending_tasks"] += 1

            if status_label in ("approved", "rejected"):
                if step.approved_by_id:
                    entry = get_user_entry(step.approved_by_id, role_hint)
                    entry["completed_tasks"] += 1
                elif role_hint:
                    if len(role_members) == 1:
                        entry = member_entries[role_members[0]]
                    else:
                        entry = get_role_entry(role_hint)
                    entry["completed_tasks"] += 1

        all_entries = (
            member_activities
            + list(ghost_entries.values())
            + list(role_entries.values())
        )
        return {
            "members": all_entries,
            "total_pending_tasks": sum(
                entry.get("pending_tasks", 0) for entry in all_entries
            ),
            "total_completed_tasks": sum(
                entry.get("completed_tasks", 0) for entry in all_entries
            ),
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
