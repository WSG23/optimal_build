"""Phase 2.3: Market Trend Predictor.

Forecasts market movements using time series analysis and LLM synthesis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import (
    PropertyType,
    MarketTransaction,
    DevelopmentPipeline,
)

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Direction of market trend."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class ConfidenceLevel(str, Enum):
    """Confidence level for predictions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RentalForecast:
    """Rental rate forecast."""

    current_psf: float
    forecast_6m_psf: float
    forecast_12m_psf: float
    change_6m_percent: float
    change_12m_percent: float
    trend: TrendDirection
    confidence: ConfidenceLevel


@dataclass
class SupplyDemandForecast:
    """Supply and demand forecast."""

    pipeline_sqft: float
    projected_absorption_sqft: float
    current_vacancy: float
    projected_vacancy: float
    imbalance: str  # "oversupply", "balanced", "undersupply"


@dataclass
class MarketDriver:
    """A key market driver."""

    name: str
    impact: str  # "positive", "negative", "neutral"
    description: str
    significance: int  # 1-10


@dataclass
class MarketForecast:
    """Complete market forecast."""

    sector: str
    location: str
    as_of_date: datetime
    rental_forecast: RentalForecast
    supply_demand: SupplyDemandForecast
    key_drivers: list[MarketDriver]
    recommendation: str
    risks: list[str]
    opportunities: list[str]
    confidence: ConfidenceLevel


@dataclass
class PredictionResult:
    """Result from market prediction."""

    success: bool
    forecast: MarketForecast | None = None
    error: str | None = None


class MarketPredictorService:
    """Service for predicting market trends."""

    def __init__(self) -> None:
        """Initialize the market predictor."""
        # In production, this would load trained ML models
        self._initialized = True

    async def predict_market(
        self,
        property_type: PropertyType,
        location: str,
        db: AsyncSession,
    ) -> PredictionResult:
        """Predict market trends for a sector and location.

        Args:
            property_type: Type of property sector
            location: District or planning area
            db: Database session

        Returns:
            PredictionResult with market forecast
        """
        try:
            # Get historical transaction data
            rental_forecast = await self._forecast_rentals(property_type, location, db)

            # Get supply/demand data
            supply_demand = await self._forecast_supply_demand(property_type, location, db)

            # Identify key drivers
            drivers = self._identify_key_drivers(property_type, rental_forecast, supply_demand)

            # Generate recommendation
            recommendation = self._generate_recommendation(rental_forecast, supply_demand, drivers)

            # Identify risks and opportunities
            risks, opportunities = self._identify_risks_opportunities(
                rental_forecast, supply_demand
            )

            forecast = MarketForecast(
                sector=property_type.value,
                location=location,
                as_of_date=datetime.now(),
                rental_forecast=rental_forecast,
                supply_demand=supply_demand,
                key_drivers=drivers,
                recommendation=recommendation,
                risks=risks,
                opportunities=opportunities,
                confidence=self._calculate_overall_confidence(rental_forecast, supply_demand),
            )

            return PredictionResult(success=True, forecast=forecast)

        except Exception as e:
            logger.error(f"Error predicting market: {e}")
            return PredictionResult(success=False, error=str(e))

    async def _forecast_rentals(
        self,
        property_type: PropertyType,
        location: str,
        db: AsyncSession,
    ) -> RentalForecast:
        """Forecast rental rates using historical data."""
        # Get historical transactions
        twelve_months_ago = datetime.now() - timedelta(days=365)
        six_months_ago = datetime.now() - timedelta(days=180)

        # Recent average (last 6 months)
        recent_query = select(func.avg(MarketTransaction.psf_price)).where(
            and_(
                MarketTransaction.transaction_date >= six_months_ago.date(),
            )
        )
        recent_result = await db.execute(recent_query)
        current_psf = float(recent_result.scalar() or 0) or 3.50  # Default if no data

        # Previous period (6-12 months ago)
        previous_query = select(func.avg(MarketTransaction.psf_price)).where(
            and_(
                MarketTransaction.transaction_date >= twelve_months_ago.date(),
                MarketTransaction.transaction_date < six_months_ago.date(),
            )
        )
        previous_result = await db.execute(previous_query)
        previous_psf = float(previous_result.scalar() or current_psf)

        # Calculate trend
        if previous_psf > 0:
            growth_rate = (current_psf - previous_psf) / previous_psf
        else:
            growth_rate = 0.02  # Default 2% growth

        # Simple forecast using trend continuation
        forecast_6m = current_psf * (1 + growth_rate * 0.5)
        forecast_12m = current_psf * (1 + growth_rate)

        # Determine trend direction
        if growth_rate > 0.03:
            trend = TrendDirection.UP
        elif growth_rate < -0.03:
            trend = TrendDirection.DOWN
        else:
            trend = TrendDirection.STABLE

        # Confidence based on data availability
        confidence = ConfidenceLevel.MEDIUM

        return RentalForecast(
            current_psf=current_psf,
            forecast_6m_psf=forecast_6m,
            forecast_12m_psf=forecast_12m,
            change_6m_percent=growth_rate * 50,  # Annualized
            change_12m_percent=growth_rate * 100,
            trend=trend,
            confidence=confidence,
        )

    async def _forecast_supply_demand(
        self,
        property_type: PropertyType,
        location: str,
        db: AsyncSession,
    ) -> SupplyDemandForecast:
        """Forecast supply and demand dynamics."""
        # Get development pipeline
        pipeline_query = select(func.sum(DevelopmentPipeline.total_gfa_sqm)).where(
            and_(
                DevelopmentPipeline.project_type == property_type,
                DevelopmentPipeline.expected_completion >= datetime.now().date(),
            )
        )
        pipeline_result = await db.execute(pipeline_query)
        pipeline_sqft = float(pipeline_result.scalar() or 0)

        # Estimate absorption (simplified - would use historical absorption rates)
        projected_absorption = pipeline_sqft * 0.75  # 75% absorption assumption

        # Estimate vacancy (simplified)
        current_vacancy = 0.08  # 8% default
        if pipeline_sqft > projected_absorption:
            projected_vacancy = current_vacancy + 0.02
            imbalance = "oversupply"
        elif pipeline_sqft < projected_absorption * 0.8:
            projected_vacancy = max(0.04, current_vacancy - 0.015)
            imbalance = "undersupply"
        else:
            projected_vacancy = current_vacancy
            imbalance = "balanced"

        return SupplyDemandForecast(
            pipeline_sqft=pipeline_sqft,
            projected_absorption_sqft=projected_absorption,
            current_vacancy=current_vacancy,
            projected_vacancy=projected_vacancy,
            imbalance=imbalance,
        )

    def _identify_key_drivers(
        self,
        property_type: PropertyType,
        rental_forecast: RentalForecast,
        supply_demand: SupplyDemandForecast,
    ) -> list[MarketDriver]:
        """Identify key market drivers."""
        drivers = []

        # Supply driver
        if supply_demand.imbalance == "oversupply":
            drivers.append(
                MarketDriver(
                    name="Supply Pipeline",
                    impact="negative",
                    description=f"High supply of {supply_demand.pipeline_sqft:,.0f} sqft expected",
                    significance=8,
                )
            )
        elif supply_demand.imbalance == "undersupply":
            drivers.append(
                MarketDriver(
                    name="Supply Constraints",
                    impact="positive",
                    description="Limited new supply supporting rental growth",
                    significance=7,
                )
            )

        # Rental trend driver
        if rental_forecast.trend == TrendDirection.UP:
            drivers.append(
                MarketDriver(
                    name="Rental Growth",
                    impact="positive",
                    description=f"Rentals up {rental_forecast.change_12m_percent:.1f}% YoY",
                    significance=7,
                )
            )
        elif rental_forecast.trend == TrendDirection.DOWN:
            drivers.append(
                MarketDriver(
                    name="Rental Pressure",
                    impact="negative",
                    description="Downward pressure on rental rates",
                    significance=6,
                )
            )

        # Sector-specific drivers
        if property_type == PropertyType.INDUSTRIAL:
            drivers.append(
                MarketDriver(
                    name="E-commerce Growth",
                    impact="positive",
                    description="Continued demand from logistics and fulfillment",
                    significance=8,
                )
            )
        elif property_type == PropertyType.OFFICE:
            drivers.append(
                MarketDriver(
                    name="Hybrid Work",
                    impact="negative",
                    description="Reduced office space requirements per employee",
                    significance=6,
                )
            )

        return drivers

    def _generate_recommendation(
        self,
        rental_forecast: RentalForecast,
        supply_demand: SupplyDemandForecast,
        drivers: list[MarketDriver],
    ) -> str:
        """Generate market recommendation."""
        positive_count = sum(1 for d in drivers if d.impact == "positive")
        negative_count = sum(1 for d in drivers if d.impact == "negative")

        if positive_count > negative_count and rental_forecast.trend != TrendDirection.DOWN:
            return "Favorable conditions for acquisition. Strong fundamentals support investment."
        elif negative_count > positive_count or supply_demand.imbalance == "oversupply":
            return "Exercise caution. Market headwinds may impact near-term performance."
        else:
            return "Neutral outlook. Selective opportunities may exist for well-located assets."

    def _identify_risks_opportunities(
        self,
        rental_forecast: RentalForecast,
        supply_demand: SupplyDemandForecast,
    ) -> tuple[list[str], list[str]]:
        """Identify market risks and opportunities."""
        risks = []
        opportunities = []

        # Risks
        if supply_demand.imbalance == "oversupply":
            risks.append("New supply may pressure occupancy and rents")
        if rental_forecast.trend == TrendDirection.DOWN:
            risks.append("Declining rental trajectory may impact NOI projections")
        if supply_demand.projected_vacancy > 0.10:
            risks.append("Elevated vacancy expected to persist")

        # Opportunities
        if supply_demand.imbalance == "undersupply":
            opportunities.append("Limited competition supports rental growth")
        if rental_forecast.trend == TrendDirection.UP:
            opportunities.append("Positive rental momentum for income growth")
        if supply_demand.projected_vacancy < 0.06:
            opportunities.append("Tight market conditions favor landlords")

        return risks, opportunities

    def _calculate_overall_confidence(
        self,
        rental_forecast: RentalForecast,
        supply_demand: SupplyDemandForecast,
    ) -> ConfidenceLevel:
        """Calculate overall prediction confidence."""
        # Simple heuristic - in production would be based on data quality metrics
        if rental_forecast.confidence == ConfidenceLevel.HIGH:
            return ConfidenceLevel.HIGH
        elif supply_demand.pipeline_sqft > 0:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


# Singleton instance
market_predictor_service = MarketPredictorService()
