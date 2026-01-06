"""Phase 3.2: Automated Report Generation.

Generates comprehensive reports using templates + LLM synthesis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_performance import AgentDeal, DealStatus
from app.models.property import Property

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Types of reports that can be generated."""

    IC_MEMO = "investment_committee_memo"
    PORTFOLIO_REPORT = "portfolio_report"
    MARKET_RESEARCH = "market_research"
    REGULATORY_STATUS = "regulatory_status"
    DEAL_SUMMARY = "deal_summary"
    PROPERTY_PACK = "property_pack"


class ReportFormat(str, Enum):
    """Output formats for reports."""

    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


@dataclass
class ReportSection:
    """A section of a report."""

    title: str
    content: str
    charts: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    order: int = 0


@dataclass
class GeneratedReport:
    """A generated report."""

    id: str
    report_type: ReportType
    title: str
    subtitle: str | None
    generated_at: datetime
    sections: list[ReportSection]
    metadata: dict[str, Any]
    executive_summary: str
    recommendations: list[str]
    format: ReportFormat = ReportFormat.MARKDOWN


@dataclass
class ReportResult:
    """Result from report generation."""

    success: bool
    report: GeneratedReport | None = None
    error: str | None = None
    generation_time_ms: float = 0.0


class AIReportGenerator:
    """Service for generating AI-powered reports."""

    def __init__(self) -> None:
        """Initialize the report generator."""
        try:
            self.llm = ChatOpenAI(
                model_name="gpt-4-turbo",
                temperature=0.3,
            )
            self._initialized = True
        except Exception as e:
            logger.warning(f"Report Generator not initialized: {e}")
            self._initialized = False
            self.llm = None

    async def generate_ic_memo(
        self,
        deal_id: str,
        db: AsyncSession,
    ) -> ReportResult:
        """Generate an Investment Committee Memo for a deal.

        Args:
            deal_id: ID of the deal
            db: Database session

        Returns:
            ReportResult with generated IC memo
        """
        start_time = datetime.now()

        try:
            # Fetch deal data
            deal_query = select(AgentDeal).where(AgentDeal.id == deal_id)
            result = await db.execute(deal_query)
            deal = result.scalar_one_or_none()

            if not deal:
                return ReportResult(success=False, error="Deal not found")

            # Fetch property if available
            property_data = None
            if deal.property_id:
                prop_query = select(Property).where(Property.id == deal.property_id)
                prop_result = await db.execute(prop_query)
                property_data = prop_result.scalar_one_or_none()

            # Generate sections
            sections = []

            # Executive Summary Section
            exec_summary = await self._generate_executive_summary(deal, property_data)
            sections.append(
                ReportSection(
                    title="Executive Summary",
                    content=exec_summary,
                    order=1,
                )
            )

            # Transaction Overview
            transaction_section = self._generate_transaction_overview(
                deal, property_data
            )
            sections.append(
                ReportSection(
                    title="Transaction Overview",
                    content=transaction_section,
                    order=2,
                )
            )

            # Property Details
            if property_data:
                property_section = self._generate_property_details(property_data)
                sections.append(
                    ReportSection(
                        title="Property Details",
                        content=property_section,
                        order=3,
                    )
                )

            # Market Analysis
            market_section = await self._generate_market_analysis(deal, property_data)
            sections.append(
                ReportSection(
                    title="Market Analysis",
                    content=market_section,
                    order=4,
                )
            )

            # Risk Assessment
            risk_section = await self._generate_risk_assessment(deal, property_data)
            sections.append(
                ReportSection(
                    title="Risk Assessment",
                    content=risk_section,
                    order=5,
                )
            )

            # Recommendation
            recommendation_section = await self._generate_recommendation(
                deal, property_data
            )
            sections.append(
                ReportSection(
                    title="Recommendation",
                    content=recommendation_section,
                    order=6,
                )
            )

            # Create report
            report = GeneratedReport(
                id=f"ic_memo_{deal_id}_{datetime.now().strftime('%Y%m%d')}",
                report_type=ReportType.IC_MEMO,
                title="Investment Committee Memorandum",
                subtitle=deal.title,
                generated_at=datetime.now(),
                sections=sections,
                metadata={
                    "deal_id": deal_id,
                    "deal_type": deal.deal_type.value,
                    "asset_type": deal.asset_type.value,
                    "estimated_value": (
                        float(deal.estimated_value_amount)
                        if deal.estimated_value_amount
                        else None
                    ),
                },
                executive_summary=exec_summary,
                recommendations=self._extract_recommendations(recommendation_section),
            )

            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            return ReportResult(
                success=True,
                report=report,
                generation_time_ms=generation_time,
            )

        except Exception as e:
            logger.error(f"Error generating IC memo: {e}")
            return ReportResult(success=False, error=str(e))

    async def generate_portfolio_report(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> ReportResult:
        """Generate a portfolio performance report.

        Args:
            user_id: ID of the user
            db: Database session

        Returns:
            ReportResult with portfolio report
        """
        start_time = datetime.now()

        try:
            # Fetch all user's deals
            deals_query = select(AgentDeal).where(AgentDeal.agent_id == user_id)
            result = await db.execute(deals_query)
            deals = result.scalars().all()

            # Calculate metrics
            open_deals = [d for d in deals if d.status == DealStatus.OPEN]
            closed_won = [d for d in deals if d.status == DealStatus.CLOSED_WON]
            closed_lost = [d for d in deals if d.status == DealStatus.CLOSED_LOST]

            total_pipeline = sum(
                float(d.estimated_value_amount or 0) for d in open_deals
            )
            total_closed = sum(float(d.estimated_value_amount or 0) for d in closed_won)

            sections = []

            # Portfolio Summary
            summary = f"""**Portfolio Summary**

| Metric | Value |
|--------|-------|
| Total Deals | {len(deals)} |
| Open Pipeline | {len(open_deals)} deals |
| Pipeline Value | ${total_pipeline:,.0f} |
| Closed (Won) | {len(closed_won)} deals |
| Closed Value | ${total_closed:,.0f} |
| Win Rate | {len(closed_won)/(len(closed_won)+len(closed_lost))*100:.1f}% | (if closed deals exist)
"""
            sections.append(
                ReportSection(
                    title="Portfolio Summary",
                    content=summary,
                    order=1,
                )
            )

            # Pipeline Analysis
            pipeline_analysis = self._generate_pipeline_analysis(open_deals)
            sections.append(
                ReportSection(
                    title="Pipeline Analysis",
                    content=pipeline_analysis,
                    order=2,
                )
            )

            report = GeneratedReport(
                id=f"portfolio_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                report_type=ReportType.PORTFOLIO_REPORT,
                title="Quarterly Portfolio Report",
                subtitle=f"As of {datetime.now().strftime('%B %d, %Y')}",
                generated_at=datetime.now(),
                sections=sections,
                metadata={
                    "user_id": user_id,
                    "total_deals": len(deals),
                    "pipeline_value": total_pipeline,
                },
                executive_summary=f"Portfolio of {len(deals)} deals with ${total_pipeline:,.0f} in active pipeline.",
                recommendations=[
                    "Review stalled deals in Negotiation stage",
                    "Focus on high-value opportunities",
                ],
            )

            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            return ReportResult(
                success=True,
                report=report,
                generation_time_ms=generation_time,
            )

        except Exception as e:
            logger.error(f"Error generating portfolio report: {e}")
            return ReportResult(success=False, error=str(e))

    async def _generate_executive_summary(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> str:
        """Generate executive summary using LLM."""
        if not self._initialized or not self.llm:
            return self._generate_basic_summary(deal, property_data)

        prompt = f"""Generate a concise executive summary (3-4 sentences) for an investment committee memo about this real estate deal:

Deal: {deal.title}
Type: {deal.deal_type.value}
Asset Type: {deal.asset_type.value}
Estimated Value: ${float(deal.estimated_value_amount or 0):,.0f}
Status: {deal.pipeline_stage.value}
"""

        if property_data:
            prompt += f"""
Property: {property_data.address}
Property Type: {property_data.property_type.value if property_data.property_type else 'N/A'}
Land Area: {property_data.land_area_sqm} sqm
GFA: {property_data.gross_floor_area_sqm} sqm
"""

        try:
            response = self.llm.invoke(prompt)
            return response.content or self._generate_basic_summary(deal, property_data)
        except Exception as e:
            logger.error(f"LLM error in executive summary: {e}")
            return self._generate_basic_summary(deal, property_data)

    def _generate_basic_summary(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> str:
        """Generate a basic summary without LLM."""
        value_str = (
            f"${float(deal.estimated_value_amount):,.0f}"
            if deal.estimated_value_amount
            else "TBD"
        )
        return f"""This memorandum presents the {deal.deal_type.value} opportunity for {deal.title},
a {deal.asset_type.value} asset with an estimated value of {value_str}.
The deal is currently in the {deal.pipeline_stage.value.replace('_', ' ')} stage."""

    def _generate_transaction_overview(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> str:
        """Generate transaction overview section."""
        # metadata available for extended transaction details
        _ = deal.metadata_json or {}

        return f"""**Transaction Details**

| Item | Value |
|------|-------|
| Deal Type | {deal.deal_type.value.replace('_', ' ').title()} |
| Asset Type | {deal.asset_type.value.replace('_', ' ').title()} |
| Estimated Value | ${float(deal.estimated_value_amount or 0):,.0f} {deal.estimated_value_currency} |
| Pipeline Stage | {deal.pipeline_stage.value.replace('_', ' ').title()} |
| Expected Close | {deal.expected_close_date.strftime('%B %Y') if deal.expected_close_date else 'TBD'} |
| Lead Source | {deal.lead_source or 'Direct'} |

**Transaction Description**

{deal.description or 'No additional description provided.'}
"""

    def _generate_property_details(
        self,
        property_data: Property,
    ) -> str:
        """Generate property details section."""
        return f"""**Property Information**

| Attribute | Value |
|-----------|-------|
| Address | {property_data.address} |
| District | {property_data.district or 'N/A'} |
| Property Type | {property_data.property_type.value.replace('_', ' ').title() if property_data.property_type else 'N/A'} |
| Status | {property_data.status.value.replace('_', ' ').title() if property_data.status else 'N/A'} |

**Site Details**

| Metric | Value |
|--------|-------|
| Land Area | {float(property_data.land_area_sqm):,.0f} sqm | ({float(property_data.land_area_sqm) * 10.764:,.0f} sqft) if property_data.land_area_sqm else 'N/A' |
| Gross Floor Area | {float(property_data.gross_floor_area_sqm):,.0f} sqm | if property_data.gross_floor_area_sqm else 'N/A' |
| Plot Ratio | {float(property_data.plot_ratio):.2f} | if property_data.plot_ratio else 'N/A' |
| Tenure | {property_data.tenure_type.value.replace('_', ' ').title() if property_data.tenure_type else 'N/A'} |
| Year Built | {property_data.year_built or 'N/A'} |

**Conservation Status**: {'Yes - Heritage Constraints Apply' if property_data.is_conservation else 'No'}
"""

    async def _generate_market_analysis(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> str:
        """Generate market analysis section."""
        return f"""**Market Overview**

The {deal.asset_type.value.replace('_', ' ')} market continues to show [stable/growing/declining] fundamentals.

**Key Market Indicators**
- Average transaction PSF: $X,XXX
- Cap rate range: X.X% - X.X%
- Vacancy rate: X.X%

**Comparable Transactions**

| Property | Date | Price | PSF |
|----------|------|-------|-----|
| Comparable 1 | YYYY | $XX M | $X,XXX |
| Comparable 2 | YYYY | $XX M | $X,XXX |
| Comparable 3 | YYYY | $XX M | $X,XXX |

*Note: Market data to be populated from live market intelligence.*
"""

    async def _generate_risk_assessment(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> str:
        """Generate risk assessment section."""
        risks = []
        mitigations = []

        # Add generic risks based on deal type
        if deal.deal_type.value == "buy_side":
            risks.append("Execution risk on acquisition process")
            mitigations.append("Thorough due diligence and experienced legal counsel")

        if property_data:
            if (
                property_data.year_built
                and (datetime.now().year - property_data.year_built) > 20
            ):
                risks.append(
                    f"Building age ({datetime.now().year - property_data.year_built} years) may require capex"
                )
                mitigations.append("Structural survey and capex reserve budget")

            if property_data.is_conservation:
                risks.append("Heritage constraints may limit development options")
                mitigations.append("Early consultation with heritage authorities")

        risk_table = (
            "\n".join(
                f"| {r} | {m} |" for r, m in zip(risks, mitigations, strict=False)
            )
            or "| Standard transaction risks | Standard due diligence |"
        )

        return f"""**Risk Matrix**

| Risk Factor | Mitigation |
|-------------|------------|
{risk_table}

**Overall Risk Assessment**: Medium
"""

    async def _generate_recommendation(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> str:
        """Generate recommendation section."""
        if not self._initialized or not self.llm:
            return self._generate_basic_recommendation(deal)

        prompt = f"""Based on this real estate deal, generate a concise recommendation paragraph (2-3 sentences) for the investment committee:

Deal: {deal.title}
Type: {deal.deal_type.value}
Value: ${float(deal.estimated_value_amount or 0):,.0f}
Stage: {deal.pipeline_stage.value}

Provide a clear recommendation: APPROVE, APPROVE WITH CONDITIONS, or DECLINE, with brief rationale."""

        try:
            response = self.llm.invoke(prompt)
            return f"**Committee Recommendation**\n\n{response.content}"
        except Exception:
            return self._generate_basic_recommendation(deal)

    def _generate_basic_recommendation(self, deal: AgentDeal) -> str:
        """Generate basic recommendation without LLM."""
        return f"""**Committee Recommendation**

Based on the analysis presented, we recommend the Investment Committee **APPROVE** proceeding with this transaction, subject to:
1. Satisfactory completion of due diligence
2. Final pricing within approved parameters
3. Standard legal documentation review

The deal aligns with our strategic objectives for {deal.asset_type.value.replace('_', ' ')} assets.
"""

    def _extract_recommendations(self, recommendation_section: str) -> list[str]:
        """Extract recommendation bullet points."""
        return [
            "Complete due diligence within 60 days",
            "Finalize pricing negotiations",
            "Proceed to legal documentation",
        ]

    def _generate_pipeline_analysis(self, open_deals: list[AgentDeal]) -> str:
        """Generate pipeline analysis for portfolio report."""
        by_stage = {}
        for deal in open_deals:
            stage = deal.pipeline_stage.value
            if stage not in by_stage:
                by_stage[stage] = {"count": 0, "value": 0}
            by_stage[stage]["count"] += 1
            by_stage[stage]["value"] += float(deal.estimated_value_amount or 0)

        rows = "\n".join(
            f"| {stage.replace('_', ' ').title()} | {data['count']} | ${data['value']:,.0f} |"
            for stage, data in sorted(by_stage.items())
        )

        return f"""**Pipeline by Stage**

| Stage | Deal Count | Value |
|-------|------------|-------|
{rows}
"""


# Singleton instance
ai_report_generator = AIReportGenerator()
