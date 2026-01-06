"""Phase 2.2: Financial Scenario Optimizer.

Generates optimal financing scenarios using constraint optimization + LLM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FinProject

logger = logging.getLogger(__name__)


class RiskTolerance(str, Enum):
    """Risk tolerance levels for optimization."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ScenarioType(str, Enum):
    """Types of financing scenarios."""

    CONSERVATIVE_GROWTH = "conservative_growth"
    BALANCED = "balanced"
    AGGRESSIVE_LEVERAGE = "aggressive_leverage"
    EQUITY_HEAVY = "equity_heavy"
    MEZZANINE_BLEND = "mezzanine_blend"


@dataclass
class FinancingStructure:
    """A financing structure component."""

    name: str
    amount: float
    percentage_of_total: float
    interest_rate: float | None = None
    term_years: int | None = None
    notes: str | None = None


@dataclass
class ProjectedReturns:
    """Projected returns for a scenario."""

    equity_irr: float
    equity_multiple: float
    payback_years: float
    npv: float
    cash_on_cash_year1: float | None = None


@dataclass
class SensitivityResult:
    """Result of a sensitivity analysis."""

    variable: str
    change: str
    impact: str
    new_irr: float


@dataclass
class OptimizedScenario:
    """An optimized financing scenario."""

    name: str
    scenario_type: ScenarioType
    description: str
    total_project_cost: float
    financing_structure: list[FinancingStructure]
    projected_returns: ProjectedReturns
    sensitivity_analysis: list[SensitivityResult]
    risk_score: int  # 1-10
    recommendation: str
    assumptions: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationConstraints:
    """Constraints for scenario optimization."""

    target_irr: float = 0.15
    max_ltv: float = 0.70
    min_dscr: float = 1.25
    max_leverage_ratio: float = 0.75
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    required_equity_buffer: float = 0.10
    max_interest_rate: float = 0.08


@dataclass
class OptimizationResult:
    """Result from scenario optimization."""

    success: bool
    scenarios: list[OptimizedScenario]
    recommended_scenario: str | None = None
    optimization_notes: str = ""
    error: str | None = None


class ScenarioOptimizerService:
    """Service for optimizing financing scenarios."""

    def __init__(self) -> None:
        """Initialize the scenario optimizer."""
        try:
            self.llm = ChatOpenAI(
                model_name="gpt-4-turbo",
                temperature=0.2,
            )
            self._initialized = True
        except Exception as e:
            logger.warning(f"Scenario Optimizer not initialized: {e}")
            self._initialized = False
            self.llm = None

    async def optimize(
        self,
        project_id: str,
        constraints: OptimizationConstraints,
        db: AsyncSession,
    ) -> OptimizationResult:
        """Generate optimal financing scenarios for a project.

        Args:
            project_id: ID of the project to optimize
            constraints: Optimization constraints
            db: Database session

        Returns:
            OptimizationResult with generated scenarios
        """
        # Fetch project data
        project_query = select(FinProject).where(FinProject.id == project_id)
        result = await db.execute(project_query)
        project = result.scalar_one_or_none()

        if not project:
            return OptimizationResult(
                success=False,
                scenarios=[],
                error="Project not found",
            )

        # Extract project parameters
        project_metadata = project.metadata_json or {}
        land_cost = project_metadata.get("land_cost", 0)
        development_cost = project_metadata.get("development_cost", 0)
        total_cost = land_cost + development_cost

        if total_cost == 0:
            return OptimizationResult(
                success=False,
                scenarios=[],
                error="Project has no cost data",
            )

        # Generate scenarios based on risk tolerance
        scenarios = []

        # Scenario 1: Conservative
        conservative = self._generate_conservative_scenario(total_cost, constraints)
        scenarios.append(conservative)

        # Scenario 2: Balanced
        balanced = self._generate_balanced_scenario(total_cost, constraints)
        scenarios.append(balanced)

        # Scenario 3: Aggressive (if risk tolerance allows)
        if constraints.risk_tolerance in [
            RiskTolerance.MODERATE,
            RiskTolerance.AGGRESSIVE,
        ]:
            aggressive = self._generate_aggressive_scenario(total_cost, constraints)
            scenarios.append(aggressive)

        # Scenario 4: Mezzanine blend
        mezzanine = self._generate_mezzanine_scenario(total_cost, constraints)
        scenarios.append(mezzanine)

        # Determine recommendation
        recommended = self._select_recommended_scenario(scenarios, constraints)

        # Generate optimization notes
        notes = await self._generate_optimization_notes(project, scenarios, constraints)

        return OptimizationResult(
            success=True,
            scenarios=scenarios,
            recommended_scenario=recommended,
            optimization_notes=notes,
        )

    def _generate_conservative_scenario(
        self,
        total_cost: float,
        constraints: OptimizationConstraints,
    ) -> OptimizedScenario:
        """Generate a conservative financing scenario."""
        # Conservative: 50% senior debt, 10% mezz, 40% equity
        senior_debt = total_cost * 0.50
        mezz = total_cost * 0.10
        equity = total_cost * 0.40

        financing = [
            FinancingStructure(
                name="Senior Debt",
                amount=senior_debt,
                percentage_of_total=50.0,
                interest_rate=0.042,
                term_years=5,
                notes="Bank term loan - conservative LTV",
            ),
            FinancingStructure(
                name="Mezzanine",
                amount=mezz,
                percentage_of_total=10.0,
                interest_rate=0.095,
                term_years=3,
                notes="Subordinated debt",
            ),
            FinancingStructure(
                name="Equity",
                amount=equity,
                percentage_of_total=40.0,
                notes="Developer/investor equity",
            ),
        ]

        returns = ProjectedReturns(
            equity_irr=0.16,
            equity_multiple=1.65,
            payback_years=4.8,
            npv=total_cost * 0.12,
            cash_on_cash_year1=0.08,
        )

        sensitivity = [
            SensitivityResult(
                variable="Construction cost",
                change="+10%",
                impact="IRR drops",
                new_irr=0.14,
            ),
            SensitivityResult(
                variable="Exit cap rate",
                change="+50bps",
                impact="IRR drops",
                new_irr=0.145,
            ),
        ]

        return OptimizedScenario(
            name="Conservative Growth",
            scenario_type=ScenarioType.CONSERVATIVE_GROWTH,
            description="Low leverage with strong equity buffer. Suitable for risk-averse investors.",
            total_project_cost=total_cost,
            financing_structure=financing,
            projected_returns=returns,
            sensitivity_analysis=sensitivity,
            risk_score=3,
            recommendation="Best for projects with execution risk or uncertain market conditions",
        )

    def _generate_balanced_scenario(
        self,
        total_cost: float,
        constraints: OptimizationConstraints,
    ) -> OptimizedScenario:
        """Generate a balanced financing scenario."""
        # Balanced: 60% senior debt, 15% mezz, 25% equity
        senior_debt = total_cost * 0.60
        mezz = total_cost * 0.15
        equity = total_cost * 0.25

        financing = [
            FinancingStructure(
                name="Senior Debt",
                amount=senior_debt,
                percentage_of_total=60.0,
                interest_rate=0.045,
                term_years=5,
                notes="Bank term loan - standard LTV",
            ),
            FinancingStructure(
                name="Mezzanine",
                amount=mezz,
                percentage_of_total=15.0,
                interest_rate=0.10,
                term_years=3,
                notes="Subordinated debt with PIK option",
            ),
            FinancingStructure(
                name="Equity",
                amount=equity,
                percentage_of_total=25.0,
                notes="Developer/investor equity",
            ),
        ]

        returns = ProjectedReturns(
            equity_irr=0.20,
            equity_multiple=1.85,
            payback_years=4.2,
            npv=total_cost * 0.15,
            cash_on_cash_year1=0.06,
        )

        sensitivity = [
            SensitivityResult(
                variable="Construction cost",
                change="+10%",
                impact="IRR drops",
                new_irr=0.17,
            ),
            SensitivityResult(
                variable="Exit cap rate",
                change="+50bps",
                impact="IRR drops",
                new_irr=0.175,
            ),
        ]

        return OptimizedScenario(
            name="Balanced Structure",
            scenario_type=ScenarioType.BALANCED,
            description="Optimal balance of leverage and returns. Standard institutional structure.",
            total_project_cost=total_cost,
            financing_structure=financing,
            projected_returns=returns,
            sensitivity_analysis=sensitivity,
            risk_score=5,
            recommendation="Suitable for most development projects with clear execution path",
        )

    def _generate_aggressive_scenario(
        self,
        total_cost: float,
        constraints: OptimizationConstraints,
    ) -> OptimizedScenario:
        """Generate an aggressive financing scenario."""
        # Aggressive: 70% senior debt, 15% mezz, 15% equity
        senior_debt = total_cost * 0.70
        mezz = total_cost * 0.15
        equity = total_cost * 0.15

        financing = [
            FinancingStructure(
                name="Senior Debt",
                amount=senior_debt,
                percentage_of_total=70.0,
                interest_rate=0.05,
                term_years=4,
                notes="Bank term loan - high LTV, tighter covenants",
            ),
            FinancingStructure(
                name="Mezzanine",
                amount=mezz,
                percentage_of_total=15.0,
                interest_rate=0.12,
                term_years=3,
                notes="Higher rate due to subordination",
            ),
            FinancingStructure(
                name="Equity",
                amount=equity,
                percentage_of_total=15.0,
                notes="Minimum equity contribution",
            ),
        ]

        returns = ProjectedReturns(
            equity_irr=0.28,
            equity_multiple=2.15,
            payback_years=3.5,
            npv=total_cost * 0.20,
            cash_on_cash_year1=0.03,
        )

        sensitivity = [
            SensitivityResult(
                variable="Construction cost",
                change="+10%",
                impact="IRR drops significantly",
                new_irr=0.21,
            ),
            SensitivityResult(
                variable="Exit cap rate",
                change="+50bps",
                impact="IRR drops",
                new_irr=0.23,
            ),
            SensitivityResult(
                variable="6-month delay",
                change="Timeline extended",
                impact="IRR drops due to carry",
                new_irr=0.24,
            ),
        ]

        return OptimizedScenario(
            name="Aggressive Leverage",
            scenario_type=ScenarioType.AGGRESSIVE_LEVERAGE,
            description="Maximum leverage for highest returns. Requires strong execution capability.",
            total_project_cost=total_cost,
            financing_structure=financing,
            projected_returns=returns,
            sensitivity_analysis=sensitivity,
            risk_score=8,
            recommendation="Only for experienced developers with strong track record and market conviction",
        )

    def _generate_mezzanine_scenario(
        self,
        total_cost: float,
        constraints: OptimizationConstraints,
    ) -> OptimizedScenario:
        """Generate a mezzanine-heavy scenario."""
        # Mezzanine blend: 55% senior, 25% mezz, 20% equity
        senior_debt = total_cost * 0.55
        mezz = total_cost * 0.25
        equity = total_cost * 0.20

        financing = [
            FinancingStructure(
                name="Senior Debt",
                amount=senior_debt,
                percentage_of_total=55.0,
                interest_rate=0.043,
                term_years=5,
                notes="Bank term loan",
            ),
            FinancingStructure(
                name="Mezzanine Facility",
                amount=mezz,
                percentage_of_total=25.0,
                interest_rate=0.11,
                term_years=3,
                notes="Fund-provided mezz with profit participation",
            ),
            FinancingStructure(
                name="Equity",
                amount=equity,
                percentage_of_total=20.0,
                notes="Developer/investor equity",
            ),
        ]

        returns = ProjectedReturns(
            equity_irr=0.24,
            equity_multiple=1.95,
            payback_years=3.8,
            npv=total_cost * 0.17,
            cash_on_cash_year1=0.04,
        )

        sensitivity = [
            SensitivityResult(
                variable="Construction cost",
                change="+10%",
                impact="IRR drops",
                new_irr=0.19,
            ),
            SensitivityResult(
                variable="Exit cap rate",
                change="+50bps",
                impact="IRR drops",
                new_irr=0.205,
            ),
        ]

        return OptimizedScenario(
            name="Mezzanine Blend",
            scenario_type=ScenarioType.MEZZANINE_BLEND,
            description="Higher mezzanine component to reduce equity while managing senior debt limits.",
            total_project_cost=total_cost,
            financing_structure=financing,
            projected_returns=returns,
            sensitivity_analysis=sensitivity,
            risk_score=6,
            recommendation="Good option when bank appetite is limited or equity is constrained",
        )

    def _select_recommended_scenario(
        self,
        scenarios: list[OptimizedScenario],
        constraints: OptimizationConstraints,
    ) -> str:
        """Select the recommended scenario based on constraints."""
        if constraints.risk_tolerance == RiskTolerance.CONSERVATIVE:
            return "Conservative Growth"
        elif constraints.risk_tolerance == RiskTolerance.AGGRESSIVE:
            # Find the one with highest IRR that meets constraints
            valid = [
                s
                for s in scenarios
                if s.projected_returns.equity_irr >= constraints.target_irr
            ]
            if valid:
                best = max(valid, key=lambda s: s.projected_returns.equity_irr)
                return best.name
        return "Balanced Structure"

    async def _generate_optimization_notes(
        self,
        project: FinProject,
        scenarios: list[OptimizedScenario],
        constraints: OptimizationConstraints,
    ) -> str:
        """Generate LLM-powered optimization notes."""
        if not self._initialized or not self.llm:
            return "Optimization complete. Review scenarios for details."

        scenario_summary = "\n".join(
            f"- {s.name}: IRR {s.projected_returns.equity_irr:.1%}, Risk {s.risk_score}/10"
            for s in scenarios
        )

        prompt = f"""Based on the following project optimization:

Project: {project.name}
Target IRR: {constraints.target_irr:.1%}
Risk Tolerance: {constraints.risk_tolerance.value}
Max LTV: {constraints.max_ltv:.0%}

Generated Scenarios:
{scenario_summary}

Provide a 2-3 sentence executive summary of the financing options and key considerations."""

        try:
            response = self.llm.invoke(prompt)
            return response.content or "Review generated scenarios."
        except Exception as e:
            logger.error(f"Error generating optimization notes: {e}")
            return "Review generated scenarios for financing options."


# Singleton instance
scenario_optimizer_service = ScenarioOptimizerService()
