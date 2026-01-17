"""Pydantic schemas for AI Configuration API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIConfigBase(BaseModel):
    """Base schema for AI configuration."""

    category: str = Field(..., min_length=1, max_length=100)
    config_key: str = Field(..., min_length=1, max_length=200)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    config_value: dict[str, Any] = Field(...)
    value_type: str = Field(default="object", max_length=50)
    validation_schema: dict[str, Any] | None = None


class AIConfigCreate(AIConfigBase):
    """Schema for creating AI configuration."""

    organization_id: UUID | None = None
    is_active: bool = True


class AIConfigUpdate(BaseModel):
    """Schema for updating AI configuration."""

    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    config_value: dict[str, Any] | None = None
    value_type: str | None = Field(default=None, max_length=50)
    validation_schema: dict[str, Any] | None = None
    is_active: bool | None = None
    change_reason: str | None = Field(
        default=None, description="Reason for the configuration change"
    )


class AIConfigResponse(AIConfigBase):
    """Schema for AI configuration response."""

    id: UUID
    organization_id: UUID | None = None
    is_active: bool
    version: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class AIConfigSummary(BaseModel):
    """Compact summary of AI configuration."""

    id: UUID
    category: str
    config_key: str
    display_name: str
    is_active: bool
    value_type: str
    organization_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class AIConfigAuditResponse(BaseModel):
    """Schema for AI configuration audit log entry."""

    id: UUID
    config_id: UUID
    previous_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    change_reason: str | None = None
    changed_by: UUID
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIConfigListResponse(BaseModel):
    """Response for listing AI configurations."""

    items: list[AIConfigSummary]
    total: int
    page: int
    page_size: int


class AIConfigCategoryResponse(BaseModel):
    """Response containing all configs for a category."""

    category: str
    configs: list[AIConfigResponse]


class AIConfigBulkCreate(BaseModel):
    """Schema for bulk creating AI configurations."""

    configs: list[AIConfigCreate] = Field(..., min_length=1)


class AIConfigBulkResponse(BaseModel):
    """Response for bulk AI configuration operations."""

    created: int
    updated: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


# Specific configuration value schemas for type safety


class ScoringWeightsConfig(BaseModel):
    """Schema for deal scoring weights configuration."""

    location_match: float = Field(ge=0, le=1)
    submarket_strength: float = Field(ge=0, le=1)
    tenure_adequacy: float = Field(ge=0, le=1)
    building_age: float = Field(ge=0, le=1)
    gpr_headroom: float = Field(ge=0, le=1)
    seller_motivation: float = Field(ge=0, le=1)
    competition_level: float = Field(ge=0, le=1)
    price_vs_market: float = Field(ge=0, le=1)
    historical_success_rate: float = Field(ge=0, le=1)
    similar_deal_outcomes: float = Field(ge=0, le=1)


class SellerMotivationConfig(BaseModel):
    """Schema for seller motivation categories."""

    high: list[str] = Field(default_factory=list)
    medium: list[str] = Field(default_factory=list)


class ThresholdConfig(BaseModel):
    """Generic threshold configuration."""

    min_years: float | None = None
    min_rate: float | None = None
    min_percent: float | None = None
    min_wins: int | None = None
    max_deviation: float | None = None
    score: float = Field(ge=-1, le=1)


class TimelineConfig(BaseModel):
    """Timeline configuration for compliance prediction."""

    min: int = Field(ge=0)
    max: int = Field(ge=0)
    typical: int = Field(ge=0)


class AllocationTargetConfig(BaseModel):
    """Portfolio allocation target configuration."""

    office: float = Field(ge=0, le=100)
    industrial: float = Field(ge=0, le=100)
    retail: float = Field(ge=0, le=100)
    residential: float = Field(ge=0, le=100)
    mixed_use: float = Field(ge=0, le=100)
    land: float = Field(ge=0, le=100)


class AlertThresholdsConfig(BaseModel):
    """Alert detection thresholds configuration."""

    assumption_deviation_percent: float = Field(ge=0, le=100)
    assumption_deviation_high_percent: float = Field(ge=0, le=100)
    pipeline_velocity_drop_percent: float = Field(le=0)
    pipeline_velocity_drop_high_percent: float = Field(le=0)
    pipeline_growth_percent: float = Field(ge=0)
    regulatory_delay_days: int = Field(ge=0)
    regulatory_delay_high_days: int = Field(ge=0)
    comparable_deviation_percent: float = Field(ge=0, le=100)


class DDItemConfig(BaseModel):
    """Due diligence item configuration."""

    name: str
    description: str
    priority: str = Field(pattern="^(critical|high|medium|low)$")
    auto_completable: bool = False
    source: str | None = None
