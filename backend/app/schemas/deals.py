"""Pydantic schemas for agent deal pipeline endpoints."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.business_performance import (
    AgentDeal,
    AgentDealStageEvent,
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

    @classmethod
    def from_orm_event(
        cls, event: AgentDealStageEvent, *, duration_seconds: float | None = None
    ) -> "DealStageEventSchema":
        payload = cls.model_validate(event).model_dump()
        payload["duration_seconds"] = duration_seconds
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
        cls, deal: AgentDeal, *, timeline: list[AgentDealStageEvent]
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
            data["timeline"].append(
                DealStageEventSchema.from_orm_event(
                    event, duration_seconds=duration_seconds
                )
            )
        return cls.model_validate(data)


__all__ = [
    "DealCreate",
    "DealSchema",
    "DealStageChangeRequest",
    "DealStageEventSchema",
    "DealUpdate",
    "DealWithTimelineSchema",
]
