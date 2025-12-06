"""ARGUS Enterprise export service.

Generates 6 CSV files for import into ARGUS Enterprise DCF software:
1. Property.csv - Basic property information
2. Tenant.csv - Lease schedules and tenant data
3. Revenue.csv - Income projections by period
4. Expense.csv - Operating expenses by category
5. Market.csv - Market rent and vacancy assumptions
6. Valuation.csv - Cap rates and DCF parameters
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

import structlog
from backend._compat.datetime import utcnow

logger = structlog.get_logger()


@dataclass
class ARGUSPropertyRecord:
    """Property-level data for ARGUS import."""

    property_id: str
    property_name: str
    address: str
    city: str
    state_province: str
    postal_code: str
    country: str = "USA"
    property_type: str = "Office"  # Office, Retail, Industrial, Multi-Family, Mixed-Use
    building_sqft: float = 0.0
    land_sqft: float = 0.0
    year_built: Optional[int] = None
    num_floors: Optional[int] = None
    num_units: Optional[int] = None
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[float] = None


@dataclass
class ARGUSTenantRecord:
    """Tenant/lease data for ARGUS import."""

    property_id: str
    tenant_id: str
    tenant_name: str
    suite_unit: str
    leased_sqft: float
    lease_start: date
    lease_end: date
    base_rent_psf: float  # Per sqft per year
    rent_escalation_pct: float = 0.03  # Annual escalation
    free_rent_months: int = 0
    tenant_improvement_psf: float = 0.0
    leasing_commission_pct: float = 0.0
    renewal_probability: float = 0.65
    renewal_term_months: int = 60


@dataclass
class ARGUSRevenueRecord:
    """Revenue projection record for ARGUS import."""

    property_id: str
    period: int  # Month number (1-120 for 10-year DCF)
    period_date: date
    base_rent: float
    percentage_rent: float = 0.0
    parking_revenue: float = 0.0
    other_revenue: float = 0.0
    vacancy_loss: float = 0.0
    concessions: float = 0.0
    effective_gross_income: float = 0.0


@dataclass
class ARGUSExpenseRecord:
    """Operating expense record for ARGUS import."""

    property_id: str
    expense_category: str  # Property Tax, Insurance, Utilities, etc.
    annual_amount: float
    growth_rate_pct: float = 0.025
    recovery_type: str = "CAM"  # CAM, NNN, Gross, None
    recovery_pct: float = 0.0


@dataclass
class ARGUSMarketRecord:
    """Market assumptions for ARGUS import."""

    property_id: str
    use_type: str  # Office, Retail, Industrial
    market_rent_psf: float
    market_rent_growth_pct: float = 0.03
    market_vacancy_pct: float = 0.08
    market_vacancy_trend: str = "Stable"  # Improving, Stable, Declining
    absorption_period_months: int = 12


@dataclass
class ARGUSValuationRecord:
    """Valuation parameters for ARGUS import."""

    property_id: str
    analysis_start_date: date
    analysis_period_months: int = 120  # 10-year hold
    discount_rate_pct: float = 0.085
    going_in_cap_rate_pct: float = 0.055
    terminal_cap_rate_pct: float = 0.060
    cap_rate_spread_bps: int = 50  # Spread over treasury
    cost_of_sale_pct: float = 0.02
    inflation_rate_pct: float = 0.025


@dataclass
class ARGUSExportBundle:
    """Complete ARGUS export data bundle."""

    property: ARGUSPropertyRecord
    tenants: List[ARGUSTenantRecord] = field(default_factory=list)
    revenue: List[ARGUSRevenueRecord] = field(default_factory=list)
    expenses: List[ARGUSExpenseRecord] = field(default_factory=list)
    market: List[ARGUSMarketRecord] = field(default_factory=list)
    valuation: ARGUSValuationRecord = field(
        default_factory=lambda: ARGUSValuationRecord(
            property_id="", analysis_start_date=date.today()
        )
    )


class ARGUSExportService:
    """Service for generating ARGUS Enterprise export files."""

    def __init__(self) -> None:
        self.export_date = utcnow()

    def generate_export_zip(self, bundle: ARGUSExportBundle) -> bytes:
        """Generate a ZIP file containing all 6 ARGUS CSVs."""
        logger.info("argus.generate_export", property_id=bundle.property.property_id)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("Property.csv", self._generate_property_csv(bundle.property))
            zf.writestr("Tenant.csv", self._generate_tenant_csv(bundle.tenants))
            zf.writestr("Revenue.csv", self._generate_revenue_csv(bundle.revenue))
            zf.writestr("Expense.csv", self._generate_expense_csv(bundle.expenses))
            zf.writestr("Market.csv", self._generate_market_csv(bundle.market))
            zf.writestr("Valuation.csv", self._generate_valuation_csv(bundle.valuation))
            zf.writestr("README.txt", self._generate_readme(bundle))

        return zip_buffer.getvalue()

    def _generate_property_csv(self, prop: ARGUSPropertyRecord) -> str:
        """Generate Property.csv content."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Property_ID",
                "Property_Name",
                "Address",
                "City",
                "State_Province",
                "Postal_Code",
                "Country",
                "Property_Type",
                "Building_SF",
                "Land_SF",
                "Year_Built",
                "Num_Floors",
                "Num_Units",
                "Acquisition_Date",
                "Acquisition_Price",
            ]
        )

        # Data row
        writer.writerow(
            [
                prop.property_id,
                prop.property_name,
                prop.address,
                prop.city,
                prop.state_province,
                prop.postal_code,
                prop.country,
                prop.property_type,
                prop.building_sqft,
                prop.land_sqft,
                prop.year_built or "",
                prop.num_floors or "",
                prop.num_units or "",
                prop.acquisition_date.isoformat() if prop.acquisition_date else "",
                prop.acquisition_price or "",
            ]
        )

        return output.getvalue()

    def _generate_tenant_csv(self, tenants: List[ARGUSTenantRecord]) -> str:
        """Generate Tenant.csv content."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Property_ID",
                "Tenant_ID",
                "Tenant_Name",
                "Suite_Unit",
                "Leased_SF",
                "Lease_Start",
                "Lease_End",
                "Base_Rent_PSF",
                "Rent_Escalation_Pct",
                "Free_Rent_Months",
                "TI_PSF",
                "Leasing_Commission_Pct",
                "Renewal_Probability",
                "Renewal_Term_Months",
            ]
        )

        # Data rows
        for tenant in tenants:
            writer.writerow(
                [
                    tenant.property_id,
                    tenant.tenant_id,
                    tenant.tenant_name,
                    tenant.suite_unit,
                    tenant.leased_sqft,
                    tenant.lease_start.isoformat(),
                    tenant.lease_end.isoformat(),
                    tenant.base_rent_psf,
                    tenant.rent_escalation_pct,
                    tenant.free_rent_months,
                    tenant.tenant_improvement_psf,
                    tenant.leasing_commission_pct,
                    tenant.renewal_probability,
                    tenant.renewal_term_months,
                ]
            )

        return output.getvalue()

    def _generate_revenue_csv(self, revenue: List[ARGUSRevenueRecord]) -> str:
        """Generate Revenue.csv content."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Property_ID",
                "Period",
                "Period_Date",
                "Base_Rent",
                "Percentage_Rent",
                "Parking_Revenue",
                "Other_Revenue",
                "Vacancy_Loss",
                "Concessions",
                "Effective_Gross_Income",
            ]
        )

        # Data rows
        for rev in revenue:
            writer.writerow(
                [
                    rev.property_id,
                    rev.period,
                    rev.period_date.isoformat(),
                    rev.base_rent,
                    rev.percentage_rent,
                    rev.parking_revenue,
                    rev.other_revenue,
                    rev.vacancy_loss,
                    rev.concessions,
                    rev.effective_gross_income,
                ]
            )

        return output.getvalue()

    def _generate_expense_csv(self, expenses: List[ARGUSExpenseRecord]) -> str:
        """Generate Expense.csv content."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Property_ID",
                "Expense_Category",
                "Annual_Amount",
                "Growth_Rate_Pct",
                "Recovery_Type",
                "Recovery_Pct",
            ]
        )

        # Data rows
        for exp in expenses:
            writer.writerow(
                [
                    exp.property_id,
                    exp.expense_category,
                    exp.annual_amount,
                    exp.growth_rate_pct,
                    exp.recovery_type,
                    exp.recovery_pct,
                ]
            )

        return output.getvalue()

    def _generate_market_csv(self, market: List[ARGUSMarketRecord]) -> str:
        """Generate Market.csv content."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Property_ID",
                "Use_Type",
                "Market_Rent_PSF",
                "Market_Rent_Growth_Pct",
                "Market_Vacancy_Pct",
                "Market_Vacancy_Trend",
                "Absorption_Period_Months",
            ]
        )

        # Data rows
        for mkt in market:
            writer.writerow(
                [
                    mkt.property_id,
                    mkt.use_type,
                    mkt.market_rent_psf,
                    mkt.market_rent_growth_pct,
                    mkt.market_vacancy_pct,
                    mkt.market_vacancy_trend,
                    mkt.absorption_period_months,
                ]
            )

        return output.getvalue()

    def _generate_valuation_csv(self, val: ARGUSValuationRecord) -> str:
        """Generate Valuation.csv content."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Property_ID",
                "Analysis_Start_Date",
                "Analysis_Period_Months",
                "Discount_Rate_Pct",
                "Going_In_Cap_Rate_Pct",
                "Terminal_Cap_Rate_Pct",
                "Cap_Rate_Spread_BPS",
                "Cost_Of_Sale_Pct",
                "Inflation_Rate_Pct",
            ]
        )

        # Data row
        writer.writerow(
            [
                val.property_id,
                val.analysis_start_date.isoformat(),
                val.analysis_period_months,
                val.discount_rate_pct,
                val.going_in_cap_rate_pct,
                val.terminal_cap_rate_pct,
                val.cap_rate_spread_bps,
                val.cost_of_sale_pct,
                val.inflation_rate_pct,
            ]
        )

        return output.getvalue()

    def _generate_readme(self, bundle: ARGUSExportBundle) -> str:
        """Generate README.txt with export metadata."""
        return f"""ARGUS Enterprise Export
========================

Export Date: {self.export_date.isoformat()}
Property: {bundle.property.property_name}
Property ID: {bundle.property.property_id}

Files Included:
- Property.csv: Basic property information
- Tenant.csv: {len(bundle.tenants)} tenant record(s)
- Revenue.csv: {len(bundle.revenue)} revenue projection(s)
- Expense.csv: {len(bundle.expenses)} expense categor(ies)
- Market.csv: {len(bundle.market)} market assumption record(s)
- Valuation.csv: DCF and valuation parameters

Import Instructions:
1. Open ARGUS Enterprise
2. Select File > Import > CSV Import Wizard
3. Import files in order: Property, Tenant, Market, Expense, Revenue, Valuation
4. Review and verify imported data

Generated by Optimal Build - Building Compliance Platform
"""

    def build_bundle_from_scenario(
        self,
        scenario_data: Dict[str, Any],
        property_data: Dict[str, Any],
    ) -> ARGUSExportBundle:
        """Build an ARGUS export bundle from finance scenario and property data."""
        logger.info("argus.build_bundle", scenario_id=scenario_data.get("id"))

        property_id = str(property_data.get("id", "PROP-001"))
        analysis_start = date.today()

        # Build property record
        prop = ARGUSPropertyRecord(
            property_id=property_id,
            property_name=property_data.get("name", "Untitled Property"),
            address=property_data.get("address", ""),
            city=property_data.get("city", ""),
            state_province=property_data.get("state", ""),
            postal_code=property_data.get("postal_code", ""),
            country=property_data.get("country", "USA"),
            property_type=property_data.get("property_type", "Office"),
            building_sqft=float(property_data.get("gfa_sqft", 0)),
            land_sqft=float(property_data.get("site_area_sqft", 0)),
            year_built=property_data.get("year_built"),
            num_floors=property_data.get("floors"),
            num_units=property_data.get("num_units"),
        )

        # Build tenant records from lease assumptions
        tenants: List[ARGUSTenantRecord] = []
        lease_assumptions = scenario_data.get("lease_assumptions", [])
        for i, lease in enumerate(lease_assumptions):
            tenants.append(
                ARGUSTenantRecord(
                    property_id=property_id,
                    tenant_id=f"T-{i+1:03d}",
                    tenant_name=lease.get("tenant_name", f"Tenant {i+1}"),
                    suite_unit=lease.get("suite", f"Suite {i+1}"),
                    leased_sqft=float(lease.get("sqft", 0)),
                    lease_start=date.fromisoformat(
                        lease.get("start_date", analysis_start.isoformat())
                    ),
                    lease_end=date.fromisoformat(
                        lease.get(
                            "end_date",
                            analysis_start.replace(
                                year=analysis_start.year + 5
                            ).isoformat(),
                        )
                    ),
                    base_rent_psf=float(lease.get("rent_psf", 35.0)),
                    rent_escalation_pct=float(lease.get("escalation_pct", 0.03)),
                    free_rent_months=int(lease.get("free_rent_months", 0)),
                    tenant_improvement_psf=float(lease.get("ti_psf", 0)),
                    renewal_probability=float(lease.get("renewal_prob", 0.65)),
                )
            )

        # Build expense records
        expenses: List[ARGUSExpenseRecord] = []
        expense_categories = [
            ("Property Tax", "property_tax", "None", 0.0),
            ("Insurance", "insurance", "CAM", 1.0),
            ("Utilities", "utilities", "CAM", 0.85),
            ("R&M", "repairs_maintenance", "CAM", 1.0),
            ("Management Fee", "management_fee", "None", 0.0),
            ("Janitorial", "janitorial", "CAM", 1.0),
            ("Security", "security", "CAM", 0.75),
            ("Landscaping", "landscaping", "CAM", 1.0),
        ]
        opex = scenario_data.get("operating_expenses", {})
        for category, key, recovery_type, recovery_pct in expense_categories:
            amount = opex.get(key, 0)
            if amount > 0:
                expenses.append(
                    ARGUSExpenseRecord(
                        property_id=property_id,
                        expense_category=category,
                        annual_amount=float(amount),
                        growth_rate_pct=float(opex.get("growth_rate", 0.025)),
                        recovery_type=recovery_type,
                        recovery_pct=recovery_pct,
                    )
                )

        # Build market records
        market: List[ARGUSMarketRecord] = []
        market_assumptions = scenario_data.get("market_assumptions", {})
        for use_type in ["Office", "Retail", "Industrial", "Residential"]:
            use_key = use_type.lower()
            if use_key in market_assumptions:
                mkt = market_assumptions[use_key]
                market.append(
                    ARGUSMarketRecord(
                        property_id=property_id,
                        use_type=use_type,
                        market_rent_psf=float(mkt.get("rent_psf", 35.0)),
                        market_rent_growth_pct=float(mkt.get("rent_growth", 0.03)),
                        market_vacancy_pct=float(mkt.get("vacancy", 0.08)),
                        market_vacancy_trend=mkt.get("trend", "Stable"),
                        absorption_period_months=int(mkt.get("absorption_months", 12)),
                    )
                )

        # Build valuation record
        dcf = scenario_data.get("dcf_assumptions", {})
        valuation = ARGUSValuationRecord(
            property_id=property_id,
            analysis_start_date=analysis_start,
            analysis_period_months=int(dcf.get("hold_period_months", 120)),
            discount_rate_pct=float(dcf.get("discount_rate", 0.085)),
            going_in_cap_rate_pct=float(dcf.get("going_in_cap", 0.055)),
            terminal_cap_rate_pct=float(dcf.get("terminal_cap", 0.060)),
            cap_rate_spread_bps=int(dcf.get("cap_spread_bps", 50)),
            cost_of_sale_pct=float(dcf.get("cost_of_sale", 0.02)),
            inflation_rate_pct=float(dcf.get("inflation", 0.025)),
        )

        return ARGUSExportBundle(
            property=prop,
            tenants=tenants,
            revenue=[],  # Revenue projections calculated by ARGUS
            expenses=expenses,
            market=market,
            valuation=valuation,
        )


# Singleton instance
_argus_service: Optional[ARGUSExportService] = None


def get_argus_export_service() -> ARGUSExportService:
    """Get the ARGUS export service singleton."""
    global _argus_service
    if _argus_service is None:
        _argus_service = ARGUSExportService()
    return _argus_service


__all__ = [
    "ARGUSExportService",
    "ARGUSExportBundle",
    "ARGUSPropertyRecord",
    "ARGUSTenantRecord",
    "ARGUSRevenueRecord",
    "ARGUSExpenseRecord",
    "ARGUSMarketRecord",
    "ARGUSValuationRecord",
    "get_argus_export_service",
]
