"""Market intelligence API endpoints."""

from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.property import PropertyType
from app.services.agents.market_data_service import MarketDataService
from app.services.agents.market_intelligence_analytics import (
    MarketIntelligenceAnalytics,
)

router = APIRouter(prefix="/market-intelligence", tags=["market-intelligence"])

_market_data_service = MarketDataService()
_market_analytics = MarketIntelligenceAnalytics(_market_data_service)


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


@router.get("/report", response_model=MarketReportResponse)
async def generate_market_report(
    property_type: PropertyType = Query(..., description="Property type to analyse"),
    location: str = Query("all", description="District or 'all' for nationwide view"),
    period_months: int = Query(12, ge=1, le=36, description="Lookback window in months"),
    competitive_set_id: Optional[UUID] = Query(None, description="Optional competitive set"),
    session: AsyncSession = Depends(get_session),
) -> MarketReportResponse:
    """Return a comprehensive market intelligence report for the requested segment."""

    try:
        report = await _market_analytics.generate_market_report(
            property_type=property_type,
            location=location,
            period_months=period_months,
            session=session,
            competitive_set_id=competitive_set_id,
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=500, detail="Failed to generate market report") from exc

    payload = MarketReportPayload(
        property_type=report.property_type,
        location=report.location,
        period=MarketPeriod(start=report.period[0], end=report.period[1]),
        comparables_analysis=report.comparables,
        supply_dynamics=report.supply,
        yield_benchmarks=report.yields,
        absorption_trends=report.absorption,
        market_cycle_position=report.cycle,
        recommendations=report.recommendations,
    )

    return MarketReportResponse(report=payload, generated_at=report.generated_at)
