"""User model for Singapore Property Development Platform."""

import uuid
from enum import Enum

from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, String
from sqlalchemy.orm import relationship


class UserRole(str, Enum):
    """User roles in the system."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    INVESTOR = "investor"
    CONTRACTOR = "contractor"
    CONSULTANT = "consultant"
    REGULATORY_OFFICER = "regulatory_officer"
    VIEWER = "viewer"


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    company_name = Column(String(255))
    phone_number = Column(String(50))

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_login = Column(DateTime)

    # Singapore specific fields
    uen_number = Column(String(50))  # Unique Entity Number for Singapore companies
    acra_registered = Column(Boolean, default=False)  # ACRA registration status

    # Relationships
    ai_agent_sessions = relationship(
        "AIAgentSession", back_populates="user", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    listing_accounts = relationship(
        "ListingIntegrationAccount",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
