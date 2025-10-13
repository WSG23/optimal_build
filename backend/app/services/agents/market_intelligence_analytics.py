"""Market Intelligence Analytics Service for commercial property analysis."""

import statistics
from datetime import date, timedelta
from typing import Any
from uuid import UUID

try:  # pragma: no cover - optional dependency
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - fallback when pandas missing
    pd = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - fallback when numpy missing
    np = None  # type: ignore[assignment]
from sqlalchemy import String, and_, cast, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.market import (
    AbsorptionTracking,
    MarketCycle,
    MarketIndex,
    YieldBenchmark,
)
from app.models.property import MarketTransaction, Property, PropertyType
from app.services.agents.market_data_service import MarketDataService
from backend._compat.datetime import utcnow

try:  # pragma: no cover - optional metrics dependency
    from app.core.metrics import MetricsCollector
except ImportError:  # pragma: no cover - fallback stub

    class MetricsCollector:  # type: ignore
        """Fallback metrics collector that performs no operations."""

        def record(self, *args: Any, **kwargs: Any) -> None:
            return None


import structlog

logger = structlog.get_logger()


class MarketReport:
    """Comprehensive market intelligence report."""

    def __init__(
        self,
        property_type: PropertyType,
        location: str,
        period: tuple[date, date],
        comparables_analysis: dict[str, Any],
        supply_dynamics: dict[str, Any],
        yield_benchmarks: dict[str, Any],
        absorption_trends: dict[str, Any],
        market_cycle_position: dict[str, Any],
        recommendations: list[str],
    ):
        self.property_type = property_type
        self.location = location
        self.period = period
        self.comparables = comparables_analysis
        self.supply = supply_dynamics
        self.yields = yield_benchmarks
        self.absorption = absorption_trends
        self.cycle = market_cycle_position
        self.recommendations = recommendations
        self.generated_at = utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "property_type": self.property_type.value,
            "location": self.location,
            "period": {
                "start": self.period[0].isoformat(),
                "end": self.period[1].isoformat(),
            },
            "comparables_analysis": self.comparables,
            "supply_dynamics": self.supply,
            "yield_benchmarks": self.yields,
            "absorption_trends": self.absorption,
            "market_cycle_position": self.cycle,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat(),
        }


class MarketIntelligenceAnalytics:
    """Service for comprehensive market intelligence and analytics."""

    def __init__(
        self,
        market_data_service: MarketDataService,
        metrics_collector: MetricsCollector | None = None,
    ):
        if pd is None or np is None:
            raise ImportError(
                "MarketIntelligenceAnalytics requires 'pandas' and 'numpy'."
            )
        self.market_data = market_data_service
        self.metrics = metrics_collector

    async def generate_market_report(
        self,
        property_type: PropertyType,
        location: str,
        period_months: int,
        session: AsyncSession,
        competitive_set_id: UUID | None = None,
    ) -> MarketReport:
        """
        Generate comprehensive market intelligence report.

        Args:
            property_type: Type of property to analyze
            location: District or area to analyze
            period_months: Number of months to analyze
            session: Database session
            competitive_set_id: Optional specific competitive set

        Returns:
            Comprehensive market report
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=period_months * 30)
        period = (start_date, end_date)

        # Run all analyses in parallel where possible
        comparables = await self._analyze_comparables(
            property_type, location, period, session
        )

        supply_dynamics = await self._analyze_supply_dynamics(
            property_type, location, period, session
        )

        yield_benchmarks = await self._analyze_yield_benchmarks(
            property_type, location, period, session
        )

        absorption_trends = await self._analyze_absorption_trends(
            property_type, location, period, session
        )

        market_cycle = await self._analyze_market_cycle(
            property_type, location, session
        )

        # Generate insights and recommendations
        recommendations = self._generate_recommendations(
            comparables,
            supply_dynamics,
            yield_benchmarks,
            absorption_trends,
            market_cycle,
        )

        # Record metrics if available
        if self.metrics:
            self._record_metrics(property_type, location, yield_benchmarks)

        return MarketReport(
            property_type=property_type,
            location=location,
            period=period,
            comparables_analysis=comparables,
            supply_dynamics=supply_dynamics,
            yield_benchmarks=yield_benchmarks,
            absorption_trends=absorption_trends,
            market_cycle_position=market_cycle,
            recommendations=recommendations,
        )

    async def _analyze_comparables(
        self,
        property_type: PropertyType,
        location: str,
        period: tuple[date, date],
        session: AsyncSession,
    ) -> dict[str, Any]:
        """Analyze comparable transactions."""

        # Get recent transactions
        stmt = (
            select(MarketTransaction)
            .join(Property, MarketTransaction.property_id == Property.id)
            .where(
                Property.property_type == property_type,
                MarketTransaction.transaction_date.between(period[0], period[1]),
            )
            .options(selectinload(MarketTransaction.property))
        )

        if location != "all":
            stmt = stmt.where(Property.district == location)

        result = await session.execute(stmt)
        transactions = result.scalars().all()

        if not transactions:
            return {
                "transaction_count": 0,
                "message": "No comparable transactions found",
            }

        # Calculate statistics
        psf_prices = [float(t.psf_price) for t in transactions if t.psf_price]
        sale_prices = [float(t.sale_price) for t in transactions]

        # Group by quarters
        quarterly_data = self._group_by_quarter(transactions)

        # Price trends
        price_trend = self._calculate_price_trend(quarterly_data)

        return {
            "transaction_count": len(transactions),
            "total_volume": sum(sale_prices),
            "average_psf": statistics.mean(psf_prices) if psf_prices else 0,
            "median_psf": statistics.median(psf_prices) if psf_prices else 0,
            "psf_range": {
                "min": min(psf_prices) if psf_prices else 0,
                "max": max(psf_prices) if psf_prices else 0,
            },
            "quarterly_trends": quarterly_data,
            "price_trend": price_trend,
            "top_transactions": self._get_top_transactions(transactions, 5),
            "buyer_profile": self._analyze_buyer_profile(transactions),
        }

    async def _analyze_supply_dynamics(
        self,
        property_type: PropertyType,
        location: str,
        period: tuple[date, date],
        session: AsyncSession,
    ) -> dict[str, Any]:
        """Analyze supply pipeline and dynamics."""

        from app.models.property import DevelopmentPipeline, PropertyStatus

        # Get upcoming supply
        stmt = select(DevelopmentPipeline).where(
            and_(
                DevelopmentPipeline.project_type == property_type,
                DevelopmentPipeline.development_status.in_(
                    [
                        PropertyStatus.PLANNED,
                        PropertyStatus.APPROVED,
                        PropertyStatus.UNDER_CONSTRUCTION,
                    ]
                ),
            )
        )

        if location != "all":
            stmt = stmt.where(DevelopmentPipeline.district == location)

        result = await session.execute(stmt)
        pipeline_projects = result.scalars().all()

        # Group by completion timeline
        supply_by_year = {}
        total_upcoming_gfa = 0

        for project in pipeline_projects:
            if project.expected_completion:
                year = project.expected_completion.year
                if year not in supply_by_year:
                    supply_by_year[year] = {
                        "projects": 0,
                        "total_gfa": 0,
                        "total_units": 0,
                    }

                supply_by_year[year]["projects"] += 1
                supply_by_year[year]["total_gfa"] += float(project.total_gfa_sqm or 0)
                supply_by_year[year]["total_units"] += project.total_units or 0
                total_upcoming_gfa += float(project.total_gfa_sqm or 0)

        # Calculate supply pressure
        supply_pressure = self._calculate_supply_pressure(
            total_upcoming_gfa, property_type, location
        )

        return {
            "pipeline_projects": len(pipeline_projects),
            "total_upcoming_gfa": total_upcoming_gfa,
            "supply_by_year": supply_by_year,
            "supply_pressure": supply_pressure,
            "major_developments": self._get_major_developments(pipeline_projects),
            "market_impact": self._assess_supply_impact(
                total_upcoming_gfa, property_type
            ),
        }

    async def _analyze_yield_benchmarks(
        self,
        property_type: PropertyType,
        location: str,
        period: tuple[date, date],
        session: AsyncSession,
    ) -> dict[str, Any]:
        """Analyze yield benchmarks and trends."""

        # Normalize property type for databases where enum metadata may be missing
        property_type_value = (
            property_type.value
            if isinstance(property_type, PropertyType)
            else str(property_type)
        )

        stmt = (
            select(YieldBenchmark)
            .where(
                and_(
                    cast(YieldBenchmark.property_type, String)
                    == literal(property_type_value, String()),
                    YieldBenchmark.benchmark_date.between(period[0], period[1]),
                )
            )
            .order_by(YieldBenchmark.benchmark_date)
        )

        if location != "all":
            stmt = stmt.where(YieldBenchmark.district == location)

        result = await session.execute(stmt)
        benchmarks = result.scalars().all()

        if not benchmarks:
            return {
                "message": "No yield data available",
                "cap_rates": {},
                "rental_rates": {},
            }

        # Get latest benchmark
        latest = benchmarks[-1]

        # Calculate trends
        cap_rate_trend = self._calculate_yield_trend(benchmarks, "cap_rate_median")
        rental_trend = self._calculate_yield_trend(benchmarks, "rental_psf_median")

        # Historical comparison
        yoy_comparison = self._calculate_yoy_change(benchmarks)

        return {
            "current_metrics": {
                "cap_rate": {
                    "mean": float(latest.cap_rate_mean or 0),
                    "median": float(latest.cap_rate_median or 0),
                    "range": {
                        "p25": float(latest.cap_rate_p25 or 0),
                        "p75": float(latest.cap_rate_p75 or 0),
                    },
                },
                "rental_rates": {
                    "mean_psf": float(latest.rental_psf_mean or 0),
                    "median_psf": float(latest.rental_psf_median or 0),
                    "occupancy": float(latest.occupancy_rate_mean or 0),
                },
                "transaction_volume": {
                    "count": latest.transaction_count or 0,
                    "total_value": float(latest.total_transaction_value or 0),
                },
            },
            "trends": {"cap_rate_trend": cap_rate_trend, "rental_trend": rental_trend},
            "yoy_changes": yoy_comparison,
            "market_position": self._assess_yield_position(latest, property_type),
        }

    async def _analyze_absorption_trends(
        self,
        property_type: PropertyType,
        location: str,
        period: tuple[date, date],
        session: AsyncSession,
    ) -> dict[str, Any]:
        """Analyze absorption and velocity trends."""

        # Get absorption tracking data
        stmt = (
            select(AbsorptionTracking)
            .where(
                and_(
                    AbsorptionTracking.property_type == property_type,
                    AbsorptionTracking.tracking_date.between(period[0], period[1]),
                )
            )
            .order_by(AbsorptionTracking.tracking_date)
        )

        if location != "all":
            stmt = stmt.where(AbsorptionTracking.district == location)

        result = await session.execute(stmt)
        absorption_data = result.scalars().all()

        if not absorption_data:
            return {"message": "No absorption data available", "metrics": {}}

        # Calculate key metrics
        latest_data = absorption_data[-1]

        # Average absorption rates
        avg_sales_absorption = statistics.mean(
            [float(d.sales_absorption_rate or 0) for d in absorption_data]
        )
        avg_leasing_absorption = statistics.mean(
            [float(d.leasing_absorption_rate or 0) for d in absorption_data]
        )

        # Velocity trends
        velocity_trend = self._analyze_velocity_trend(absorption_data)

        # Forecast
        absorption_forecast = self._forecast_absorption(absorption_data, months_ahead=6)

        return {
            "current_metrics": {
                "sales_absorption_rate": float(latest_data.sales_absorption_rate or 0),
                "leasing_absorption_rate": float(
                    latest_data.leasing_absorption_rate or 0
                ),
                "avg_days_to_sale": latest_data.avg_days_to_sale or 0,
                "avg_days_to_lease": latest_data.avg_days_to_lease or 0,
            },
            "period_averages": {
                "avg_sales_absorption": avg_sales_absorption,
                "avg_leasing_absorption": avg_leasing_absorption,
            },
            "velocity_trend": velocity_trend,
            "market_comparison": {
                "vs_market_average": float(latest_data.relative_performance or 0)
            },
            "forecast": absorption_forecast,
            "seasonal_patterns": self._detect_seasonal_patterns(absorption_data),
        }

    async def _analyze_market_cycle(
        self, property_type: PropertyType, location: str, session: AsyncSession
    ) -> dict[str, Any]:
        """Analyze current position in market cycle."""

        # Get market cycle data
        stmt = (
            select(MarketCycle)
            .where(MarketCycle.property_type == property_type)
            .order_by(MarketCycle.cycle_date.desc())
            .limit(1)
        )

        result = await session.execute(stmt)
        current_cycle = result.scalar_one_or_none()

        if not current_cycle:
            return {
                "phase": "unknown",
                "indicators": {},
                "outlook": "insufficient data",
            }

        # Get market indices for trend analysis
        indices = await self._get_market_indices(property_type, session)

        # Determine cycle position
        cycle_position = {
            "current_phase": current_cycle.cycle_phase,
            "phase_duration_months": current_cycle.phase_duration_months,
            "phase_strength": float(current_cycle.phase_strength or 0),
            "indicators": {
                "price_momentum": float(current_cycle.price_momentum or 0),
                "rental_momentum": float(current_cycle.rental_momentum or 0),
                "transaction_volume_change": float(
                    current_cycle.transaction_volume_change or 0
                ),
                "supply_demand_ratio": float(current_cycle.supply_demand_ratio or 0),
            },
            "outlook": {
                "next_12_months": current_cycle.cycle_outlook,
                "pipeline_impact": float(current_cycle.pipeline_supply_12m or 0),
                "demand_forecast": float(current_cycle.expected_demand_12m or 0),
            },
        }

        # Add index trends
        if indices:
            cycle_position["index_trends"] = self._analyze_index_trends(indices)

        return cycle_position

    # Helper methods

    def _group_by_quarter(
        self, transactions: list[MarketTransaction]
    ) -> dict[str, Any]:
        """Group transactions by quarter."""
        quarterly = {}

        for txn in transactions:
            quarter = (
                f"{txn.transaction_date.year}-Q{(txn.transaction_date.month-1)//3 + 1}"
            )

            if quarter not in quarterly:
                quarterly[quarter] = {"count": 0, "total_volume": 0, "avg_psf": []}

            quarterly[quarter]["count"] += 1
            quarterly[quarter]["total_volume"] += float(txn.sale_price)
            if txn.psf_price:
                quarterly[quarter]["avg_psf"].append(float(txn.psf_price))

        # Calculate averages
        for _quarter, data in quarterly.items():
            if data["avg_psf"]:
                data["avg_psf"] = statistics.mean(data["avg_psf"])
            else:
                data["avg_psf"] = 0

        return quarterly

    def _calculate_price_trend(self, quarterly_data: dict[str, Any]) -> str:
        """Calculate price trend from quarterly data."""
        if len(quarterly_data) < 2:
            return "insufficient_data"

        quarters = sorted(quarterly_data.keys())
        prices = [quarterly_data[q]["avg_psf"] for q in quarters]

        # Simple linear trend
        if len(prices) >= 2:
            recent_avg = statistics.mean(prices[-2:])
            older_avg = statistics.mean(prices[:-2]) if len(prices) > 2 else prices[0]

            change_pct = (
                ((recent_avg - older_avg) / older_avg) * 100 if older_avg else 0
            )

            if change_pct > 5:
                return "upward"
            elif change_pct < -5:
                return "downward"
            else:
                return "stable"

        return "stable"

    def _get_top_transactions(
        self, transactions: list[MarketTransaction], limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get top transactions by value."""
        sorted_txns = sorted(transactions, key=lambda x: x.sale_price, reverse=True)[
            :limit
        ]

        return [
            {
                "date": txn.transaction_date.isoformat(),
                "property_name": txn.property.name if txn.property else "Unknown",
                "price": float(txn.sale_price),
                "psf": float(txn.psf_price) if txn.psf_price else None,
                "buyer_type": txn.buyer_type,
            }
            for txn in sorted_txns
        ]

    def _analyze_buyer_profile(
        self, transactions: list[MarketTransaction]
    ) -> dict[str, int]:
        """Analyze buyer type distribution."""
        buyer_types = {}

        for txn in transactions:
            buyer_type = txn.buyer_type or "Unknown"
            buyer_types[buyer_type] = buyer_types.get(buyer_type, 0) + 1

        return buyer_types

    def _calculate_supply_pressure(
        self, upcoming_gfa: float, property_type: PropertyType, location: str
    ) -> str:
        """Calculate supply pressure level."""
        # Simplified - in production, compare to existing stock

        thresholds = {
            PropertyType.OFFICE: 500000,  # sqm
            PropertyType.RETAIL: 200000,
            PropertyType.RESIDENTIAL: 1000000,
            PropertyType.INDUSTRIAL: 300000,
        }

        threshold = thresholds.get(property_type, 500000)

        if upcoming_gfa > threshold * 1.5:
            return "high"
        elif upcoming_gfa > threshold:
            return "moderate"
        else:
            return "low"

    def _get_major_developments(
        self, projects: list[Any], limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get major development projects."""
        sorted_projects = sorted(
            projects, key=lambda x: x.total_gfa_sqm or 0, reverse=True
        )[:limit]

        return [
            {
                "name": proj.project_name,
                "developer": proj.developer,
                "gfa": float(proj.total_gfa_sqm or 0),
                "units": proj.total_units,
                "completion": (
                    proj.expected_completion.isoformat()
                    if proj.expected_completion
                    else None
                ),
                "status": proj.development_status.value,
            }
            for proj in sorted_projects
        ]

    def _assess_supply_impact(
        self, upcoming_gfa: float, property_type: PropertyType
    ) -> str:
        """Assess market impact of upcoming supply."""
        pressure = self._calculate_supply_pressure(upcoming_gfa, property_type, "")

        impact_messages = {
            "high": "Significant supply influx expected - potential downward pressure on rents and prices",
            "moderate": "Balanced supply additions - market should absorb without major disruption",
            "low": "Limited new supply - potential for rental and price growth",
        }

        return impact_messages.get(pressure, "Unable to assess impact")

    def _calculate_yield_trend(
        self, benchmarks: list[YieldBenchmark], metric: str
    ) -> str:
        """Calculate trend for yield metric."""
        if len(benchmarks) < 2:
            return "insufficient_data"

        values = [getattr(b, metric) for b in benchmarks if getattr(b, metric)]

        if len(values) < 2:
            return "insufficient_data"

        # Compare recent to older values
        recent = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
        older = statistics.mean(values[:-3]) if len(values) > 3 else values[0]

        change = ((float(recent) - float(older)) / float(older)) * 100 if older else 0

        if abs(change) < 2:
            return "stable"
        elif change > 0:
            return "increasing"
        else:
            return "decreasing"

    def _calculate_yoy_change(
        self, benchmarks: list[YieldBenchmark]
    ) -> dict[str, float]:
        """Calculate year-over-year changes."""
        if len(benchmarks) < 12:
            return {}

        current = benchmarks[-1]
        year_ago = None

        # Find benchmark from ~12 months ago
        target_date = current.benchmark_date - timedelta(days=365)
        for b in benchmarks:
            if abs((b.benchmark_date - target_date).days) < 30:
                year_ago = b
                break

        if not year_ago:
            return {}

        return {
            "cap_rate_change_bps": float(
                (current.cap_rate_median or 0) - (year_ago.cap_rate_median or 0)
            )
            * 100,
            "rental_change_pct": float(
                ((current.rental_psf_median or 0) - (year_ago.rental_psf_median or 0))
                / (year_ago.rental_psf_median or 1)
            )
            * 100,
            "transaction_volume_change_pct": float(
                (
                    (current.total_transaction_value or 0)
                    - (year_ago.total_transaction_value or 0)
                )
                / (year_ago.total_transaction_value or 1)
            )
            * 100,
        }

    def _assess_yield_position(
        self, benchmark: YieldBenchmark, property_type: PropertyType
    ) -> str:
        """Assess current yield position in market."""
        # Simplified assessment based on cap rates
        cap_rate = float(benchmark.cap_rate_median or 0)

        # Typical ranges by property type (simplified)
        attractive_ranges = {
            PropertyType.OFFICE: (4.0, 5.5),
            PropertyType.RETAIL: (5.0, 7.0),
            PropertyType.INDUSTRIAL: (6.0, 8.0),
            PropertyType.RESIDENTIAL: (3.0, 4.5),
        }

        min_rate, max_rate = attractive_ranges.get(property_type, (4.0, 6.0))

        if cap_rate < min_rate:
            return "yields_compressed"
        elif cap_rate > max_rate:
            return "yields_elevated"
        else:
            return "yields_normal"

    def _analyze_velocity_trend(self, absorption_data: list[AbsorptionTracking]) -> str:
        """Analyze absorption velocity trend."""
        if len(absorption_data) < 3:
            return "insufficient_data"

        # Get recent vs older velocity
        recent_velocity = statistics.mean(
            [d.avg_units_per_month or 0 for d in absorption_data[-3:]]
        )

        older_velocity = statistics.mean(
            [d.avg_units_per_month or 0 for d in absorption_data[:-3]]
        )

        if older_velocity == 0:
            return "stable"

        change = ((recent_velocity - older_velocity) / older_velocity) * 100

        if change > 10:
            return "accelerating"
        elif change < -10:
            return "decelerating"
        else:
            return "stable"

    def _forecast_absorption(
        self, absorption_data: list[AbsorptionTracking], months_ahead: int = 6
    ) -> dict[str, Any]:
        """Simple absorption forecast."""
        if len(absorption_data) < 3:
            return {"message": "Insufficient data for forecast"}

        # Calculate average absorption rate
        avg_absorption = statistics.mean(
            [float(d.sales_absorption_rate or 0) for d in absorption_data[-6:]]
        )

        # Simple linear projection
        current_absorbed = float(absorption_data[-1].sales_absorption_rate or 0)
        projected_absorbed = min(
            current_absorbed + (avg_absorption * months_ahead / 100), 100
        )

        # Estimate sellout timeline
        if avg_absorption > 0:
            # Protect against division by zero when avg_absorption is very small
            absorption_rate = avg_absorption / 100
            if absorption_rate > 0.001:  # More than 0.1% monthly absorption
                months_to_sellout = (100 - current_absorbed) / absorption_rate
            else:
                months_to_sellout = None  # Too slow to estimate
        else:
            months_to_sellout = None

        return {
            "current_absorption": current_absorbed,
            "projected_absorption_6m": projected_absorbed,
            "avg_monthly_absorption": avg_absorption,
            "estimated_sellout_months": months_to_sellout,
        }

    def _detect_seasonal_patterns(
        self, absorption_data: list[AbsorptionTracking]
    ) -> dict[str, Any]:
        """Detect seasonal patterns in absorption."""
        if len(absorption_data) < 12:
            return {"message": "Insufficient data for seasonal analysis"}

        # Group by month
        monthly_absorption = {}
        for data in absorption_data:
            month = data.tracking_date.month
            if month not in monthly_absorption:
                monthly_absorption[month] = []
            monthly_absorption[month].append(float(data.sales_absorption_rate or 0))

        # Calculate monthly averages
        monthly_avg = {
            month: statistics.mean(values)
            for month, values in monthly_absorption.items()
        }

        # Identify peak and low months
        if monthly_avg:
            peak_month = max(monthly_avg.items(), key=lambda x: x[1])
            low_month = min(monthly_avg.items(), key=lambda x: x[1])

            return {
                "peak_month": peak_month[0],
                "peak_absorption": peak_month[1],
                "low_month": low_month[0],
                "low_absorption": low_month[1],
                "seasonality_strength": (
                    (peak_month[1] - low_month[1]) / low_month[1] if low_month[1] else 0
                ),
            }

        return {}

    async def _get_market_indices(
        self, property_type: PropertyType, session: AsyncSession
    ) -> list[MarketIndex]:
        """Get market indices for property type."""
        stmt = (
            select(MarketIndex)
            .where(MarketIndex.property_type == property_type)
            .order_by(MarketIndex.index_date.desc())
            .limit(12)
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    def _analyze_index_trends(self, indices: list[MarketIndex]) -> dict[str, Any]:
        """Analyze market index trends."""
        if not indices:
            return {}

        latest = indices[0]

        return {
            "current_index": float(latest.index_value),
            "mom_change": float(latest.mom_change or 0),
            "qoq_change": float(latest.qoq_change or 0),
            "yoy_change": float(latest.yoy_change or 0),
            "trend": self._determine_index_trend(indices),
        }

    def _determine_index_trend(self, indices: list[MarketIndex]) -> str:
        """Determine overall index trend."""
        if len(indices) < 3:
            return "insufficient_data"

        # Check last 3 months direction
        changes = [i.mom_change for i in indices[:3] if i.mom_change is not None]

        if all(c > 0 for c in changes):
            return "uptrend"
        elif all(c < 0 for c in changes):
            return "downtrend"
        else:
            return "sideways"

    def _generate_recommendations(
        self,
        comparables: dict[str, Any],
        supply: dict[str, Any],
        yields: dict[str, Any],
        absorption: dict[str, Any],
        cycle: dict[str, Any],
    ) -> list[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Price trend recommendations
        if comparables.get("price_trend") == "upward":
            recommendations.append(
                "Consider accelerating sales/leasing efforts to capture current price momentum"
            )
        elif comparables.get("price_trend") == "downward":
            recommendations.append(
                "Focus on value-add initiatives and differentiation to maintain pricing power"
            )

        # Supply pressure recommendations
        if supply.get("supply_pressure") == "high":
            recommendations.append(
                "High supply pressure ahead - prioritize quick absorption and consider competitive pricing"
            )
        elif supply.get("supply_pressure") == "low":
            recommendations.append(
                "Limited new supply creates pricing opportunity - consider premium positioning"
            )

        # Yield recommendations
        if yields.get("market_position") == "yields_compressed":
            recommendations.append(
                "Compressed yields suggest market peak - focus on income stability over capital growth"
            )
        elif yields.get("market_position") == "yields_elevated":
            recommendations.append(
                "Elevated yields may present buying opportunity for long-term investors"
            )

        # Absorption recommendations
        velocity = absorption.get("velocity_trend")
        if velocity == "accelerating":
            recommendations.append(
                "Absorption accelerating - maintain momentum with targeted marketing"
            )
        elif velocity == "decelerating":
            recommendations.append(
                "Absorption slowing - consider incentives or product adjustments"
            )

        # Cycle recommendations
        phase = cycle.get("current_phase")
        if phase == "expansion":
            recommendations.append(
                "Market in expansion phase - optimize for revenue growth"
            )
        elif phase == "hyper_supply":
            recommendations.append(
                "Entering oversupply phase - focus on occupancy over rental growth"
            )
        elif phase == "recession":
            recommendations.append(
                "Market downturn - prioritize tenant retention and cost management"
            )
        elif phase == "recovery":
            recommendations.append(
                "Market recovering - position for upcoming growth cycle"
            )

        # Always add data-driven decision making
        recommendations.append(
            "Continue monitoring market indicators weekly for early trend detection"
        )

        return recommendations

    def _record_metrics(
        self, property_type: PropertyType, location: str, yields: dict[str, Any]
    ):
        """Record metrics for monitoring."""
        if not self.metrics:
            return

        # Record current cap rate
        if yields.get("current_metrics", {}).get("cap_rate", {}).get("median"):
            self.metrics.record_gauge(
                "market_intelligence.cap_rate",
                yields["current_metrics"]["cap_rate"]["median"],
                tags={"property_type": property_type.value, "location": location},
            )

        # Record rental rates
        if yields.get("current_metrics", {}).get("rental_rates", {}).get("median_psf"):
            self.metrics.record_gauge(
                "market_intelligence.rental_psf",
                yields["current_metrics"]["rental_rates"]["median_psf"],
                tags={"property_type": property_type.value, "location": location},
            )
