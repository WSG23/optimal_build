"""Models for managing stored rule packs."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import BaseModel
from app.models.types import FlexibleJSONB

JSONType = FlexibleJSONB


class RulePack(BaseModel):
    """Persisted rule pack definition with jurisdictional metadata."""

    __tablename__ = "rule_packs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    jurisdiction: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    authority: Mapped[str | None] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    definition: Mapped[dict] = mapped_column(JSONType, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("slug", "version", name="uq_rule_pack_slug_version"),
    )


__all__ = ["RulePack"]
