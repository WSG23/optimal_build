"""Organization (tenant) model.

A singleton ``default`` row is seeded by migration so existing data can be
back-filled with a non-null ``organization_id`` once multi-tenant queries roll
out. New rows continue to allow NULL during the transition window.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel

DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class Organization(BaseModel):
    """Tenant boundary for row-level isolation."""

    __tablename__ = "organizations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


__all__ = ["DEFAULT_ORG_ID", "Organization"]
