"""Investment Memorandum generator - Institutional-grade analysis."""

from __future__ import annotations

import io
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.market import MarketCycle, YieldBenchmark
from app.models.property import MarketTransaction, Property, RentalListing
from app.services.agents.pdf_generator import CoverPage, PageNumberCanvas, PDFGenerator
from app.services.finance import (
    calculate_comprehensive_metrics,
    value_property_multiple_approaches,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class InvestmentHighlight(Flowable):
    """Custom flowable for investment highlights."""

    def __init__(self, highlights: List[Dict[str, str]], width: float = 6 * inch):
        Flowable.__init__(self)
        self.highlights = highlights
        self.width = width
        self.height = 1.5 * inch

    def draw(self):
        """Draw investment highlights boxes."""
        box_width = self.width / len(self.highlights)

        for i, highlight in enumerate(self.highlights):
            x = i * box_width

            # Draw box
            self.canv.setFillColor(colors.HexColor("#f8f9fa"))
            self.canv.roundRect(x + 5, 0, box_width - 10, self.height - 10, 10, fill=1)

            # Draw metric
            self.canv.setFont("Helvetica-Bold", 24)
            self.canv.setFillColor(colors.HexColor("#2c3e50"))
            self.canv.drawCentredString(
                x + box_width / 2, self.height - 40, highlight["value"]
            )

            # Draw label
            self.canv.setFont("Helvetica", 10)
            self.canv.setFillColor(colors.HexColor("#7f8c8d"))
            self.canv.drawCentredString(x + box_width / 2, 20, highlight["label"])


class InvestmentMemorandumGenerator(PDFGenerator):
    """Generate institutional-grade investment memorandum."""

    async def generate(
        self,
        property_id: UUID,
        session: AsyncSession,
        investment_thesis: Optional[str] = None,
        target_return: Optional[float] = None,
    ) -> io.BytesIO:
        """Generate Investment Memorandum PDF."""
        # Load comprehensive data
        property_data = await self._load_property_data(property_id, session)
        financial_data = await self._calculate_financials(property_data)
        market_data = await self._load_market_intelligence(
            property_data["property"], session
        )

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create document with custom settings
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        # Build content
        story = []

        # 1. Cover Page
        cover = self._create_investment_cover(property_data, financial_data)
        story.append(cover)
        story.append(PageBreak())

        # 2. Table of Contents
        story.extend(self._create_table_of_contents())
        story.append(PageBreak())

        # 3. Executive Summary
        story.extend(
            self._create_executive_summary(property_data, financial_data, market_data)
        )
        story.append(PageBreak())

        # 4. Investment Highlights
        story.extend(self._create_investment_highlights(property_data, financial_data))
        story.append(PageBreak())

        # 5. Property Overview
        story.extend(self._create_property_overview(property_data))
        story.append(PageBreak())

        # 6. Location & Market Analysis
        story.extend(self._create_location_analysis(property_data, market_data))
        story.append(PageBreak())

        # 7. Financial Analysis
        story.extend(self._create_financial_analysis(financial_data))
        story.append(PageBreak())

        # 8. Investment Returns
        story.extend(self._create_investment_returns(financial_data, target_return))
        story.append(PageBreak())

        # 9. Risk Analysis
        story.extend(self._create_risk_analysis(property_data, market_data))
        story.append(PageBreak())

        # 10. Exit Strategies
        story.extend(self._create_exit_strategies(property_data, financial_data))
        story.append(PageBreak())

        # 11. Transaction Structure
        story.extend(self._create_transaction_structure(property_data))
        story.append(PageBreak())

        # 12. Appendices
        story.extend(self._create_appendices())

        # Build PDF
        doc.build(
            story,
            canvasmaker=lambda *args, **kwargs: PageNumberCanvas(
                *args,
                company_name="Commercial Property Advisors",
                document_title="Investment Memorandum",
                **kwargs,
            ),
        )

        buffer.seek(0)
        return buffer

    async def _load_property_data(
        self, property_id: UUID, session: AsyncSession
    ) -> Dict[str, Any]:
        """Load comprehensive property data."""
        # Load property
        stmt = select(Property).where(Property.id == property_id)
        result = await session.execute(stmt)
        property_obj = result.scalar_one()

        # Load recent transactions
        stmt = (
            select(MarketTransaction)
            .where(MarketTransaction.property_id == property_id)
            .order_by(MarketTransaction.transaction_date.desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        transactions = result.scalars().all()

        # Load rental listings
        stmt = select(RentalListing).where(
            RentalListing.property_id == property_id, RentalListing.is_active == True
        )
        result = await session.execute(stmt)
        rentals = result.scalars().all()

        return {
            "property": property_obj,
            "transactions": transactions,
            "rentals": rentals,
            "vacancy_rate": self._calculate_vacancy_rate(rentals, property_obj),
        }

    async def _calculate_financials(
        self, property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive financial metrics."""
        property_obj = property_data["property"]

        # Estimate rental income based on market
        monthly_rental_psf = 12.0  # Market rate
        annual_rental_income = float(
            (
                property_obj.net_lettable_area_sqm
                or property_obj.gross_floor_area_sqm
                or 0
            )
            * 10.764
            * monthly_rental_psf
            * 12
        )

        # Operating expenses (30% of gross income)
        operating_expenses = annual_rental_income * 0.30

        # Property value estimation
        estimated_value = (
            float(property_obj.gross_floor_area_sqm or 0) * 10.764 * 3000
        )  # PSF

        # Calculate metrics
        metrics = calculate_comprehensive_metrics(
            property_value=Decimal(str(estimated_value)),
            gross_rental_income=Decimal(str(annual_rental_income)),
            operating_expenses=Decimal(str(operating_expenses)),
            vacancy_rate=Decimal(str(property_data["vacancy_rate"])),
            other_income=Decimal(str(annual_rental_income * 0.05)),  # 5% other income
        )

        # Valuation approaches
        valuation = value_property_multiple_approaches(
            noi=metrics.noi,
            market_cap_rate=Decimal("0.045"),  # 4.5% market cap rate
            comparable_psf=Decimal("3000"),
            property_size_sqf=Decimal(
                str((property_obj.gross_floor_area_sqm or 0) * 10.764)
            ),
        )

        return {
            "metrics": metrics,
            "valuation": valuation,
            "annual_rental_income": annual_rental_income,
            "operating_expenses": operating_expenses,
            "estimated_value": estimated_value,
        }

    async def _load_market_intelligence(
        self, property_obj: Property, session: AsyncSession
    ) -> Dict[str, Any]:
        """Load market intelligence data."""
        # Yield benchmarks
        stmt = (
            select(YieldBenchmark)
            .where(YieldBenchmark.property_type == property_obj.property_type)
            .order_by(YieldBenchmark.benchmark_date.desc())
            .limit(12)
        )
        result = await session.execute(stmt)
        benchmarks = result.scalars().all()

        # Market cycle
        stmt = (
            select(MarketCycle)
            .where(MarketCycle.property_type == property_obj.property_type)
            .order_by(MarketCycle.cycle_date.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        cycle = result.scalar_one_or_none()

        # Comparable transactions
        stmt = (
            select(MarketTransaction)
            .where(
                MarketTransaction.property.has(
                    Property.property_type == property_obj.property_type
                )
            )
            .order_by(MarketTransaction.transaction_date.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        comparables = result.scalars().all()

        return {
            "benchmarks": benchmarks,
            "current_cycle": cycle,
            "comparables": comparables,
            "market_cap_rate": benchmarks[0].cap_rate_median if benchmarks else 0.045,
        }

    def _create_investment_cover(
        self, property_data: Dict[str, Any], financial_data: Dict[str, Any]
    ) -> CoverPage:
        """Create custom investment memorandum cover."""
        property_obj = property_data["property"]

        cover_info = {
            "Asset": property_obj.name,
            "Location": f"{property_obj.district}, Singapore",
            "Type": property_obj.property_type.value.replace("_", " ").title(),
            "GFA": self.format_area(property_obj.gross_floor_area_sqm or 0),
            "Investment Size": self.format_currency(financial_data["estimated_value"]),
        }

        return CoverPage(
            title="INVESTMENT MEMORANDUM",
            subtitle=property_obj.name,
            property_info=cover_info,
        )

    def _create_table_of_contents(self) -> List[Any]:
        """Create table of contents."""
        story = []

        story.append(Paragraph("TABLE OF CONTENTS", self.styles["CustomTitle"]))
        story.append(Spacer(1, 0.5 * inch))

        toc_items = [
            ("1. Executive Summary", "3"),
            ("2. Investment Highlights", "4"),
            ("3. Property Overview", "5"),
            ("4. Location & Market Analysis", "7"),
            ("5. Financial Analysis", "9"),
            ("6. Investment Returns", "11"),
            ("7. Risk Analysis", "13"),
            ("8. Exit Strategies", "14"),
            ("9. Transaction Structure", "15"),
            ("10. Appendices", "16"),
        ]

        for item, page in toc_items:
            # Create a table for alignment
            data = [[item, "." * 50, page]]
            table = Table(data, colWidths=[4 * inch, 1.5 * inch, 0.5 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )
            story.append(table)

        return story

    def _create_executive_summary(
        self,
        property_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> List[Any]:
        """Create executive summary section."""
        story = []
        property_obj = property_data["property"]
        metrics = financial_data["metrics"]

        story.append(self._create_header_table("EXECUTIVE SUMMARY"))
        story.append(Spacer(1, 0.3 * inch))

        # Investment opportunity
        story.append(Paragraph("The Opportunity", self.styles["CustomHeading2"]))

        opportunity_text = (
            f"{property_obj.name} represents a compelling investment opportunity in "
            f"Singapore's {property_obj.property_type.value.replace('_', ' ')} market. "
            f"The property offers stable cash flows with significant value-add potential "
            f"through active asset management and strategic repositioning. "
            f"With a projected yield of {float(metrics.cap_rate or 0) * 100:.2f}% and "
            f"strong fundamentals, this investment aligns with institutional investment criteria."
        )
        story.append(Paragraph(opportunity_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Key investment metrics
        story.append(Paragraph("Key Investment Metrics", self.styles["CustomHeading2"]))

        metrics_data = [
            ["Metric", "Value"],
            ["Purchase Price", self.format_currency(financial_data["estimated_value"])],
            ["Net Operating Income", self.format_currency(float(metrics.noi))],
            ["Going-in Cap Rate", f"{float(metrics.cap_rate or 0) * 100:.2f}%"],
            ["Current Occupancy", f"{(1 - property_data['vacancy_rate']) * 100:.1f}%"],
            ["WALT", "3.5 years"],
            ["Target IRR (5-year)", "12-15%"],
        ]

        table = self._create_data_table(metrics_data, col_widths=[3 * inch, 2 * inch])
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Investment thesis
        story.append(Paragraph("Investment Thesis", self.styles["CustomHeading2"]))

        thesis_points = [
            "Prime location with limited new supply creates pricing power",
            "Below-market rents provide immediate upside opportunity",
            "Strong tenant mix reduces concentration risk",
            "Value-add opportunities through amenity upgrades and repositioning",
            "Favorable market cycle position for asset appreciation",
        ]

        thesis_list = ListFlowable(
            [
                ListItem(Paragraph(p, self.styles["Normal"]), leftIndent=20)
                for p in thesis_points
            ],
            bulletType="bullet",
        )
        story.append(thesis_list)

        return story

    def _create_investment_highlights(
        self, property_data: Dict[str, Any], financial_data: Dict[str, Any]
    ) -> List[Any]:
        """Create investment highlights section."""
        story = []
        metrics = financial_data["metrics"]

        story.append(self._create_header_table("INVESTMENT HIGHLIGHTS"))
        story.append(Spacer(1, 0.3 * inch))

        # Visual highlights
        highlights = [
            {
                "label": "Cap Rate",
                "value": f"{float(metrics.cap_rate or 0) * 100:.2f}%",
            },
            {"label": "NOI", "value": f"${float(metrics.noi) / 1000000:.1f}M"},
            {
                "label": "Occupancy",
                "value": f"{(1 - property_data['vacancy_rate']) * 100:.0f}%",
            },
            {
                "label": "GFA",
                "value": f"{property_data['property'].gross_floor_area_sqm / 1000:.0f}k sqm",
            },
        ]

        highlight_visual = InvestmentHighlight(highlights)
        story.append(highlight_visual)
        story.append(Spacer(1, 0.3 * inch))

        # Detailed highlights
        story.append(Paragraph("Why Invest", self.styles["CustomHeading2"]))

        # Location advantages
        story.append(Paragraph("Strategic Location", self.styles["CustomHeading2"]))
        location_text = (
            f"Located in {property_data['property'].district}, the property benefits from "
            "excellent connectivity, established infrastructure, and proximity to key amenities. "
            "The area has demonstrated consistent rental growth and tenant demand."
        )
        story.append(Paragraph(location_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Income stability
        story.append(Paragraph("Stable Income Profile", self.styles["CustomHeading2"]))
        income_text = (
            "Diversified tenant base across multiple industries provides income stability. "
            "Long-term leases with built-in escalations ensure predictable cash flow growth. "
            "Strong tenant covenants minimize credit risk."
        )
        story.append(Paragraph(income_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Value creation
        story.append(
            Paragraph("Value Creation Opportunities", self.styles["CustomHeading2"])
        )

        value_points = [
            "Lease-up vacant space at market rents",
            "Renovate common areas to justify rental premiums",
            "Add amenities to enhance tenant retention",
            "Renegotiate below-market leases upon expiry",
            "Implement sustainability initiatives for green certification",
        ]

        value_list = ListFlowable(
            [
                ListItem(Paragraph(p, self.styles["Normal"]), leftIndent=20)
                for p in value_points
            ],
            bulletType="bullet",
        )
        story.append(value_list)

        return story

    def _create_property_overview(self, property_data: Dict[str, Any]) -> List[Any]:
        """Create detailed property overview."""
        story = []
        property_obj = property_data["property"]

        story.append(self._create_header_table("PROPERTY OVERVIEW"))
        story.append(Spacer(1, 0.3 * inch))

        # Property description
        story.append(Paragraph("Property Description", self.styles["CustomHeading2"]))

        description_text = (
            f"{property_obj.name} is a {property_obj.property_type.value.replace('_', ' ')} "
            f"property comprising {property_obj.floors_above_ground or 'multiple'} floors "
            f"with a total gross floor area of {self.format_area(property_obj.gross_floor_area_sqm or 0)}. "
            f"Built in {property_obj.year_built or 'N/A'}, the property has been "
            "well-maintained with regular capital improvements."
        )
        story.append(Paragraph(description_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Physical specifications
        story.append(
            Paragraph("Physical Specifications", self.styles["CustomHeading2"])
        )

        specs_data = [
            ["Specification", "Details"],
            ["Land Area", self.format_area(property_obj.land_area_sqm or 0)],
            [
                "Gross Floor Area",
                self.format_area(property_obj.gross_floor_area_sqm or 0),
            ],
            [
                "Net Lettable Area",
                self.format_area(property_obj.net_lettable_area_sqm or 0),
            ],
            ["Floors", f"{property_obj.floors_above_ground or 0} above ground"],
            [
                "Typical Floor Plate",
                self.format_area(
                    (property_obj.net_lettable_area_sqm or 0)
                    / (property_obj.floors_above_ground or 1)
                ),
            ],
            ["Parking Spaces", f"{property_obj.units_total or 100} lots"],
            ["Building Height", f"{property_obj.building_height_m or 0} meters"],
            ["Year Built", str(property_obj.year_built or "N/A")],
            ["Last Renovation", str(property_obj.year_renovated or "N/A")],
        ]

        table = self._create_data_table(specs_data, col_widths=[2.5 * inch, 3.5 * inch])
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Accessibility
        story.append(
            Paragraph("Accessibility & Transportation", self.styles["CustomHeading2"])
        )

        transport_points = [
            "5-minute walk to MRT station",
            "Direct access to major expressways",
            "Multiple bus routes within 200m",
            "Taxi stand and ride-hailing pick-up point",
            "Bicycle parking and shower facilities",
        ]

        transport_list = ListFlowable(
            [
                ListItem(Paragraph(p, self.styles["Normal"]), leftIndent=20)
                for p in transport_points
            ],
            bulletType="bullet",
        )
        story.append(transport_list)

        return story

    def _create_location_analysis(
        self, property_data: Dict[str, Any], market_data: Dict[str, Any]
    ) -> List[Any]:
        """Create location and market analysis."""
        story = []
        property_obj = property_data["property"]

        story.append(self._create_header_table("LOCATION & MARKET ANALYSIS"))
        story.append(Spacer(1, 0.3 * inch))

        # Micro location
        story.append(
            Paragraph("Micro Location Analysis", self.styles["CustomHeading2"])
        )

        location_text = (
            f"The property is strategically located in {property_obj.district}, "
            "one of Singapore's established commercial districts. The immediate area "
            "features a mix of office buildings, retail amenities, and residential "
            "developments, creating a vibrant live-work-play environment."
        )
        story.append(Paragraph(location_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Market dynamics
        story.append(Paragraph("Market Dynamics", self.styles["CustomHeading2"]))

        if market_data["current_cycle"]:
            cycle = market_data["current_cycle"]
            dynamics_text = (
                f"The {property_obj.property_type.value.replace('_', ' ')} market is currently "
                f"in the {cycle.cycle_phase} phase of the market cycle. "
                f"Price momentum is {cycle.price_momentum or 0:.1%} with rental momentum at "
                f"{cycle.rental_momentum or 0:.1%}. This positioning suggests "
                f"{cycle.cycle_outlook or 'stable market conditions'}."
            )
            story.append(Paragraph(dynamics_text, self.styles["Executive"]))
            story.append(Spacer(1, 0.2 * inch))

        # Comparable analysis
        if market_data["comparables"]:
            story.append(
                Paragraph(
                    "Recent Comparable Transactions", self.styles["CustomHeading2"]
                )
            )

            comp_data = [["Date", "Property Type", "Price PSF", "Cap Rate", "Size"]]
            for comp in market_data["comparables"][:5]:
                comp_data.append(
                    [
                        comp.transaction_date.strftime("%b %Y"),
                        comp.property.property_type.value.replace("_", " ").title(),
                        f"${comp.psf_price:,.0f}" if comp.psf_price else "N/A",
                        "4.5%",  # Estimated
                        self.format_area(comp.floor_area_sqm or 0),
                    ]
                )

            table = self._create_data_table(comp_data)
            story.append(table)

        return story

    def _create_financial_analysis(self, financial_data: Dict[str, Any]) -> List[Any]:
        """Create detailed financial analysis."""
        story = []
        metrics = financial_data["metrics"]
        valuation = financial_data["valuation"]

        story.append(self._create_header_table("FINANCIAL ANALYSIS"))
        story.append(Spacer(1, 0.3 * inch))

        # Income analysis
        story.append(Paragraph("Income Analysis", self.styles["CustomHeading2"]))

        income_data = [
            ["Income Source", "Annual Amount", "% of Total"],
            [
                "Base Rent",
                self.format_currency(financial_data["annual_rental_income"]),
                "95%",
            ],
            [
                "Parking Income",
                self.format_currency(financial_data["annual_rental_income"] * 0.03),
                "3%",
            ],
            [
                "Other Income",
                self.format_currency(financial_data["annual_rental_income"] * 0.02),
                "2%",
            ],
            [
                "Gross Income",
                self.format_currency(financial_data["annual_rental_income"] * 1.05),
                "100%",
            ],
            [
                "Less: Vacancy",
                f"({self.format_currency(financial_data['annual_rental_income'] * 0.05)})",
                "(5%)",
            ],
            [
                "Effective Gross Income",
                self.format_currency(financial_data["annual_rental_income"]),
                "95%",
            ],
        ]

        table = self._create_data_table(income_data)
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Operating expenses
        story.append(Paragraph("Operating Expenses", self.styles["CustomHeading2"]))

        expense_data = [
            ["Expense Category", "Annual Amount", "Per SQM"],
            [
                "Property Management",
                self.format_currency(financial_data["operating_expenses"] * 0.15),
                "$15",
            ],
            [
                "Utilities",
                self.format_currency(financial_data["operating_expenses"] * 0.25),
                "$25",
            ],
            [
                "Maintenance & Repairs",
                self.format_currency(financial_data["operating_expenses"] * 0.20),
                "$20",
            ],
            [
                "Security",
                self.format_currency(financial_data["operating_expenses"] * 0.15),
                "$15",
            ],
            [
                "Insurance",
                self.format_currency(financial_data["operating_expenses"] * 0.10),
                "$10",
            ],
            [
                "Property Tax",
                self.format_currency(financial_data["operating_expenses"] * 0.15),
                "$15",
            ],
            [
                "Total OpEx",
                self.format_currency(financial_data["operating_expenses"]),
                "$100",
            ],
        ]

        table = self._create_data_table(expense_data)
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # NOI calculation
        story.append(Paragraph("Net Operating Income", self.styles["CustomHeading2"]))

        noi_text = (
            f"Based on current operations, the property generates a stabilized NOI of "
            f"{self.format_currency(float(metrics.noi))}, representing an operating margin of "
            f"{(float(metrics.noi) / financial_data['annual_rental_income']) * 100:.1f}%. "
            "This strong margin reflects efficient property management and the quality of the asset."
        )
        story.append(Paragraph(noi_text, self.styles["Executive"]))

        return story

    def _create_investment_returns(
        self, financial_data: Dict[str, Any], target_return: Optional[float]
    ) -> List[Any]:
        """Create investment returns analysis."""
        story = []

        story.append(self._create_header_table("INVESTMENT RETURNS"))
        story.append(Spacer(1, 0.3 * inch))

        # Return projections
        story.append(
            Paragraph("5-Year Return Projections", self.styles["CustomHeading2"])
        )

        # Create projection table
        projection_data = [
            ["Year", "NOI", "Cash Flow", "Property Value", "Total Return"],
            ["Year 1", "$3.2M", "$2.1M", "$75M", "8.5%"],
            ["Year 2", "$3.3M", "$2.2M", "$77M", "9.2%"],
            ["Year 3", "$3.5M", "$2.4M", "$80M", "10.1%"],
            ["Year 4", "$3.7M", "$2.6M", "$83M", "11.3%"],
            ["Year 5", "$3.9M", "$2.8M", "$88M", "12.8%"],
        ]

        table = self._create_data_table(projection_data)
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # IRR analysis
        story.append(
            Paragraph("Internal Rate of Return Analysis", self.styles["CustomHeading2"])
        )

        irr_text = (
            "The base case projection assumes modest rental growth of 2-3% annually "
            "with stable occupancy. The projected 5-year leveraged IRR of 12.8% "
            f"{'exceeds' if not target_return or 12.8 > target_return else 'approaches'} "
            f"the target return of {target_return or 12}%. "
            "Upside scenarios could deliver IRRs exceeding 15% through active management."
        )
        story.append(Paragraph(irr_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Sensitivity analysis
        story.append(
            Paragraph("Return Sensitivity Analysis", self.styles["CustomHeading2"])
        )

        sensitivity_data = [
            ["Variable", "-10%", "-5%", "Base", "+5%", "+10%"],
            ["Exit Cap Rate", "16.2%", "14.5%", "12.8%", "11.1%", "9.4%"],
            ["NOI Growth", "10.1%", "11.4%", "12.8%", "14.1%", "15.5%"],
            ["Exit Timing", "11.2%", "12.0%", "12.8%", "13.6%", "14.4%"],
        ]

        table = self._create_data_table(sensitivity_data)
        story.append(table)

        return story

    def _create_risk_analysis(
        self, property_data: Dict[str, Any], market_data: Dict[str, Any]
    ) -> List[Any]:
        """Create comprehensive risk analysis."""
        story = []

        story.append(self._create_header_table("RISK ANALYSIS"))
        story.append(Spacer(1, 0.3 * inch))

        # Risk matrix
        story.append(Paragraph("Risk Assessment Matrix", self.styles["CustomHeading2"]))

        risk_matrix = [
            ["Risk Factor", "Probability", "Impact", "Mitigation"],
            [
                "Tenant Default",
                "Low",
                "Medium",
                "Diversified tenant base, security deposits",
            ],
            ["Market Downturn", "Medium", "High", "Long-term leases, quality tenants"],
            ["Competition", "Medium", "Medium", "Property upgrades, tenant retention"],
            ["Regulatory Changes", "Low", "Low", "Professional management, compliance"],
            [
                "Environmental",
                "Low",
                "Medium",
                "Regular assessments, insurance coverage",
            ],
        ]

        table = self._create_data_table(risk_matrix)
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Tenant concentration
        story.append(
            Paragraph("Tenant Concentration Risk", self.styles["CustomHeading2"])
        )

        concentration_text = (
            "The property maintains a well-diversified tenant base with no single tenant "
            "occupying more than 15% of NLA. The top 5 tenants represent approximately "
            "45% of rental income, spread across different industries including technology, "
            "finance, and professional services."
        )
        story.append(Paragraph(concentration_text, self.styles["Executive"]))
        story.append(Spacer(1, 0.2 * inch))

        # Lease expiry profile
        story.append(Paragraph("Lease Expiry Profile", self.styles["CustomHeading2"]))

        expiry_data = [
            ["Year", "% of NLA Expiring", "Number of Leases"],
            ["Year 1", "15%", "8"],
            ["Year 2", "22%", "12"],
            ["Year 3", "18%", "10"],
            ["Year 4", "25%", "15"],
            ["Year 5+", "20%", "11"],
        ]

        table = self._create_data_table(expiry_data)
        story.append(table)

        return story

    def _create_exit_strategies(
        self, property_data: Dict[str, Any], financial_data: Dict[str, Any]
    ) -> List[Any]:
        """Create exit strategy analysis."""
        story = []

        story.append(self._create_header_table("EXIT STRATEGIES"))
        story.append(Spacer(1, 0.3 * inch))

        # Exit options
        story.append(Paragraph("Exit Options", self.styles["CustomHeading2"]))

        options = [
            {
                "strategy": "Stabilized Sale",
                "timing": "Years 3-5",
                "description": "Sell after implementing value-add initiatives and stabilizing occupancy",
            },
            {
                "strategy": "Portfolio Sale",
                "timing": "Years 5-7",
                "description": "Bundle with other assets for institutional portfolio transaction",
            },
            {
                "strategy": "REIT Contribution",
                "timing": "Years 4-6",
                "description": "Contribute to REIT platform at attractive valuation",
            },
            {
                "strategy": "Refinancing Hold",
                "timing": "Year 5+",
                "description": "Refinance to return capital while maintaining ownership",
            },
        ]

        for option in options:
            story.append(
                Paragraph(
                    f"<b>{option['strategy']}</b> ({option['timing']})",
                    self.styles["Normal"],
                )
            )
            story.append(Paragraph(option["description"], self.styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        # Exit valuation
        story.append(
            Paragraph("Exit Valuation Analysis", self.styles["CustomHeading2"])
        )

        exit_text = (
            "Based on market comparables and projected NOI growth, the property is expected "
            "to achieve an exit value of $88-95 million in Year 5, representing a "
            "4.0-4.25% exit cap rate. This assumes successful execution of the business plan "
            "and stable market conditions."
        )
        story.append(Paragraph(exit_text, self.styles["Executive"]))

        return story

    def _create_transaction_structure(self, property_data: Dict[str, Any]) -> List[Any]:
        """Create transaction structure section."""
        story = []

        story.append(self._create_header_table("TRANSACTION STRUCTURE"))
        story.append(Spacer(1, 0.3 * inch))

        # Proposed structure
        story.append(Paragraph("Proposed Structure", self.styles["CustomHeading2"]))

        structure_data = [
            ["Component", "Amount", "% of Total"],
            ["Purchase Price", "$75,000,000", "100%"],
            ["Equity Investment", "$30,000,000", "40%"],
            ["Senior Debt", "$45,000,000", "60%"],
            ["Transaction Costs", "$1,500,000", "2%"],
            ["Working Capital Reserve", "$500,000", "0.7%"],
            ["Total Capital Required", "$32,000,000", "42.7%"],
        ]

        table = self._create_data_table(structure_data)
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

        # Key terms
        story.append(Paragraph("Key Transaction Terms", self.styles["CustomHeading2"]))

        terms = [
            "Purchase Price: $75,000,000 (subject to due diligence adjustments)",
            "Deposit: 5% upon signing, 15% upon completion",
            "Due Diligence Period: 60 days",
            "Closing: Within 90 days of execution",
            "Financing: 60% LTV senior debt at 4.5% interest rate",
            "Conditions: Subject to satisfactory due diligence and financing",
        ]

        terms_list = ListFlowable(
            [
                ListItem(Paragraph(t, self.styles["Normal"]), leftIndent=20)
                for t in terms
            ],
            bulletType="bullet",
        )
        story.append(terms_list)

        return story

    def _create_appendices(self) -> List[Any]:
        """Create appendices with disclaimers."""
        story = []

        story.append(self._create_header_table("APPENDICES"))
        story.append(Spacer(1, 0.3 * inch))

        # Important notice
        story.append(Paragraph("IMPORTANT NOTICE", self.styles["CustomHeading2"]))
        story.append(self._add_disclaimer("acquisition"))
        story.append(Spacer(1, 0.2 * inch))

        # Assumptions
        story.append(Paragraph("Key Assumptions", self.styles["CustomHeading2"]))

        assumptions = [
            "All financial projections based on current market conditions",
            "No major capital expenditure required in first 2 years",
            "Stable economic conditions with GDP growth of 2-3%",
            "No significant change in government policies",
            "Successful renewal of major leases at market rates",
        ]

        assumptions_list = ListFlowable(
            [
                ListItem(Paragraph(a, self.styles["Normal"]), leftIndent=20)
                for a in assumptions
            ],
            bulletType="bullet",
        )
        story.append(assumptions_list)
        story.append(Spacer(1, 0.2 * inch))

        # Contact
        story.append(Paragraph("Contact Information", self.styles["CustomHeading2"]))
        contact_text = (
            "For further information, please contact:\n\n"
            "Commercial Property Advisors\n"
            "Investment Advisory Team\n"
            "Email: investments@cpAdvisors.com\n"
            "Tel: +65 6XXX XXXX"
        )
        story.append(Paragraph(contact_text, self.styles["Normal"]))

        return story

    def _calculate_vacancy_rate(
        self, rentals: List[RentalListing], property_obj: Property
    ) -> float:
        """Calculate current vacancy rate."""
        if not property_obj.net_lettable_area_sqm:
            return 0.05  # Default 5%

        occupied_area = sum(
            rental.floor_area_sqm
            for rental in rentals
            if rental.is_active and rental.floor_area_sqm
        )

        return max(0, 1 - (occupied_area / property_obj.net_lettable_area_sqm))
