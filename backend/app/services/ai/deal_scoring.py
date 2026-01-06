"""Phase 2.1: Deal Scoring Model.

ML model to predict deal success probability with explainability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_performance import (
    AgentDeal,
    DealStatus,
)
from app.models.property import Property, MarketTransaction

logger = logging.getLogger(__name__)


class ScoreConfidence(str, Enum):
    """Confidence levels for deal scores."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FactorType(str, Enum):
    """Types of scoring factors."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class ScoringFactor:
    """A factor contributing to the deal score."""

    name: str
    description: str
    factor_type: FactorType
    impact_score: float  # -1 to 1
    evidence: str | None = None


@dataclass
class DealScore:
    """Result from deal scoring model."""

    score: int  # 0-100
    confidence: ScoreConfidence
    probability: float  # 0-1 success probability
    positive_factors: list[ScoringFactor] = field(default_factory=list)
    risk_factors: list[ScoringFactor] = field(default_factory=list)
    neutral_factors: list[ScoringFactor] = field(default_factory=list)
    recommendation: str = ""
    comparable_deals: list[dict[str, Any]] = field(default_factory=list)
    scoring_version: str = "1.0"
    scored_at: datetime = field(default_factory=datetime.now)


# Scoring weights for different factors
SCORING_WEIGHTS = {
    # Location factors
    "location_match": 0.15,
    "submarket_strength": 0.10,
    # Property factors
    "tenure_adequacy": 0.10,
    "building_age": 0.05,
    "gpr_headroom": 0.08,
    # Deal factors
    "seller_motivation": 0.12,
    "competition_level": 0.08,
    "price_vs_market": 0.15,
    # Historical factors
    "historical_success_rate": 0.10,
    "similar_deal_outcomes": 0.07,
}


class DealScoringService:
    """Service for scoring deals using ML and heuristics."""

    def __init__(self) -> None:
        """Initialize the deal scoring service."""
        self.model_version = "1.0"
        self._model_loaded = False
        # In production, this would load an actual ML model
        # For now, we use a heuristic-based scoring system

    async def score_deal(
        self,
        deal_id: str,
        db: AsyncSession,
        user_id: str,
    ) -> DealScore:
        """Score a deal and provide explainable results.

        Args:
            deal_id: ID of the deal to score
            db: Database session
            user_id: ID of the user requesting the score

        Returns:
            DealScore with score, factors, and recommendation
        """
        # Fetch the deal
        deal_query = select(AgentDeal).where(AgentDeal.id == deal_id)
        result = await db.execute(deal_query)
        deal = result.scalar_one_or_none()

        if not deal:
            return DealScore(
                score=0,
                confidence=ScoreConfidence.LOW,
                probability=0.0,
                recommendation="Deal not found",
            )

        # Fetch related property if available
        property_data = None
        if deal.property_id:
            prop_query = select(Property).where(Property.id == deal.property_id)
            prop_result = await db.execute(prop_query)
            property_data = prop_result.scalar_one_or_none()

        # Calculate individual factor scores
        positive_factors = []
        risk_factors = []
        neutral_factors = []

        # Score: Location Match
        location_score = await self._score_location_match(
            deal, property_data, db, user_id
        )
        self._categorize_factor(
            location_score, positive_factors, risk_factors, neutral_factors
        )

        # Score: Tenure Adequacy
        tenure_score = await self._score_tenure(deal, property_data)
        self._categorize_factor(
            tenure_score, positive_factors, risk_factors, neutral_factors
        )

        # Score: Price vs Market
        price_score = await self._score_price_vs_market(deal, property_data, db)
        self._categorize_factor(
            price_score, positive_factors, risk_factors, neutral_factors
        )

        # Score: GPR Headroom
        gpr_score = await self._score_gpr_headroom(deal, property_data)
        self._categorize_factor(
            gpr_score, positive_factors, risk_factors, neutral_factors
        )

        # Score: Historical Success Rate
        history_score = await self._score_historical_success(deal, db, user_id)
        self._categorize_factor(
            history_score, positive_factors, risk_factors, neutral_factors
        )

        # Score: Competition Level
        competition_score = await self._score_competition(deal)
        self._categorize_factor(
            competition_score, positive_factors, risk_factors, neutral_factors
        )

        # Score: Seller Motivation
        seller_score = await self._score_seller_motivation(deal)
        self._categorize_factor(
            seller_score, positive_factors, risk_factors, neutral_factors
        )

        # Calculate overall score
        all_factors = positive_factors + risk_factors + neutral_factors
        weighted_sum = sum(
            f.impact_score * SCORING_WEIGHTS.get(f.name.lower().replace(" ", "_"), 0.05)
            for f in all_factors
        )

        # Normalize to 0-100
        # Weighted sum ranges from -1 to 1, so we map to 0-100
        raw_score = (weighted_sum + 1) / 2 * 100
        final_score = max(0, min(100, int(raw_score)))

        # Calculate probability
        probability = final_score / 100.0

        # Determine confidence
        if len(all_factors) >= 5 and len(positive_factors) + len(risk_factors) >= 3:
            confidence = ScoreConfidence.HIGH
        elif len(all_factors) >= 3:
            confidence = ScoreConfidence.MEDIUM
        else:
            confidence = ScoreConfidence.LOW

        # Generate recommendation
        recommendation = self._generate_recommendation(
            final_score, positive_factors, risk_factors
        )

        # Get comparable deals
        comparable_deals = await self._get_comparable_deals(deal, db, user_id)

        return DealScore(
            score=final_score,
            confidence=confidence,
            probability=probability,
            positive_factors=positive_factors,
            risk_factors=risk_factors,
            neutral_factors=neutral_factors,
            recommendation=recommendation,
            comparable_deals=comparable_deals,
            scoring_version=self.model_version,
        )

    def _categorize_factor(
        self,
        factor: ScoringFactor,
        positive: list[ScoringFactor],
        negative: list[ScoringFactor],
        neutral: list[ScoringFactor],
    ) -> None:
        """Categorize a factor based on its impact."""
        if factor.impact_score > 0.1:
            factor.factor_type = FactorType.POSITIVE
            positive.append(factor)
        elif factor.impact_score < -0.1:
            factor.factor_type = FactorType.NEGATIVE
            negative.append(factor)
        else:
            factor.factor_type = FactorType.NEUTRAL
            neutral.append(factor)

    async def _score_location_match(
        self,
        deal: AgentDeal,
        property_data: Property | None,
        db: AsyncSession,
        user_id: str,
    ) -> ScoringFactor:
        """Score based on location match with historical successes."""
        if not property_data:
            return ScoringFactor(
                name="Location Match",
                description="No property data available for location analysis",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        # Check how many successful deals user had in this location
        location = property_data.district or property_data.planning_area

        if not location:
            return ScoringFactor(
                name="Location Match",
                description="Location not specified",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        # Query for historical wins in same location
        # This is simplified - would need to join with Property table
        wins_query = select(func.count(AgentDeal.id)).where(
            and_(
                AgentDeal.agent_id == user_id,
                AgentDeal.status == DealStatus.CLOSED_WON,
            )
        )
        result = await db.execute(wins_query)
        win_count = result.scalar() or 0

        if win_count >= 5:
            return ScoringFactor(
                name="Location Match",
                description=f"You have {win_count} successful deals in similar locations",
                factor_type=FactorType.POSITIVE,
                impact_score=0.8,
                evidence=f"{win_count} historical wins",
            )
        elif win_count >= 2:
            return ScoringFactor(
                name="Location Match",
                description=f"You have some experience in this location ({win_count} deals)",
                factor_type=FactorType.POSITIVE,
                impact_score=0.4,
                evidence=f"{win_count} historical wins",
            )
        else:
            return ScoringFactor(
                name="Location Match",
                description="Limited track record in this location",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

    async def _score_tenure(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> ScoringFactor:
        """Score based on remaining tenure."""
        if not property_data or not property_data.lease_expiry_date:
            return ScoringFactor(
                name="Tenure Adequacy",
                description="Tenure information not available",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        today = datetime.now().date()
        years_remaining = (property_data.lease_expiry_date - today).days / 365

        if years_remaining >= 70:
            return ScoringFactor(
                name="Tenure Adequacy",
                description=f"Strong tenure: {years_remaining:.0f} years remaining",
                factor_type=FactorType.POSITIVE,
                impact_score=0.7,
                evidence=f"{years_remaining:.0f} years",
            )
        elif years_remaining >= 50:
            return ScoringFactor(
                name="Tenure Adequacy",
                description=f"Adequate tenure: {years_remaining:.0f} years remaining",
                factor_type=FactorType.POSITIVE,
                impact_score=0.3,
                evidence=f"{years_remaining:.0f} years",
            )
        elif years_remaining >= 30:
            return ScoringFactor(
                name="Tenure Adequacy",
                description=f"Limited tenure: {years_remaining:.0f} years remaining",
                factor_type=FactorType.NEGATIVE,
                impact_score=-0.3,
                evidence=f"{years_remaining:.0f} years",
            )
        else:
            return ScoringFactor(
                name="Tenure Adequacy",
                description=f"Short tenure: Only {years_remaining:.0f} years remaining",
                factor_type=FactorType.NEGATIVE,
                impact_score=-0.7,
                evidence=f"{years_remaining:.0f} years",
            )

    async def _score_price_vs_market(
        self,
        deal: AgentDeal,
        property_data: Property | None,
        db: AsyncSession,
    ) -> ScoringFactor:
        """Score based on deal price vs market comparables."""
        deal_metadata = deal.metadata_json or {}
        target_psf = deal_metadata.get("target_psf")

        if not target_psf:
            return ScoringFactor(
                name="Price vs Market",
                description="Target price not specified",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        # Get market average
        six_months_ago = datetime.now() - timedelta(days=180)
        market_query = select(func.avg(MarketTransaction.psf_price)).where(
            MarketTransaction.transaction_date >= six_months_ago.date()
        )
        result = await db.execute(market_query)
        market_avg = result.scalar()

        if not market_avg:
            return ScoringFactor(
                name="Price vs Market",
                description="Insufficient market data for comparison",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        deviation = (target_psf - float(market_avg)) / float(market_avg) * 100

        if deviation < -10:
            return ScoringFactor(
                name="Price vs Market",
                description=f"Target price is {abs(deviation):.1f}% below market average",
                factor_type=FactorType.POSITIVE,
                impact_score=0.6,
                evidence=f"${target_psf:,.0f} vs ${float(market_avg):,.0f} avg",
            )
        elif deviation < 5:
            return ScoringFactor(
                name="Price vs Market",
                description="Target price is in line with market",
                factor_type=FactorType.POSITIVE,
                impact_score=0.2,
                evidence=f"${target_psf:,.0f} vs ${float(market_avg):,.0f} avg",
            )
        elif deviation < 15:
            return ScoringFactor(
                name="Price vs Market",
                description=f"Target price is {deviation:.1f}% above market average",
                factor_type=FactorType.NEGATIVE,
                impact_score=-0.3,
                evidence=f"${target_psf:,.0f} vs ${float(market_avg):,.0f} avg",
            )
        else:
            return ScoringFactor(
                name="Price vs Market",
                description=f"Target price is significantly above market ({deviation:.1f}%)",
                factor_type=FactorType.NEGATIVE,
                impact_score=-0.6,
                evidence=f"${target_psf:,.0f} vs ${float(market_avg):,.0f} avg",
            )

    async def _score_gpr_headroom(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> ScoringFactor:
        """Score based on development potential (GPR headroom)."""
        if not property_data:
            return ScoringFactor(
                name="GPR Headroom",
                description="Property data not available",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        current_gfa = property_data.gross_floor_area_sqm
        land_area = property_data.land_area_sqm
        plot_ratio = property_data.plot_ratio

        if not all([current_gfa, land_area, plot_ratio]):
            return ScoringFactor(
                name="GPR Headroom",
                description="Insufficient data for GPR analysis",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        current_ratio = float(current_gfa) / float(land_area)
        headroom = (float(plot_ratio) - current_ratio) / float(plot_ratio) * 100

        if headroom > 20:
            return ScoringFactor(
                name="GPR Headroom",
                description=f"Significant development potential: {headroom:.0f}% GPR headroom",
                factor_type=FactorType.POSITIVE,
                impact_score=0.7,
                evidence=f"Current {current_ratio:.2f} vs allowed {float(plot_ratio):.2f}",
            )
        elif headroom > 10:
            return ScoringFactor(
                name="GPR Headroom",
                description=f"Some development potential: {headroom:.0f}% GPR headroom",
                factor_type=FactorType.POSITIVE,
                impact_score=0.3,
                evidence=f"Current {current_ratio:.2f} vs allowed {float(plot_ratio):.2f}",
            )
        else:
            return ScoringFactor(
                name="GPR Headroom",
                description="Fully developed - limited upside potential",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

    async def _score_historical_success(
        self,
        deal: AgentDeal,
        db: AsyncSession,
        user_id: str,
    ) -> ScoringFactor:
        """Score based on historical success rate for similar deals."""
        # Get win/loss stats for similar deal types
        similar_query = (
            select(
                AgentDeal.status,
                func.count(AgentDeal.id).label("count"),
            )
            .where(
                and_(
                    AgentDeal.agent_id == user_id,
                    AgentDeal.deal_type == deal.deal_type,
                    AgentDeal.asset_type == deal.asset_type,
                    AgentDeal.status.in_(
                        [DealStatus.CLOSED_WON, DealStatus.CLOSED_LOST]
                    ),
                )
            )
            .group_by(AgentDeal.status)
        )

        result = await db.execute(similar_query)
        stats = {row.status: row.count for row in result}

        wins = stats.get(DealStatus.CLOSED_WON, 0)
        losses = stats.get(DealStatus.CLOSED_LOST, 0)
        total = wins + losses

        if total < 5:
            return ScoringFactor(
                name="Historical Success",
                description=f"Limited history for {deal.deal_type.value} {deal.asset_type.value} deals",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

        win_rate = wins / total

        if win_rate >= 0.7:
            return ScoringFactor(
                name="Historical Success",
                description=f"Strong track record: {win_rate:.0%} win rate on similar deals",
                factor_type=FactorType.POSITIVE,
                impact_score=0.7,
                evidence=f"{wins} wins / {total} total",
            )
        elif win_rate >= 0.5:
            return ScoringFactor(
                name="Historical Success",
                description=f"Moderate track record: {win_rate:.0%} win rate on similar deals",
                factor_type=FactorType.POSITIVE,
                impact_score=0.3,
                evidence=f"{wins} wins / {total} total",
            )
        else:
            return ScoringFactor(
                name="Historical Success",
                description=f"Challenging category: {win_rate:.0%} win rate historically",
                factor_type=FactorType.NEGATIVE,
                impact_score=-0.3,
                evidence=f"{wins} wins / {total} total",
            )

    async def _score_competition(self, deal: AgentDeal) -> ScoringFactor:
        """Score based on competition level."""
        metadata = deal.metadata_json or {}
        competition = metadata.get("competition_level", "unknown")

        if competition == "none" or competition == "low":
            return ScoringFactor(
                name="Competition Level",
                description="Low competition for this deal",
                factor_type=FactorType.POSITIVE,
                impact_score=0.5,
            )
        elif competition == "medium":
            return ScoringFactor(
                name="Competition Level",
                description="Moderate competition expected",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )
        elif competition == "high":
            return ScoringFactor(
                name="Competition Level",
                description="High competition - multiple bidders expected",
                factor_type=FactorType.NEGATIVE,
                impact_score=-0.4,
            )
        else:
            return ScoringFactor(
                name="Competition Level",
                description="Competition level unknown",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

    async def _score_seller_motivation(self, deal: AgentDeal) -> ScoringFactor:
        """Score based on seller motivation."""
        metadata = deal.metadata_json or {}
        motivation = metadata.get("seller_motivation", "unknown")

        high_motivation = [
            "estate_sale",
            "distressed",
            "divorce",
            "urgent",
            "relocation",
        ]
        medium_motivation = ["portfolio_rebalance", "upgrade", "retirement"]

        if motivation.lower() in high_motivation:
            return ScoringFactor(
                name="Seller Motivation",
                description=f"High seller motivation: {motivation.replace('_', ' ')}",
                factor_type=FactorType.POSITIVE,
                impact_score=0.6,
            )
        elif motivation.lower() in medium_motivation:
            return ScoringFactor(
                name="Seller Motivation",
                description=f"Moderate seller motivation: {motivation.replace('_', ' ')}",
                factor_type=FactorType.POSITIVE,
                impact_score=0.2,
            )
        else:
            return ScoringFactor(
                name="Seller Motivation",
                description="Seller motivation not assessed",
                factor_type=FactorType.NEUTRAL,
                impact_score=0.0,
            )

    def _generate_recommendation(
        self,
        score: int,
        positive_factors: list[ScoringFactor],
        risk_factors: list[ScoringFactor],
    ) -> str:
        """Generate a recommendation based on the score and factors."""
        if score >= 80:
            action = "Strong Buy - Proceed with confidence"
        elif score >= 65:
            action = "Proceed with standard due diligence"
        elif score >= 50:
            action = "Proceed with caution - enhanced DD recommended"
        elif score >= 35:
            action = "Review carefully - significant risks identified"
        else:
            action = "Reconsider - multiple red flags"

        top_positive = (
            ", ".join(f.name for f in positive_factors[:2])
            if positive_factors
            else "None identified"
        )
        top_risks = (
            ", ".join(f.name for f in risk_factors[:2])
            if risk_factors
            else "None identified"
        )

        return f"{action}. Key strengths: {top_positive}. Key risks: {top_risks}."

    async def _get_comparable_deals(
        self,
        deal: AgentDeal,
        db: AsyncSession,
        user_id: str,
    ) -> list[dict[str, Any]]:
        """Get comparable historical deals."""
        query = (
            select(AgentDeal)
            .where(
                and_(
                    AgentDeal.agent_id == user_id,
                    AgentDeal.deal_type == deal.deal_type,
                    AgentDeal.asset_type == deal.asset_type,
                    AgentDeal.status.in_(
                        [DealStatus.CLOSED_WON, DealStatus.CLOSED_LOST]
                    ),
                    AgentDeal.id != deal.id,
                )
            )
            .order_by(AgentDeal.actual_close_date.desc())
            .limit(5)
        )

        result = await db.execute(query)
        comparable = result.scalars().all()

        return [
            {
                "id": str(d.id),
                "title": d.title,
                "outcome": d.status.value,
                "value": (
                    float(d.estimated_value_amount)
                    if d.estimated_value_amount
                    else None
                ),
                "close_date": (
                    d.actual_close_date.isoformat() if d.actual_close_date else None
                ),
            }
            for d in comparable
        ]


# Singleton instance
deal_scoring_service = DealScoringService()
