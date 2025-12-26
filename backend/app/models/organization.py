"""Organization model for multi-tenancy support.

This module provides workspace/organization isolation for enterprise deployments.
Organizations are the top-level container for all data in the system.
"""

from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import UUID, BaseModel
from backend._compat.datetime import utcnow


class OrganizationPlan(str, Enum):
    """Subscription plans for organizations."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrganizationRole(str, Enum):
    """Roles within an organization (distinct from project-level roles)."""

    OWNER = "owner"  # Full access, billing, can delete org
    ADMIN = "admin"  # Manage members, settings
    MEMBER = "member"  # Standard access
    VIEWER = "viewer"  # Read-only access


class Organization(BaseModel):
    """Organization/tenant container for multi-tenancy.

    All projects, finance data, and team members belong to an organization.
    This enables data isolation between different companies/teams.
    """

    __tablename__ = "organizations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)

    # Billing and subscription
    plan = Column(
        SQLEnum(OrganizationPlan, values_callable=lambda x: [e.value for e in x]),
        default=OrganizationPlan.FREE,
        nullable=False,
    )

    # Organization settings
    settings = Column(JSONB, default=dict, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Soft delete support
    deleted_at = Column(DateTime, nullable=True)

    # Singapore-specific compliance
    uen_number = Column(String(50), nullable=True)  # Unique Entity Number

    # Relationships
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    projects = relationship(
        "Project",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name} ({self.slug})>"


class OrganizationMember(BaseModel):
    """User membership in an organization.

    Users can belong to multiple organizations with different roles.
    This is separate from project-level team membership.
    """

    __tablename__ = "organization_members"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Role within this organization
    role = Column(
        SQLEnum(OrganizationRole, values_callable=lambda x: [e.value for e in x]),
        default=OrganizationRole.MEMBER,
        nullable=False,
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
        Index("ix_organization_members_org_id", "organization_id"),
        Index("ix_organization_members_user_id", "user_id"),
        Index("ix_organization_members_active", "organization_id", "is_active"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<OrganizationMember org={self.organization_id} user={self.user_id}>"


class OrganizationInvitation(BaseModel):
    """Invitations to join an organization.

    Tracks pending invitations with expiration and token-based acceptance.
    """

    __tablename__ = "organization_invitations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    role = Column(
        SQLEnum(OrganizationRole, values_callable=lambda x: [e.value for e in x]),
        default=OrganizationRole.MEMBER,
        nullable=False,
    )

    # Token for acceptance
    token = Column(String(100), unique=True, nullable=False, index=True)

    # Status tracking
    status = Column(
        String(20), default="pending", nullable=False
    )  # pending, accepted, expired, revoked
    invited_by = Column(UUID(), ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization")
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        Index("ix_organization_invitations_org_id", "organization_id"),
        Index("ix_organization_invitations_email_status", "email", "status"),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<OrganizationInvitation {self.email} -> {self.organization_id}>"


__all__ = [
    "Organization",
    "OrganizationMember",
    "OrganizationInvitation",
    "OrganizationPlan",
    "OrganizationRole",
]
