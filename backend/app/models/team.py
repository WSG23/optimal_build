"""Team management models for project collaboration."""

import uuid
from enum import Enum

from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from app.models.users import UserRole
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import relationship


class InvitationStatus(str, Enum):
    """Status of a team invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class TeamMember(BaseModel):
    """Represents a user's membership in a project team."""

    __tablename__ = "team_members"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Role within this specific project context
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="team_members")
    user = relationship("User", backref="team_memberships")

    __table_args__ = (
        # correct unique constraint syntax for SQLAlchemy
        {"sqlite_autoincrement": True},
    )


class TeamInvitation(BaseModel):
    """Pending invitation for a user to join a project."""

    __tablename__ = "team_invitations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=False, index=True)

    # We invite by email. If user exists, we can link them, but email is the key.
    email = Column(String(255), nullable=False, index=True)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    # Security
    token = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum(InvitationStatus, values_callable=lambda x: [e.value for e in x]),
        default=InvitationStatus.PENDING,
        nullable=False,
    )

    invited_by_id = Column(UUID(), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)

    # Relationships
    project = relationship("Project", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])

    def is_valid(self) -> bool:
        """Check if invitation is valid (pending and not expired)."""
        if self.status != InvitationStatus.PENDING:
            return False
        # Handle both timezone-aware and timezone-naive datetimes
        now = utcnow()
        expires = self.expires_at
        # Strip timezone info from now if expires_at is timezone-naive
        if expires.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        return now < expires
