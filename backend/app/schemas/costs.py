"""Pydantic schemas for cost APIs."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CostIndex(BaseModel):
    """Cost index response schema."""

    id: int
    series_name: str
    jurisdiction: str
    category: str
    subcategory: str | None
    period: str
    value: Decimal
    unit: str
    source: str | None
    provider: str
    methodology: str | None

    model_config = ConfigDict(from_attributes=True)
