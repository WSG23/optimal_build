"""Decision provenance (PR2 of data-collection upgrade).

For every UI moment that presents more than one option (recommended scenarios,
comparable transactions, financing structures) we want to know:

* what the choice set was,
* which option was shown at which rank,
* which one the user picked,
* what they ignored,
* how long they deliberated.

That is the raw material for preference-pair training (chose A over B) and the
single most undercollected signal in CRE products today. Without it you can
only train on accepted recommendations, never on the comparison.

A *choice set* is a UUID generated client-side when the alternatives are
rendered. All rows in a set share that ``choice_set_id`` so a single batch
write captures the whole presentation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB


class DecisionAlternative(BaseModel):
    """One option presented to the user inside a choice set."""

    __tablename__ = "decision_alternatives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    organization_id = mapped_column(UUID(), nullable=True, index=True)
    user_id = mapped_column(UUID(), nullable=True)
    anonymous_id: Mapped[Optional[str]] = mapped_column(String(64))
    session_id: Mapped[Optional[str]] = mapped_column(String(64))

    decision_type: Mapped[str] = mapped_column(String(60), nullable=False)
    choice_set_id: Mapped[str] = mapped_column(String(64), nullable=False)
    context_entity_type: Mapped[Optional[str]] = mapped_column(String(80))
    context_entity_id: Mapped[Optional[str]] = mapped_column(String(64))

    alternative_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    alternative_label: Mapped[Optional[str]] = mapped_column(String(255))
    alternative_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))

    presented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    chosen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chosen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    time_to_decide_ms: Mapped[Optional[int]] = mapped_column(Integer)
    dismissed_reason: Mapped[Optional[str]] = mapped_column(String(120))
    rationale: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "idx_decision_alts_choice_set",
            "choice_set_id",
            "alternative_rank",
        ),
        Index(
            "idx_decision_alts_type_chosen_presented",
            "decision_type",
            "chosen",
            "presented_at",
        ),
        Index(
            "idx_decision_alts_user_presented",
            "user_id",
            "presented_at",
        ),
        Index(
            "idx_decision_alts_context",
            "context_entity_type",
            "context_entity_id",
            "presented_at",
        ),
    )


__all__ = ["DecisionAlternative"]
