"""Business performance models for agent deal pipeline and supporting data."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel, MetadataProxy
from app.models.types import FlexibleJSONB

JSONType = FlexibleJSONB


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    """Return the list of values defined on an Enum class."""

    return [member.value for member in enum_cls]


class DealAssetType(str, Enum):
    """Supported asset classifications for agent deals."""

    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    RESIDENTIAL = "residential"
    MIXED_USE = "mixed_use"
    HOTEL = "hotel"
    WAREHOUSE = "warehouse"
    LAND = "land"
    SPECIAL_PURPOSE = "special_purpose"
    PORTFOLIO = "portfolio"


class DealType(str, Enum):
    """High-level deal archetypes tracked in the pipeline."""

    BUY_SIDE = "buy_side"
    SELL_SIDE = "sell_side"
    LEASE = "lease"
    MANAGEMENT = "management"
    CAPITAL_RAISE = "capital_raise"
    OTHER = "other"


class PipelineStage(str, Enum):
    """Deal progression stages."""

    LEAD_CAPTURED = "lead_captured"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    AGREEMENT = "agreement"
    DUE_DILIGENCE = "due_diligence"
    AWAITING_CLOSURE = "awaiting_closure"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class DealStatus(str, Enum):
    """Lifecycle status for an agent deal."""

    OPEN = "open"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    CANCELLED = "cancelled"


class DealContactType(str, Enum):
    """Roles for contacts attached to a deal."""

    PRINCIPAL = "principal"
    CO_BROKE = "co_broke"
    LEGAL = "legal"
    FINANCE = "finance"
    OTHER = "other"


class DealDocumentType(str, Enum):
    """Document categories referenced by a deal."""

    LOI = "loi"
    VALUATION = "valuation"
    AGREEMENT = "agreement"
    FINANCIALS = "financials"
    OTHER = "other"


class AgentDeal(BaseModel):
    """Primary entity representing a cross-asset pipeline opportunity."""

    __tablename__ = "agent_deals"

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    agent_id: Mapped[str] = mapped_column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[Optional[str]] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    property_id: Mapped[Optional[str]] = mapped_column(
        UUID(),
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    asset_type: Mapped[DealAssetType] = mapped_column(
        SQLEnum(
            DealAssetType,
            name="deal_asset_type",
            values_callable=_enum_values,
        ),
        nullable=False,
        index=True,
    )
    deal_type: Mapped[DealType] = mapped_column(
        SQLEnum(
            DealType,
            name="deal_type",
            values_callable=_enum_values,
        ),
        nullable=False,
        index=True,
    )
    pipeline_stage: Mapped[PipelineStage] = mapped_column(
        SQLEnum(
            PipelineStage,
            name="pipeline_stage",
            values_callable=_enum_values,
        ),
        default=PipelineStage.LEAD_CAPTURED,
        nullable=False,
        index=True,
    )
    status: Mapped[DealStatus] = mapped_column(
        SQLEnum(
            DealStatus,
            name="deal_status",
            values_callable=_enum_values,
        ),
        default=DealStatus.OPEN,
        nullable=False,
        index=True,
    )
    lead_source: Mapped[Optional[str]] = mapped_column(String(120))
    estimated_value_amount: Mapped[Optional[float]] = mapped_column(Numeric(16, 2))
    estimated_value_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="SGD", server_default="SGD"
    )
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_close_date: Mapped[Optional[date]] = mapped_column(Date)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    metadata = MetadataProxy()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    stage_events: Mapped[list["AgentDealStageEvent"]] = relationship(
        "AgentDealStageEvent",
        back_populates="deal",
        cascade="all, delete-orphan",
        order_by="AgentDealStageEvent.recorded_at",
    )
    contacts: Mapped[list["AgentDealContact"]] = relationship(
        "AgentDealContact", back_populates="deal", cascade="all, delete-orphan"
    )
    documents: Mapped[list["AgentDealDocument"]] = relationship(
        "AgentDealDocument", back_populates="deal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_agent_deals_agent_stage", "agent_id", "pipeline_stage"),
        Index("ix_agent_deals_status_created", "status", "created_at"),
    )


class AgentDealStageEvent(BaseModel):
    """Immutable history of stage transitions for a deal."""

    __tablename__ = "agent_deal_stage_events"

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(),
        ForeignKey("agent_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_stage: Mapped[Optional[PipelineStage]] = mapped_column(
        SQLEnum(
            PipelineStage,
            name="pipeline_stage",
            values_callable=_enum_values,
        ),
        nullable=True,
    )
    to_stage: Mapped[PipelineStage] = mapped_column(
        SQLEnum(
            PipelineStage,
            name="pipeline_stage",
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    changed_by: Mapped[Optional[str]] = mapped_column(
        UUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    note: Mapped[Optional[str]] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    metadata = MetadataProxy()

    deal: Mapped[AgentDeal] = relationship("AgentDeal", back_populates="stage_events")

    __table_args__ = (
        Index("ix_agent_deal_stage_events_stage_time", "to_stage", "recorded_at"),
    )


class AgentDealContact(BaseModel):
    """Counterparty contacts involved with a deal."""

    __tablename__ = "agent_deal_contacts"

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(),
        ForeignKey("agent_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_type: Mapped[DealContactType] = mapped_column(
        SQLEnum(
            DealContactType,
            name="deal_contact_type",
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    company: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    metadata = MetadataProxy()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    deal: Mapped[AgentDeal] = relationship("AgentDeal", back_populates="contacts")

    __table_args__ = (Index("ix_agent_deal_contacts_type", "contact_type"),)


class AgentDealDocument(BaseModel):
    """References to supporting documents for a deal."""

    __tablename__ = "agent_deal_documents"

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    deal_id: Mapped[str] = mapped_column(
        UUID(),
        ForeignKey("agent_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[DealDocumentType] = mapped_column(
        SQLEnum(
            DealDocumentType,
            name="deal_document_type",
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    uri: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(120))
    uploaded_by: Mapped[Optional[str]] = mapped_column(
        UUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    metadata = MetadataProxy()

    deal: Mapped[AgentDeal] = relationship("AgentDeal", back_populates="documents")

    __table_args__ = (
        Index("ix_agent_deal_documents_type", "document_type"),
        UniqueConstraint("deal_id", "title", name="uq_agent_deal_document_title"),
    )


__all__ = [
    "AgentDeal",
    "AgentDealStageEvent",
    "AgentDealContact",
    "AgentDealDocument",
    "DealAssetType",
    "DealType",
    "DealStatus",
    "PipelineStage",
    "DealContactType",
    "DealDocumentType",
]
