"""Pydantic schemas for market intelligence payloads."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict

from app.models.property import PropertyType


class MarketPeriod(BaseModel):
    """Reporting window for market analytics."""

    start: date
    end: date


class MarketReportPayload(BaseModel):
    """Structured market intelligence report payload."""

    property_type: PropertyType
    location: str
    period: MarketPeriod
    comparables_analysis: Dict[str, Any]
    supply_dynamics: Dict[str, Any]
    yield_benchmarks: Dict[str, Any]
    absorption_trends: Dict[str, Any]
    market_cycle_position: Dict[str, Any]
    recommendations: List[str]


class MarketReportResponse(BaseModel):
    """API response envelope for market intelligence reports."""

    report: MarketReportPayload
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "MarketPeriod",
    "MarketReportPayload",
    "MarketReportResponse",
]
