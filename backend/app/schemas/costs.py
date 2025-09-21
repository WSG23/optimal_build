"""Pydantic schemas for cost APIs."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class CostIndex(BaseModel):
    """Cost index response schema."""

    id: int
    series_name: str
    jurisdiction: str
    category: str
    subcategory: Optional[str]
    period: str
    value: Decimal
    unit: str
    source: Optional[str]
    provider: str
    methodology: Optional[str]

    class Config:
        """Pydantic configuration."""

        from_attributes = True
