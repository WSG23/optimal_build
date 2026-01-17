"""Phase 4.3: Portfolio Optimization Engine.

AI-powered portfolio allocation and rebalancing recommendations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_performance import AgentDeal, DealAssetType, DealStatus
from app.models.property import Property

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Portfolio optimization strategies."""

    MAXIMIZE_RETURNS = "maximize_returns"
    MINIMIZE_RISK = "minimize_risk"
    BALANCED = "balanced"
    INCOME_FOCUSED = "income_focused"
    GROWTH_FOCUSED = "growth_focused"


class RiskProfile(str, Enum):
    """Investor risk profiles."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class AssetAllocation:
    """Current or recommended asset allocation."""

    asset_type: str
    current_value: float
    current_percentage: float
    recommended_percentage: float
    variance: float
    action: str  # "hold", "increase", "decrease"


@dataclass
class PortfolioMetrics:
    """Key portfolio metrics."""

    total_value: float
    total_assets: int
    weighted_yield: float
    portfolio_beta: float
    diversification_score: int  # 1-100
    concentration_risk: str  # "low", "medium", "high"
    liquidity_score: int  # 1-100


@dataclass
class RebalancingRecommendation:
    """A specific rebalancing recommendation."""

    asset_id: str
    asset_name: str
    asset_type: str
    current_allocation: float
    recommended_action: str  # "sell", "hold", "buy more"
    target_allocation: float
    rationale: str
    priority: str  # "high", "medium", "low"
    estimated_impact: dict[str, float]


@dataclass
class PortfolioOptimizationResult:
    """Result from portfolio optimization."""

    id: str
    user_id: str
    strategy: OptimizationStrategy
    risk_profile: RiskProfile
    metrics: PortfolioMetrics
    current_allocation: list[AssetAllocation]
    recommendations: list[RebalancingRecommendation]
    target_allocation: dict[str, float]
    expected_improvement: dict[str, float]
    analysis_summary: str
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationRequest:
    """Request for portfolio optimization."""

    user_id: str
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    risk_profile: RiskProfile = RiskProfile.MODERATE
    constraints: dict[str, Any] = field(default_factory=dict)
    target_return: float | None = None
    max_concentration: float = 0.30  # Max 30% in single asset type
    min_liquidity: float = 0.10  # Min 10% liquid assets


class PortfolioOptimizerService:
    """Service for AI-powered portfolio optimization."""

    def __init__(self) -> None:
        """Initialize the optimizer."""
        self.llm: Optional[ChatOpenAI] = None
        try:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0.2,
            )
            self._initialized = True
        except Exception as e:
            logger.warning(f"Portfolio Optimizer not initialized: {e}")
            self._initialized = False

    async def optimize(
        self,
        request: OptimizationRequest,
        db: AsyncSession,
    ) -> PortfolioOptimizationResult:
        """Optimize portfolio allocation.

        Args:
            request: Optimization request
            db: Database session

        Returns:
            PortfolioOptimizationResult with recommendations
        """
        try:
            # Gather portfolio data
            portfolio_data = await self._gather_portfolio_data(request.user_id, db)

            # Calculate current metrics
            metrics = self._calculate_metrics(portfolio_data)

            # Analyze current allocation
            current_allocation = self._analyze_allocation(portfolio_data)

            # Generate target allocation based on strategy
            target_allocation = self._generate_target_allocation(
                request.strategy,
                request.risk_profile,
                request.constraints,
            )

            # Generate rebalancing recommendations
            recommendations = await self._generate_recommendations(
                current_allocation,
                target_allocation,
                portfolio_data,
                request,
            )

            # Calculate expected improvements
            expected_improvement = self._calculate_improvement(
                metrics,
                recommendations,
            )

            # Generate analysis summary
            summary = await self._generate_summary(
                metrics,
                current_allocation,
                recommendations,
                request,
            )

            return PortfolioOptimizationResult(
                id=str(uuid4()),
                user_id=request.user_id,
                strategy=request.strategy,
                risk_profile=request.risk_profile,
                metrics=metrics,
                current_allocation=current_allocation,
                recommendations=recommendations,
                target_allocation=target_allocation,
                expected_improvement=expected_improvement,
                analysis_summary=summary,
            )

        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            return self._empty_result(request)

    async def _gather_portfolio_data(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Gather all portfolio data for a user."""
        # Get all deals for the user
        deals_query = select(AgentDeal).where(
            AgentDeal.agent_id == user_id,
            AgentDeal.status.in_([DealStatus.OPEN, DealStatus.CLOSED_WON]),
        )
        result = await db.execute(deals_query)
        deals = result.scalars().all()

        # Get associated properties
        property_ids = [d.property_id for d in deals if d.property_id]
        properties = []
        if property_ids:
            prop_query = select(Property).where(Property.id.in_(property_ids))
            prop_result = await db.execute(prop_query)
            properties = prop_result.scalars().all()

        # Financial projects would be loaded in production
        # project_ids = [d.project_id for d in deals if hasattr(d, "project_id") and d.project_id]

        return {
            "deals": deals,
            "properties": properties,
            "projects": [],  # Placeholder for financial project integration
            "total_value": sum(float(d.estimated_value_amount or 0) for d in deals),
        }

    def _calculate_metrics(self, portfolio_data: dict[str, Any]) -> PortfolioMetrics:
        """Calculate portfolio metrics."""
        deals = portfolio_data.get("deals", [])
        total_value = portfolio_data.get("total_value", 0)

        # Count by asset type for diversification
        by_type = {}
        for deal in deals:
            asset_type = deal.asset_type.value
            by_type[asset_type] = by_type.get(asset_type, 0) + float(
                deal.estimated_value_amount or 0
            )

        # Calculate diversification score (more types = higher score)
        num_types = len(by_type)
        diversification_score = min(100, num_types * 20)

        # Calculate concentration risk
        max_concentration = (
            max(by_type.values()) / total_value if total_value > 0 and by_type else 0
        )
        if max_concentration > 0.5:
            concentration_risk = "high"
        elif max_concentration > 0.3:
            concentration_risk = "medium"
        else:
            concentration_risk = "low"

        # Estimate weighted yield (simplified)
        weighted_yield = 0.045  # Placeholder - would calculate from actual yields

        return PortfolioMetrics(
            total_value=total_value,
            total_assets=len(deals),
            weighted_yield=weighted_yield,
            portfolio_beta=1.0,  # Placeholder
            diversification_score=diversification_score,
            concentration_risk=concentration_risk,
            liquidity_score=60,  # Placeholder - real estate is generally illiquid
        )

    def _analyze_allocation(
        self,
        portfolio_data: dict[str, Any],
    ) -> list[AssetAllocation]:
        """Analyze current asset allocation."""
        deals = portfolio_data.get("deals", [])
        total_value = portfolio_data.get("total_value", 0)

        if not deals or total_value == 0:
            return []

        # Group by asset type
        by_type = {}
        for deal in deals:
            asset_type = deal.asset_type.value
            if asset_type not in by_type:
                by_type[asset_type] = 0
            by_type[asset_type] += float(deal.estimated_value_amount or 0)

        # Create allocation list
        allocations = []
        target_allocations = self._get_balanced_targets()

        for asset_type, value in by_type.items():
            current_pct = (value / total_value * 100) if total_value > 0 else 0
            recommended_pct = target_allocations.get(asset_type, 15.0)
            variance = current_pct - recommended_pct

            if variance > 5:
                action = "decrease"
            elif variance < -5:
                action = "increase"
            else:
                action = "hold"

            allocations.append(
                AssetAllocation(
                    asset_type=asset_type,
                    current_value=value,
                    current_percentage=current_pct,
                    recommended_percentage=recommended_pct,
                    variance=variance,
                    action=action,
                )
            )

        return allocations

    def _get_balanced_targets(self) -> dict[str, float]:
        """Get balanced allocation targets."""
        return {
            DealAssetType.OFFICE.value: 20.0,
            DealAssetType.INDUSTRIAL.value: 25.0,
            DealAssetType.RETAIL.value: 15.0,
            DealAssetType.RESIDENTIAL.value: 20.0,
            DealAssetType.MIXED_USE.value: 10.0,
            DealAssetType.LAND.value: 10.0,
        }

    def _generate_target_allocation(
        self,
        strategy: OptimizationStrategy,
        risk_profile: RiskProfile,
        constraints: dict[str, Any],
    ) -> dict[str, float]:
        """Generate target allocation based on strategy."""
        base_allocations = {
            OptimizationStrategy.MAXIMIZE_RETURNS: {
                "office": 15.0,
                "industrial": 35.0,
                "retail": 10.0,
                "residential": 15.0,
                "mixed_use": 15.0,
                "land": 10.0,
            },
            OptimizationStrategy.MINIMIZE_RISK: {
                "office": 25.0,
                "industrial": 20.0,
                "retail": 10.0,
                "residential": 30.0,
                "mixed_use": 10.0,
                "land": 5.0,
            },
            OptimizationStrategy.BALANCED: {
                "office": 20.0,
                "industrial": 25.0,
                "retail": 15.0,
                "residential": 20.0,
                "mixed_use": 10.0,
                "land": 10.0,
            },
            OptimizationStrategy.INCOME_FOCUSED: {
                "office": 30.0,
                "industrial": 25.0,
                "retail": 20.0,
                "residential": 15.0,
                "mixed_use": 5.0,
                "land": 5.0,
            },
            OptimizationStrategy.GROWTH_FOCUSED: {
                "office": 10.0,
                "industrial": 30.0,
                "retail": 10.0,
                "residential": 20.0,
                "mixed_use": 15.0,
                "land": 15.0,
            },
        }

        return base_allocations.get(strategy, base_allocations[OptimizationStrategy.BALANCED])

    async def _generate_recommendations(
        self,
        current_allocation: list[AssetAllocation],
        target_allocation: dict[str, float],
        portfolio_data: dict[str, Any],
        request: OptimizationRequest,
    ) -> list[RebalancingRecommendation]:
        """Generate specific rebalancing recommendations."""
        recommendations = []
        deals = portfolio_data.get("deals", [])

        for allocation in current_allocation:
            if allocation.action == "hold":
                continue

            # Find deals of this asset type
            type_deals = [d for d in deals if d.asset_type.value == allocation.asset_type]

            if allocation.action == "decrease":
                # Recommend selling underperforming assets
                for deal in type_deals[:2]:  # Limit recommendations
                    recommendations.append(
                        RebalancingRecommendation(
                            asset_id=str(deal.id),
                            asset_name=deal.title,
                            asset_type=allocation.asset_type,
                            current_allocation=allocation.current_percentage,
                            recommended_action="consider_sell",
                            target_allocation=allocation.recommended_percentage,
                            rationale=f"{allocation.asset_type} is overweight by {allocation.variance:.1f}%",
                            priority=("medium" if abs(allocation.variance) < 10 else "high"),
                            estimated_impact={
                                "portfolio_balance": abs(allocation.variance),
                                "risk_reduction": (0.5 if allocation.action == "decrease" else 0.0),
                            },
                        )
                    )

            elif allocation.action == "increase":
                # Recommend acquisitions
                recommendations.append(
                    RebalancingRecommendation(
                        asset_id="new_acquisition",
                        asset_name=f"New {allocation.asset_type.title()} Opportunity",
                        asset_type=allocation.asset_type,
                        current_allocation=allocation.current_percentage,
                        recommended_action="acquire",
                        target_allocation=allocation.recommended_percentage,
                        rationale=f"{allocation.asset_type} is underweight by {abs(allocation.variance):.1f}%",
                        priority="medium" if abs(allocation.variance) < 10 else "high",
                        estimated_impact={
                            "portfolio_balance": abs(allocation.variance),
                            "diversification_improvement": 5.0,
                        },
                    )
                )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 1))

        return recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_improvement(
        self,
        metrics: PortfolioMetrics,
        recommendations: list[RebalancingRecommendation],
    ) -> dict[str, float]:
        """Calculate expected improvement from recommendations."""
        total_balance_improvement = sum(
            r.estimated_impact.get("portfolio_balance", 0) for r in recommendations
        )

        return {
            "diversification_improvement": min(20, total_balance_improvement / 2),
            "risk_reduction": 0.05 if total_balance_improvement > 10 else 0.02,
            "expected_yield_change": 0.002,  # 20 bps improvement
            "concentration_reduction": total_balance_improvement,
        }

    async def _generate_summary(
        self,
        metrics: PortfolioMetrics,
        current_allocation: list[AssetAllocation],
        recommendations: list[RebalancingRecommendation],
        request: OptimizationRequest,
    ) -> str:
        """Generate analysis summary."""
        if not self._initialized or not self.llm:
            return self._generate_basic_summary(metrics, recommendations)

        allocation_text = "\n".join(
            f"- {a.asset_type}: {a.current_percentage:.1f}% (target: {a.recommended_percentage:.1f}%)"
            for a in current_allocation
        )

        rec_text = "\n".join(
            f"- {r.recommended_action} {r.asset_type}: {r.rationale}" for r in recommendations[:3]
        )

        prompt = f"""Generate a concise executive summary (3-4 sentences) for this portfolio optimization analysis:

Portfolio Value: ${metrics.total_value:,.0f}
Assets: {metrics.total_assets}
Diversification Score: {metrics.diversification_score}/100
Concentration Risk: {metrics.concentration_risk}

Current Allocation:
{allocation_text}

Top Recommendations:
{rec_text}

Strategy: {request.strategy.value}
Risk Profile: {request.risk_profile.value}

Provide actionable insights in a professional tone."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content
            if isinstance(content, str):
                return content or self._generate_basic_summary(metrics, recommendations)
            return self._generate_basic_summary(metrics, recommendations)
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return self._generate_basic_summary(metrics, recommendations)

    def _generate_basic_summary(
        self,
        metrics: PortfolioMetrics,
        recommendations: list[RebalancingRecommendation],
    ) -> str:
        """Generate basic summary without LLM."""
        return f"""Portfolio Analysis Summary:

Your portfolio of ${metrics.total_value:,.0f} across {metrics.total_assets} assets shows a diversification score of {metrics.diversification_score}/100 with {metrics.concentration_risk} concentration risk.

{len(recommendations)} rebalancing actions are recommended to improve portfolio balance and reduce risk."""

    def _empty_result(self, request: OptimizationRequest) -> PortfolioOptimizationResult:
        """Create empty result for failed optimization."""
        return PortfolioOptimizationResult(
            id=str(uuid4()),
            user_id=request.user_id,
            strategy=request.strategy,
            risk_profile=request.risk_profile,
            metrics=PortfolioMetrics(
                total_value=0,
                total_assets=0,
                weighted_yield=0,
                portfolio_beta=1.0,
                diversification_score=0,
                concentration_risk="unknown",
                liquidity_score=0,
            ),
            current_allocation=[],
            recommendations=[],
            target_allocation={},
            expected_improvement={},
            analysis_summary="Unable to analyze portfolio.",
        )


# Singleton instance
portfolio_optimizer_service = PortfolioOptimizerService()
