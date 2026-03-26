from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.team import UserRole, InvitationStatus


class TeamMemberBase(BaseModel):
    user_id: UUID
    role: UserRole


class TeamMemberRead(TeamMemberBase):
    project_id: UUID
    joined_at: datetime
    last_active_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TeamMemberActivityRead(BaseModel):
    """Extended team member info with activity stats."""

    id: UUID
    user_id: UUID
    project_id: UUID
    role: UserRole
    joined_at: datetime
    last_active_at: Optional[datetime] = None
    # User details (joined from User model)
    name: str
    email: str
    # Activity stats (computed)
    pending_tasks: int = 0
    completed_tasks: int = 0

    model_config = ConfigDict(from_attributes=True)


class TeamActivityStatsResponse(BaseModel):
    """Response schema for team activity statistics."""

    members: list[TeamMemberActivityRead]
    total_pending_tasks: int
    total_completed_tasks: int
    active_members_count: int


class InvitationBase(BaseModel):
    email: EmailStr
    role: UserRole


class InvitationCreate(InvitationBase):
    pass


class InvitationRead(InvitationBase):
    id: UUID
    project_id: UUID
    status: InvitationStatus
    token: str  # In real world, maybe hide this
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
