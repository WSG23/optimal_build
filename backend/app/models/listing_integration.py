"""Models for external listing integrations (PropertyGuru, EdgeProp, CRM)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.models.base import UUID, BaseModel


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class ListingProvider(str, Enum):
    PROPERTYGURU = "propertyguru"
    EDGEPROP = "edgeprop"
    ZOHO_CRM = "zoho_crm"


class ListingAccountStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REVOKED = "revoked"


class ListingPublicationStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class ListingIntegrationAccount(BaseModel):
    """Stores OAuth tokens and metadata for external listing providers."""

    __tablename__ = "listing_integration_accounts"

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[ListingProvider] = mapped_column(
        SQLEnum(
            ListingProvider,
            name="listing_provider",
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    status: Mapped[ListingAccountStatus] = mapped_column(
        SQLEnum(
            ListingAccountStatus,
            name="listing_account_status",
            values_callable=_enum_values,
        ),
        default=ListingAccountStatus.CONNECTED,
        nullable=False,
    )
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="listing_accounts")
    publications = relationship(
        "ListingPublication",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "provider", name="uq_listing_account_user_provider"
        ),
    )


class ListingPublication(BaseModel):
    """Tracks listing publication status per external provider."""

    __tablename__ = "listing_publications"

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    property_id: Mapped[str] = mapped_column(
        UUID(),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[str] = mapped_column(
        UUID(),
        ForeignKey("listing_integration_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_listing_id: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[ListingPublicationStatus] = mapped_column(
        SQLEnum(
            ListingPublicationStatus,
            name="listing_publication_status",
            values_callable=_enum_values,
        ),
        default=ListingPublicationStatus.DRAFT,
        nullable=False,
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    account = relationship("ListingIntegrationAccount", back_populates="publications")
    property = relationship("Property", backref="listing_publications")


__all__ = [
    "ListingProvider",
    "ListingAccountStatus",
    "ListingPublicationStatus",
    "ListingIntegrationAccount",
    "ListingPublication",
]
