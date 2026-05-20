"""Generic row-level change history.

One ``entity_history`` row per mutation. Use this instead of per-table shadow
tables so ML training pipelines can reconstruct any entity's state at a given
point in time with a single query pattern.

Writer contract (application code):

* ``entity_type`` — the ORM ``__tablename__`` of the row that changed.
* ``entity_id`` — string form of the primary key (UUID or int both fit).
* ``version`` — monotonically increasing per (entity_type, entity_id); writers
  read ``MAX(version)`` for the entity and increment.
* ``before`` / ``after`` — full row snapshots (or column subset) as JSON.
  Storing both makes deltas computable in SQL without joining adjacent rows.
* ``changed_by`` — user id or service principal that initiated the change.
* ``reason`` — free-text reason (e.g. ``"user_correction"``, ``"ingest_job"``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB


class EntityHistory(BaseModel):
    """Append-only audit trail of row mutations across the schema."""

    __tablename__ = "entity_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    operation: Mapped[str] = mapped_column(String(16), nullable=False)
    before: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    after: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    changed_fields: Mapped[Optional[list[str]]] = mapped_column(FlexibleJSONB)

    changed_by = mapped_column(UUID(), nullable=True)
    changed_by_label: Mapped[Optional[str]] = mapped_column(String(255))
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    request_id: Mapped[Optional[str]] = mapped_column(String(64))

    organization_id = mapped_column(UUID(), nullable=True)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "entity_id",
            "version",
            name="uq_entity_history_version",
        ),
        Index(
            "idx_entity_history_entity",
            "entity_type",
            "entity_id",
            "version",
        ),
        Index(
            "idx_entity_history_changed_at",
            "entity_type",
            "changed_at",
        ),
        Index(
            "idx_entity_history_org_changed_at",
            "organization_id",
            "changed_at",
        ),
    )


__all__ = ["EntityHistory"]
