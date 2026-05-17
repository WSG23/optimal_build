"""Behavioral event capture (PR1 of data-collection upgrade).

Two append-only logs powering the training-data pipeline:

* :class:`UserEvent` — every meaningful UI action (page view, click, hover-end,
  filter applied, export downloaded). Generic enough that adding a new event
  type does not require a schema change.
* :class:`SearchQuery` — what users typed, what they got back, which rank they
  clicked. The retrieval/ranking signal we cannot reconstruct after the fact.

Writers should treat both tables as append-only. Sensitive payload fields
(emails, full IP) must be hashed at the API layer before persistence — the
storage tier should not see them in plaintext.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB


class UserEvent(BaseModel):
    """Single behavioral observation. Partition-friendly by ``occurred_at``."""

    __tablename__ = "user_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    organization_id = mapped_column(UUID(), nullable=True, index=True)
    user_id = mapped_column(UUID(), nullable=True)
    anonymous_id: Mapped[Optional[str]] = mapped_column(String(64))
    session_id: Mapped[Optional[str]] = mapped_column(String(64))

    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    event_name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(80))
    target_id: Mapped[Optional[str]] = mapped_column(String(64))

    payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)

    path: Mapped[Optional[str]] = mapped_column(String(255))
    referrer: Mapped[Optional[str]] = mapped_column(String(255))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64))

    client_event_id: Mapped[Optional[str]] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    server_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_user_events_occurred", "occurred_at"),
        Index("idx_user_events_user_occurred", "user_id", "occurred_at"),
        Index(
            "idx_user_events_type_name_occurred",
            "event_type",
            "event_name",
            "occurred_at",
        ),
        Index(
            "idx_user_events_target",
            "target_type",
            "target_id",
            "occurred_at",
        ),
        Index("idx_user_events_client_id", "client_event_id"),
    )


class SearchQuery(BaseModel):
    """Search intent + result + click-through outcome."""

    __tablename__ = "search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    organization_id = mapped_column(UUID(), nullable=True, index=True)
    user_id = mapped_column(UUID(), nullable=True)
    anonymous_id: Mapped[Optional[str]] = mapped_column(String(64))
    session_id: Mapped[Optional[str]] = mapped_column(String(64))

    query_text: Mapped[str] = mapped_column(String(500), nullable=False)
    query_type: Mapped[Optional[str]] = mapped_column(String(40))
    filters: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)

    result_count: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    top_results: Mapped[Optional[list]] = mapped_column(FlexibleJSONB)

    clicked_rank: Mapped[Optional[int]] = mapped_column(Integer)
    clicked_entity_type: Mapped[Optional[str]] = mapped_column(String(80))
    clicked_entity_id: Mapped[Optional[str]] = mapped_column(String(64))
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_search_queries_occurred", "occurred_at"),
        Index(
            "idx_search_queries_user_occurred",
            "user_id",
            "occurred_at",
        ),
        Index(
            "idx_search_queries_type_occurred",
            "query_type",
            "occurred_at",
        ),
    )


__all__ = ["SearchQuery", "UserEvent"]
