from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr
from app.models.team import UserRole, InvitationStatus


class TeamMemberBase(BaseModel):
    user_id: UUID
    role: UserRole


class TeamMemberRead(TeamMemberBase):
    project_id: UUID
    joined_at: datetime
    # Assuming user details might be joined, but keeping it simple for now

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True
