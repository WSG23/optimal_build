"""Pydantic schemas for agent deal pipeline endpoints."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.business_performance import (
    AgentCommissionAdjustment,
    AgentCommissionRecord,
    AgentDeal,
    AgentDealStageEvent,
    CommissionAdjustmentType,
    CommissionStatus,
    CommissionType,
    DealAssetType,
    DealStatus,
    DealType,
    PipelineStage,
)


class DealCreate(BaseModel):
    """Payload required to open a new deal in the pipeline."""

    title: str
    asset_type: DealAssetType
    deal_type: DealType
    description: str | None = None
    pipeline_stage: PipelineStage = PipelineStage.LEAD_CAPTURED
    status: DealStatus = DealStatus.OPEN
    lead_source: str | None = None
    estimated_value_amount: Decimal | None = None
    estimated_value_currency: str = Field(default="SGD", min_length=3, max_length=3)
    expected_close_date: date | None = None
    confidence: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1"))
    project_id: UUID | None = None
    property_id: UUID | None = None
    metadata: dict[str, Any] | None = None
    agent_id: UUID | None = Field(
        default=None,
        description="Optional override – defaults to authenticated user.",
    )


class DealUpdate(BaseModel):
    """Mutable fields on an existing deal."""

    title: str | None = None
    description: str | None = None
    asset_type: DealAssetType | None = None
    deal_type: DealType | None = None
    lead_source: str | None = None
    estimated_value_amount: Decimal | None = None
    estimated_value_currency: str | None = Field(
        default=None, min_length=3, max_length=3
    )
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    confidence: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1"))
    project_id: UUID | None = None
    property_id: UUID | None = None
    metadata: dict[str, Any] | None = None
    status: DealStatus | None = None


class DealStageChangeRequest(BaseModel):
    """Request body for a stage transition."""

    to_stage: PipelineStage
    note: str | None = None
    metadata: dict[str, Any] | None = None
    occurred_at: datetime | None = None


class DealStageEventSchema(BaseModel):
    """Serialised representation of a stage history event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    from_stage: PipelineStage | None = None
    to_stage: PipelineStage
    changed_by: UUID | None = None
    note: str | None = None
    recorded_at: datetime
    metadata: dict[str, Any]
    duration_seconds: float | None = None
    audit_log: dict[str, Any] | None = None

    @classmethod
    def from_orm_event(
        cls,
        event: AgentDealStageEvent,
        *,
        duration_seconds: float | None = None,
        audit_log: dict[str, Any] | None = None,
    ) -> "DealStageEventSchema":
        payload = cls.model_validate(event).model_dump()
        payload["duration_seconds"] = duration_seconds
        payload["audit_log"] = audit_log
        return cls.model_validate(payload)


class DealSchema(BaseModel):
    """Serialised deal returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    project_id: UUID | None = None
    property_id: UUID | None = None
    title: str
    description: str | None = None
    asset_type: DealAssetType
    deal_type: DealType
    pipeline_stage: PipelineStage
    status: DealStatus
    lead_source: str | None = None
    estimated_value_amount: Decimal | None = None
    estimated_value_currency: str
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    confidence: Decimal | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_deal(cls, deal: AgentDeal) -> "DealSchema":
        return cls.model_validate(deal)


class DealWithTimelineSchema(DealSchema):
    """Deal details including ordered stage history."""

    timeline: list[DealStageEventSchema] = Field(default_factory=list)

    @classmethod
    def from_orm_deal(
        cls,
        deal: AgentDeal,
        *,
        timeline: list[AgentDealStageEvent],
        audit_logs: dict[str, dict[str, Any]] | None = None,
    ) -> "DealWithTimelineSchema":
        data = cls.model_validate(deal).model_dump()
        data["timeline"] = []
        for index, event in enumerate(timeline):
            next_event = timeline[index + 1] if index + 1 < len(timeline) else None
            duration_seconds: float | None = None
            if (
                event.recorded_at
                and next_event
                and next_event.recorded_at
                and next_event.recorded_at >= event.recorded_at
            ):
                duration_seconds = (
                    next_event.recorded_at - event.recorded_at
                ).total_seconds()
            audit_log = None
            if audit_logs:
                audit_id = None
                if event.metadata:
                    audit_id = event.metadata.get("audit_log_id")
                if audit_id:
                    audit_log = audit_logs.get(str(audit_id))
            data["timeline"].append(
                DealStageEventSchema.from_orm_event(
                    event,
                    duration_seconds=duration_seconds,
                    audit_log=audit_log,
                )
            )
        return cls.model_validate(data)


class CommissionCreate(BaseModel):
    """Payload for creating a commission record."""

    agent_id: UUID
    commission_type: CommissionType
    status: CommissionStatus = CommissionStatus.PENDING
    basis_amount: Decimal | None = None
    basis_currency: str = Field(default="SGD", min_length=3, max_length=3)
    commission_rate: Decimal | None = None
    commission_amount: Decimal | None = None
    introduced_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class CommissionStatusChangeRequest(BaseModel):
    """Request payload for a commission status transition."""

    status: CommissionStatus
    occurred_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class CommissionAdjustmentCreate(BaseModel):
    """Payload for recording a commission adjustment."""

    adjustment_type: CommissionAdjustmentType
    amount: Decimal | None = None
    currency: str = Field(default="SGD", min_length=3, max_length=3)
    note: str | None = None
    recorded_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class CommissionAdjustmentResponse(BaseModel):
    """Serialised commission adjustment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    commission_id: UUID
    adjustment_type: CommissionAdjustmentType
    amount: Decimal | None = None
    currency: str
    note: str | None = None
    recorded_by: UUID | None = None
    recorded_at: datetime
    metadata: dict[str, Any]
    audit_log_id: int | None = None

    @classmethod
    def from_orm_adjustment(
        cls, adjustment: AgentCommissionAdjustment
    ) -> "CommissionAdjustmentResponse":
        return cls.model_validate(adjustment)


class CommissionResponse(BaseModel):
    """Commission record including adjustments."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    agent_id: UUID
    commission_type: CommissionType
    status: CommissionStatus
    basis_amount: Decimal | None = None
    basis_currency: str
    commission_rate: Decimal | None = None
    commission_amount: Decimal | None = None
    introduced_at: datetime | None = None
    confirmed_at: datetime | None = None
    invoiced_at: datetime | None = None
    paid_at: datetime | None = None
    disputed_at: datetime | None = None
    resolved_at: datetime | None = None
    metadata: dict[str, Any]
    audit_log_id: int | None = None
    created_at: datetime
    updated_at: datetime
    adjustments: list[CommissionAdjustmentResponse] = Field(
        default_factory=list, exclude=True
    )

    @classmethod
    def from_orm_record(cls, record: AgentCommissionRecord) -> "CommissionResponse":
        # Build dict manually to avoid lazy-loading adjustments during validation
        data = {
            "id": record.id,
            "deal_id": record.deal_id,
            "agent_id": record.agent_id,
            "commission_type": record.commission_type,
            "status": record.status,
            "basis_amount": record.basis_amount,
            "basis_currency": record.basis_currency,
            "commission_rate": record.commission_rate,
            "commission_amount": record.commission_amount,
            "introduced_at": record.introduced_at,
            "confirmed_at": record.confirmed_at,
            "invoiced_at": record.invoiced_at,
            "paid_at": record.paid_at,
            "disputed_at": record.disputed_at,
            "resolved_at": record.resolved_at,
            "metadata": record.metadata,
            "audit_log_id": record.audit_log_id,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "adjustments": [],
        }
        model = cls.model_validate(data)
        # Only access adjustments if explicitly loaded
        if hasattr(record, "__dict__") and "adjustments" in record.__dict__:
            model.adjustments = [
                CommissionAdjustmentResponse.from_orm_adjustment(adj)
                for adj in record.adjustments
            ]
        return model


__all__ = [
    "DealCreate",
    "DealSchema",
    "DealStageChangeRequest",
    "DealStageEventSchema",
    "DealUpdate",
    "DealWithTimelineSchema",
    "CommissionCreate",
    "CommissionResponse",
    "CommissionStatusChangeRequest",
    "CommissionAdjustmentCreate",
    "CommissionAdjustmentResponse",
]
