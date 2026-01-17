"""Phase 4.4: Competitive Intelligence.

AI-powered competitor tracking and market intelligence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import MarketTransaction, DevelopmentPipeline
from app.models.business_performance import AgentDeal

logger = logging.getLogger(__name__)


class CompetitorType(str, Enum):
    """Types of competitors."""

    DEVELOPER = "developer"
    INVESTOR = "investor"
    REIT = "reit"
    FUND = "fund"
    FAMILY_OFFICE = "family_office"


class IntelligenceCategory(str, Enum):
    """Categories of intelligence."""

    TRANSACTION = "transaction"
    DEVELOPMENT = "development"
    MARKET_ENTRY = "market_entry"
    DIVESTMENT = "divestment"
    PARTNERSHIP = "partnership"
    REGULATORY = "regulatory"


class AlertPriority(str, Enum):
    """Priority levels for intelligence alerts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Competitor:
    """A competitor entity."""

    id: str
    name: str
    competitor_type: CompetitorType
    focus_sectors: list[str]
    focus_districts: list[str]
    estimated_aum: float | None = None
    recent_activity_count: int = 0
    threat_level: str = "medium"


@dataclass
class CompetitorActivity:
    """An activity by a competitor."""

    id: str
    competitor_id: str
    competitor_name: str
    category: IntelligenceCategory
    title: str
    description: str
    location: str | None = None
    value: float | None = None
    detected_at: datetime = field(default_factory=datetime.now)
    source: str | None = None
    relevance_score: float = 0.5


@dataclass
class MarketIntelligence:
    """Market intelligence insight."""

    id: str
    category: str
    title: str
    insight: str
    data_points: list[dict[str, Any]]
    impact: str
    recommendation: str
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CompetitiveAlert:
    """An intelligence alert."""

    id: str
    priority: AlertPriority
    title: str
    description: str
    competitor_id: str | None = None
    competitor_name: str | None = None
    activity_id: str | None = None
    action_required: str | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class IntelligenceDashboard:
    """Dashboard of competitive intelligence."""

    competitors: list[Competitor]
    recent_activities: list[CompetitorActivity]
    alerts: list[CompetitiveAlert]
    market_insights: list[MarketIntelligence]
    summary: str
    generated_at: datetime = field(default_factory=datetime.now)


class CompetitiveIntelligenceService:
    """Service for competitive intelligence."""

    llm: Optional[ChatOpenAI]

    def __init__(self) -> None:
        """Initialize the service."""
        try:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0.3,
            )
            self._initialized = True
            self._competitors: dict[str, Competitor] = {}
            self._activities: list[CompetitorActivity] = []
            self._alerts: list[CompetitiveAlert] = []

            # Initialize with known market players
            self._initialize_competitors()
        except Exception as e:
            logger.warning(f"Competitive Intelligence not initialized: {e}")
            self._initialized = False
            self.llm = None
            self._competitors = {}
            self._activities = []
            self._alerts = []

    def _initialize_competitors(self) -> None:
        """Initialize with known market competitors."""
        known_competitors = [
            Competitor(
                id="comp_1",
                name="CapitaLand",
                competitor_type=CompetitorType.DEVELOPER,
                focus_sectors=["office", "retail", "residential", "industrial"],
                focus_districts=["CBD", "Jurong", "Tampines"],
                estimated_aum=50_000_000_000,
                threat_level="high",
            ),
            Competitor(
                id="comp_2",
                name="Mapletree",
                competitor_type=CompetitorType.REIT,
                focus_sectors=["industrial", "logistics", "office"],
                focus_districts=["Jurong", "Tuas", "CBD"],
                estimated_aum=30_000_000_000,
                threat_level="high",
            ),
            Competitor(
                id="comp_3",
                name="Frasers Property",
                competitor_type=CompetitorType.DEVELOPER,
                focus_sectors=["residential", "retail", "industrial"],
                focus_districts=["Orchard", "CBD", "North"],
                estimated_aum=20_000_000_000,
                threat_level="medium",
            ),
            Competitor(
                id="comp_4",
                name="Keppel",
                competitor_type=CompetitorType.DEVELOPER,
                focus_sectors=["office", "mixed_use", "data_center"],
                focus_districts=["CBD", "Changi", "Tuas"],
                estimated_aum=25_000_000_000,
                threat_level="high",
            ),
            Competitor(
                id="comp_5",
                name="Lendlease",
                competitor_type=CompetitorType.DEVELOPER,
                focus_sectors=["mixed_use", "residential"],
                focus_districts=["Paya Lebar", "CBD"],
                estimated_aum=15_000_000_000,
                threat_level="medium",
            ),
        ]

        for comp in known_competitors:
            self._competitors[comp.id] = comp

    async def get_dashboard(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> IntelligenceDashboard:
        """Get the intelligence dashboard.

        Args:
            user_id: ID of the user
            db: Database session

        Returns:
            IntelligenceDashboard with all intelligence
        """
        try:
            # Gather market data
            market_data = await self._gather_market_data(db)

            # Detect competitor activities
            activities = await self._detect_activities(market_data, db)

            # Generate alerts
            alerts = await self._generate_alerts(activities, user_id, db)

            # Generate market insights
            insights = await self._generate_insights(market_data, db)

            # Generate summary
            summary = await self._generate_summary(activities, alerts, insights)

            return IntelligenceDashboard(
                competitors=list(self._competitors.values()),
                recent_activities=activities[:20],
                alerts=alerts[:10],
                market_insights=insights[:5],
                summary=summary,
            )

        except Exception as e:
            logger.error(f"Dashboard generation failed: {e}")
            return IntelligenceDashboard(
                competitors=[],
                recent_activities=[],
                alerts=[],
                market_insights=[],
                summary="Unable to generate intelligence dashboard.",
            )

    async def _gather_market_data(
        self,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Gather market data for analysis."""
        # Get recent transactions
        cutoff = datetime.now() - timedelta(days=90)
        txn_query = (
            select(MarketTransaction)
            .where(MarketTransaction.transaction_date >= cutoff.date())
            .order_by(MarketTransaction.transaction_date.desc())
            .limit(100)
        )
        result = await db.execute(txn_query)
        transactions = result.scalars().all()

        # Get development pipeline
        pipeline_query = select(DevelopmentPipeline).where(
            DevelopmentPipeline.estimated_completion >= datetime.now().date()
        )
        pipeline_result = await db.execute(pipeline_query)
        pipeline = pipeline_result.scalars().all()

        return {
            "transactions": transactions,
            "pipeline": pipeline,
            "transaction_count": len(transactions),
            "pipeline_count": len(pipeline),
        }

    async def _detect_activities(
        self,
        market_data: dict[str, Any],
        db: AsyncSession,
    ) -> list[CompetitorActivity]:
        """Detect competitor activities from market data."""
        activities = []
        transactions = market_data.get("transactions", [])

        for txn in transactions[:50]:
            # Check if buyer/seller matches known competitors
            for comp in self._competitors.values():
                # Simplified matching - production would use NLP
                if comp.name.lower() in (txn.buyer or "").lower():
                    activities.append(
                        CompetitorActivity(
                            id=str(uuid4()),
                            competitor_id=comp.id,
                            competitor_name=comp.name,
                            category=IntelligenceCategory.TRANSACTION,
                            title=f"{comp.name} Acquisition",
                            description=f"Acquired property at {txn.property_id or 'undisclosed location'}",
                            location=str(txn.property_id) if txn.property_id else None,
                            value=float(txn.price) if txn.price else None,
                            relevance_score=0.8,
                        )
                    )
                elif comp.name.lower() in (txn.seller or "").lower():
                    activities.append(
                        CompetitorActivity(
                            id=str(uuid4()),
                            competitor_id=comp.id,
                            competitor_name=comp.name,
                            category=IntelligenceCategory.DIVESTMENT,
                            title=f"{comp.name} Divestment",
                            description=f"Sold property at {txn.property_id or 'undisclosed location'}",
                            location=str(txn.property_id) if txn.property_id else None,
                            value=float(txn.price) if txn.price else None,
                            relevance_score=0.7,
                        )
                    )

        # Add simulated activities for demo
        if not activities:
            activities = self._get_sample_activities()

        self._activities = activities
        return activities

    def _get_sample_activities(self) -> list[CompetitorActivity]:
        """Get sample activities for demonstration."""
        return [
            CompetitorActivity(
                id=str(uuid4()),
                competitor_id="comp_1",
                competitor_name="CapitaLand",
                category=IntelligenceCategory.DEVELOPMENT,
                title="New Mixed-Use Development at Jurong",
                description="CapitaLand announced new mixed-use development at Jurong Gateway",
                location="Jurong East",
                value=500_000_000,
                relevance_score=0.9,
            ),
            CompetitorActivity(
                id=str(uuid4()),
                competitor_id="comp_2",
                competitor_name="Mapletree",
                category=IntelligenceCategory.TRANSACTION,
                title="Industrial Acquisition at Tuas",
                description="Mapletree acquired industrial complex in Tuas South",
                location="Tuas",
                value=200_000_000,
                relevance_score=0.85,
            ),
            CompetitorActivity(
                id=str(uuid4()),
                competitor_id="comp_4",
                competitor_name="Keppel",
                category=IntelligenceCategory.PARTNERSHIP,
                title="JV with GIC for Data Centre",
                description="Keppel forms JV with GIC for data centre development",
                location="Changi",
                value=800_000_000,
                relevance_score=0.95,
            ),
        ]

    async def _generate_alerts(
        self,
        activities: list[CompetitorActivity],
        user_id: str,
        db: AsyncSession,
    ) -> list[CompetitiveAlert]:
        """Generate alerts from activities."""
        alerts = []

        # Get user's focus areas from their deals
        deal_query = select(AgentDeal).where(AgentDeal.agent_id == user_id)
        result = await db.execute(deal_query)
        user_deals = result.scalars().all()

        user_sectors = set(d.asset_type.value for d in user_deals)
        # user_districts would be extracted from properties in production

        for activity in activities:
            comp = self._competitors.get(activity.competitor_id)
            if not comp:
                continue

            # Check for sector overlap
            sector_overlap = bool(set(comp.focus_sectors) & user_sectors)

            if activity.relevance_score > 0.8 or sector_overlap:
                priority = (
                    AlertPriority.HIGH
                    if activity.relevance_score > 0.9
                    else AlertPriority.MEDIUM
                )

                alerts.append(
                    CompetitiveAlert(
                        id=str(uuid4()),
                        priority=priority,
                        title=activity.title,
                        description=activity.description,
                        competitor_id=activity.competitor_id,
                        competitor_name=activity.competitor_name,
                        activity_id=activity.id,
                        action_required=self._suggest_action(activity, comp),
                        expires_at=datetime.now() + timedelta(days=7),
                    )
                )

        # Sort by priority
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3,
        }
        alerts.sort(key=lambda a: priority_order.get(a.priority, 2))

        self._alerts = alerts
        return alerts

    def _suggest_action(
        self,
        activity: CompetitorActivity,
        competitor: Competitor,
    ) -> str:
        """Suggest action based on activity."""
        if activity.category == IntelligenceCategory.TRANSACTION:
            return (
                f"Review comparable opportunities in {activity.location or 'the area'}"
            )
        elif activity.category == IntelligenceCategory.DEVELOPMENT:
            return "Assess impact on local market dynamics"
        elif activity.category == IntelligenceCategory.DIVESTMENT:
            return "Evaluate acquisition opportunity"
        elif activity.category == IntelligenceCategory.PARTNERSHIP:
            return "Consider strategic response or partnership opportunities"
        return "Monitor for further developments"

    async def _generate_insights(
        self,
        market_data: dict[str, Any],
        db: AsyncSession,
    ) -> list[MarketIntelligence]:
        """Generate market insights from data."""
        insights = []

        transactions = market_data.get("transactions", [])
        pipeline = market_data.get("pipeline", [])

        # Transaction volume insight
        if transactions:
            total_value = sum(float(t.price or 0) for t in transactions)
            insights.append(
                MarketIntelligence(
                    id=str(uuid4()),
                    category="transaction_volume",
                    title="Recent Transaction Activity",
                    insight=f"{len(transactions)} transactions totaling ${total_value:,.0f} in the past 90 days",
                    data_points=[
                        {"metric": "count", "value": len(transactions)},
                        {"metric": "total_value", "value": total_value},
                    ],
                    impact="Market activity indicates steady investor appetite",
                    recommendation="Continue active deal sourcing in high-activity sectors",
                )
            )

        # Pipeline insight
        if pipeline:
            total_gfa = sum(float(p.estimated_gfa_sqm or 0) for p in pipeline)
            insights.append(
                MarketIntelligence(
                    id=str(uuid4()),
                    category="supply_pipeline",
                    title="Development Pipeline",
                    insight=f"{len(pipeline)} projects with {total_gfa:,.0f} sqm GFA in pipeline",
                    data_points=[
                        {"metric": "project_count", "value": len(pipeline)},
                        {"metric": "total_gfa", "value": total_gfa},
                    ],
                    impact="New supply may impact rental rates in affected sectors",
                    recommendation="Factor pipeline into acquisition underwriting",
                )
            )

        # Competitor activity insight
        if self._activities:
            active_competitors = len(set(a.competitor_id for a in self._activities))
            insights.append(
                MarketIntelligence(
                    id=str(uuid4()),
                    category="competitor_activity",
                    title="Competitor Landscape",
                    insight=f"{active_competitors} major players active with {len(self._activities)} recent activities",
                    data_points=[
                        {"metric": "active_competitors", "value": active_competitors},
                        {"metric": "activity_count", "value": len(self._activities)},
                    ],
                    impact="Competitive environment remains active",
                    recommendation="Maintain competitive positioning and speed on good opportunities",
                )
            )

        return insights

    async def _generate_summary(
        self,
        activities: list[CompetitorActivity],
        alerts: list[CompetitiveAlert],
        insights: list[MarketIntelligence],
    ) -> str:
        """Generate intelligence summary."""
        if not self._initialized or not self.llm:
            return self._generate_basic_summary(activities, alerts, insights)

        activities_text = "\n".join(
            f"- {a.competitor_name}: {a.title}" for a in activities[:5]
        )

        alerts_text = "\n".join(f"- [{a.priority.value}] {a.title}" for a in alerts[:3])

        prompt = f"""Generate a 3-4 sentence executive summary of the competitive intelligence:

Recent Competitor Activities:
{activities_text or "No recent activities detected"}

Active Alerts:
{alerts_text or "No active alerts"}

Number of Insights: {len(insights)}

Provide actionable intelligence summary for a real estate investment professional."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content
            if isinstance(content, str):
                return content
            return self._generate_basic_summary(activities, alerts, insights)
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return self._generate_basic_summary(activities, alerts, insights)

    def _generate_basic_summary(
        self,
        activities: list[CompetitorActivity],
        alerts: list[CompetitiveAlert],
        insights: list[MarketIntelligence],
    ) -> str:
        """Generate basic summary without LLM."""
        high_priority_count = sum(
            1
            for a in alerts
            if a.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]
        )

        return f"""Competitive Intelligence Summary:

{len(activities)} competitor activities detected across {len(self._competitors)} tracked competitors.
{high_priority_count} high-priority alerts require attention.
{len(insights)} market insights generated from recent data.

Monitor competitor movements and adjust strategy accordingly."""

    def track_competitor(self, competitor: Competitor) -> None:
        """Add a competitor to track.

        Args:
            competitor: Competitor to track
        """
        self._competitors[competitor.id] = competitor

    def get_competitor(self, competitor_id: str) -> Competitor | None:
        """Get a tracked competitor.

        Args:
            competitor_id: ID of the competitor

        Returns:
            Competitor or None
        """
        return self._competitors.get(competitor_id)

    def list_competitors(self) -> list[Competitor]:
        """List all tracked competitors.

        Returns:
            List of competitors
        """
        return list(self._competitors.values())


# Singleton instance
competitive_intelligence_service = CompetitiveIntelligenceService()
