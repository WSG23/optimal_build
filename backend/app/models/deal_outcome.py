"""Deal outcome models for capturing realised results vs projections."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from app.models.base import UUID, BaseModel, MetadataProxy
from app.models.types import FlexibleJSONB
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

JSONType = FlexibleJSONB


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    """Return the list of values defined on an Enum class."""

    return [member.value for member in enum_cls]


class OutcomeResolution(str, Enum):
    """Why the deal resolved the way it did."""

    COMPLETED = "completed"
    PARTIAL_CLOSE = "partial_close"
    LOST_PRICE = "lost_price"
    LOST_PLANNING = "lost_planning"
    LOST_COMPETITION = "lost_competition"
    LOST_TIMELINE = "lost_timeline"
    LOST_FINANCING = "lost_financing"
    LOST_COMPLIANCE = "lost_compliance"
    LOST_OTHER = "lost_other"
    WITHDRAWN = "withdrawn"


class ApprovalOutcome(str, Enum):
    """Authority decision on the development application."""

    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    AMENDED_AND_APPROVED = "amended_and_approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"


class DealOutcome(BaseModel):
    """Realised outcome for a closed deal, enabling projected-vs-actual analysis."""

    __tablename__ = "deal_outcomes"

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(),
        ForeignKey("agent_deals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    scenario_id: Mapped[Optional[int]] = mapped_column(
        Integer(),
        ForeignKey("fin_scenarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recorded_by: Mapped[Optional[str]] = mapped_column(
        UUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # --- Resolution ---
    resolution: Mapped[str] = mapped_column(String(40), nullable=False)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Actual financials (nullable — partial data is fine) ---
    actual_purchase_price: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    actual_price_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="SGD", server_default="SGD"
    )
    actual_gfa_approved_sqm: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    actual_construction_cost: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    actual_noi: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
    actual_yield_pct: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 3), nullable=True
    )

    # --- Timeline ---
    actual_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approval_submitted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approval_decided_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # --- Authority / approval metadata ---
    approval_authority: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    approval_outcome: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    approval_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gfa_amendment_sqm: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # --- Denormalised for benchmark queries ---
    jurisdiction_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    asset_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    # --- Extensible metadata ---
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    metadata = MetadataProxy()

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    deal: Mapped["AgentDeal"] = relationship(  # noqa: F821
        "AgentDeal", back_populates="outcome"
    )
    scenario: Mapped[Optional["FinScenario"]] = relationship(  # noqa: F821
        "FinScenario", back_populates="deal_outcomes"
    )
    recorder: Mapped[Optional["User"]] = relationship("User")  # noqa: F821

    __table_args__ = (
        Index("ix_deal_outcomes_deal_id", "deal_id", unique=True),
        Index("ix_deal_outcomes_resolution", "resolution"),
        Index(
            "ix_deal_outcomes_jurisdiction_asset",
            "jurisdiction_code",
            "asset_type",
        ),
        Index("ix_deal_outcomes_created_at", "created_at"),
    )


__all__ = ["ApprovalOutcome", "DealOutcome", "OutcomeResolution"]
