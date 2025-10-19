"""Prefect flow for generating market intelligence snapshots."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.property import PropertyType
from app.services.agents.market_data_service import MarketDataService
from app.services.agents.market_intelligence_analytics import (
    MarketIntelligenceAnalytics,
)
from prefect import flow

DEFAULT_LOCATIONS = ("all",)
DEFAULT_PROPERTY_TYPES = (
    PropertyType.OFFICE,
    PropertyType.RETAIL,
)


@flow(name="market-intelligence-refresh")
async def refresh_market_intelligence(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    property_types: Sequence[PropertyType] | None = None,
    locations: Iterable[str] = DEFAULT_LOCATIONS,
    period_months: int = 12,
) -> list[dict[str, Any]]:
    """Run market intelligence analyses for the requested segments."""

    analytics = MarketIntelligenceAnalytics(MarketDataService())
    property_type_list = list(property_types or DEFAULT_PROPERTY_TYPES)
    location_list = list(locations)

    results: list[dict[str, Any]] = []
    async with session_factory() as session:
        for property_type in property_type_list:
            for location in location_list:
                report = await analytics.generate_market_report(
                    property_type=property_type,
                    location=location,
                    period_months=period_months,
                    session=session,
                )
                results.append(report.to_dict())

    return results


__all__ = ["refresh_market_intelligence"]
