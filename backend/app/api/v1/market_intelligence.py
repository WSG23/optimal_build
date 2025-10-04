"""Market intelligence API endpoints."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.metrics import MetricsCollector
from app.models.property import PropertyType
from app.schemas.market import (
    MarketPeriod,
    MarketReportPayload,
    MarketReportResponse,
)
from app.services.agents.market_data_service import MarketDataService
from app.services.agents.market_intelligence_analytics import (
    MarketIntelligenceAnalytics,
)
from app.utils.logging import get_logger, log_event

router = APIRouter(prefix="/market-intelligence", tags=["market-intelligence"])
logger = get_logger(__name__)

_market_data_service = MarketDataService()
_metrics_collector = MetricsCollector()
_market_analytics = MarketIntelligenceAnalytics(
    _market_data_service,
    metrics_collector=_metrics_collector,
)


@router.get("/report", response_model=MarketReportResponse)
async def generate_market_report(
    property_type: PropertyType = Query(..., description="Property type to analyse"),
    location: str = Query("all", description="District or 'all' for nationwide view"),
    period_months: int = Query(
        12, ge=1, le=36, description="Lookback window in months"
    ),
    competitive_set_id: Optional[UUID] = Query(
        None, description="Optional competitive set"
    ),
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
        log_event(
            logger,
            "market_intelligence_report_failed",
            error=str(exc),
            property_type=property_type.value,
            location=location,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate market report: {exc}",
        ) from exc

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
