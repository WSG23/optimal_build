"""Model output persistence with built-in feedback loop.

One row per inference. Together with ``entity_history`` this gives ML training
two of the three primitives it needs: ground-truth (history) and model output
(here). Add ``human_feedback`` post-hoc to close the loop without altering the
original prediction.

Writer contract:

* ``model_name`` / ``model_version`` — registry coordinates (e.g.
  ``"compliance.v1"`` / ``"2026-05-18.r3"``). Indexed together for drift queries.
* ``input_entity_type`` / ``input_entity_id`` — pointer to the thing being
  predicted on. Same encoding as :mod:`entity_history`.
* ``output`` — JSON; the structured prediction (label probs, recommendation,
  scenario summary).
* ``confidence`` — ``Numeric(6,4)`` so feature stores can train without float
  drift.
* ``human_feedback`` / ``feedback_at`` — populated when a user accepts,
  rejects, or amends the prediction.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB


class Prediction(BaseModel):
    """Persisted model output with optional human feedback."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str] = mapped_column(String(60), nullable=False)
    model_provider: Mapped[Optional[str]] = mapped_column(String(60))

    input_entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    input_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    input_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    input_hash: Mapped[Optional[str]] = mapped_column(String(64))

    output: Mapped[dict] = mapped_column(FlexibleJSONB, default=dict, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(120))
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))

    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost_estimate: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)

    organization_id = mapped_column(UUID(), nullable=True, index=True)
    created_by = mapped_column(UUID(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    human_feedback: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    human_feedback_label: Mapped[Optional[str]] = mapped_column(String(60))
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    feedback_by = mapped_column(UUID(), nullable=True)

    __table_args__ = (
        Index(
            "idx_predictions_model_version",
            "model_name",
            "model_version",
            "created_at",
        ),
        Index(
            "idx_predictions_entity",
            "input_entity_type",
            "input_entity_id",
            "created_at",
        ),
        Index(
            "idx_predictions_feedback",
            "model_name",
            "human_feedback_label",
            "feedback_at",
        ),
    )


__all__ = ["Prediction"]
