"""Organization schemas for multi-tenancy API.

Provides Pydantic models for:
- Organization CRUD operations
- Member management
- Invitation workflows
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationPlan(str, Enum):
    """Subscription plans for organizations."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrganizationRole(str, Enum):
    """Roles within an organization."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# ============================================================================
# Organization Schemas
# ============================================================================


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Organization name"
    )
    slug: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="URL-safe slug for the organization",
    )
    uen_number: Optional[str] = Field(
        None, max_length=50, description="Singapore UEN number"
    )


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[dict] = Field(None, description="Organization settings")
    uen_number: Optional[str] = Field(None, max_length=50)


class OrganizationResponse(BaseModel):
    """Schema for organization in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    plan: OrganizationPlan
    is_active: bool
    is_verified: bool
    uen_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class OrganizationDetail(OrganizationResponse):
    """Detailed organization response including settings and member count."""

    settings: dict = Field(default_factory=dict)
    member_count: int = 0
    project_count: int = 0


# ============================================================================
# Organization Member Schemas
# ============================================================================


class OrganizationMemberCreate(BaseModel):
    """Schema for adding a member to an organization."""

    user_id: UUID = Field(..., description="User ID to add as member")
    role: OrganizationRole = Field(
        default=OrganizationRole.MEMBER, description="Role within organization"
    )


class OrganizationMemberUpdate(BaseModel):
    """Schema for updating a member's role."""

    role: OrganizationRole = Field(..., description="New role for the member")


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrganizationRole
    is_active: bool
    joined_at: datetime

    # Included from user relationship
    user_email: Optional[str] = None
    user_name: Optional[str] = None


# ============================================================================
# Organization Invitation Schemas
# ============================================================================


class InvitationStatus(str, Enum):
    """Status of an invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class OrganizationInvitationCreate(BaseModel):
    """Schema for creating an invitation."""

    email: EmailStr = Field(..., description="Email address to invite")
    role: OrganizationRole = Field(
        default=OrganizationRole.MEMBER, description="Role to assign on acceptance"
    )


class OrganizationInvitationResponse(BaseModel):
    """Schema for invitation in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    email: str
    role: OrganizationRole
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""

    token: str = Field(..., min_length=1, description="Invitation token")


# ============================================================================
# Switch Organization
# ============================================================================


class SwitchOrganization(BaseModel):
    """Schema for switching active organization context."""

    organization_id: UUID = Field(..., description="Organization ID to switch to")


# ============================================================================
# List Responses
# ============================================================================


class OrganizationListResponse(BaseModel):
    """Paginated list of organizations."""

    items: list[OrganizationResponse]
    total: int
    page: int
    page_size: int


class OrganizationMemberListResponse(BaseModel):
    """Paginated list of organization members."""

    items: list[OrganizationMemberResponse]
    total: int
    page: int
    page_size: int


class OrganizationInvitationListResponse(BaseModel):
    """Paginated list of organization invitations."""

    items: list[OrganizationInvitationResponse]
    total: int
    page: int
    page_size: int


__all__ = [
    "OrganizationPlan",
    "OrganizationRole",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationDetail",
    "OrganizationMemberCreate",
    "OrganizationMemberUpdate",
    "OrganizationMemberResponse",
    "InvitationStatus",
    "OrganizationInvitationCreate",
    "OrganizationInvitationResponse",
    "InvitationAccept",
    "SwitchOrganization",
    "OrganizationListResponse",
    "OrganizationMemberListResponse",
    "OrganizationInvitationListResponse",
]
