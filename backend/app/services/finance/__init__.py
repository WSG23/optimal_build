"""Finance related service helpers."""

from .argus_export import (
    ARGUSExportBundle,
    ARGUSExportService,
    ARGUSExpenseRecord,
    ARGUSMarketRecord,
    ARGUSPropertyRecord,
    ARGUSRevenueRecord,
    ARGUSTenantRecord,
    ARGUSValuationRecord,
    get_argus_export_service,
)
from .asset_models import (
    AssetFinanceInput,
    build_asset_financials,
    serialise_breakdown,
    summarise_asset_financials,
)
from .calculator import dscr_timeline, escalate_amount, irr, npv, price_sensitivity_grid
from .re_metrics import (
    PropertyValuation,
    REFinancialMetrics,
    calculate_cap_rate,
    calculate_cash_on_cash_return,
    calculate_comprehensive_metrics,
    calculate_debt_yield,
    calculate_gross_rent_multiplier,
    calculate_loan_to_value,
    calculate_noi,
    calculate_operating_expense_ratio,
    calculate_property_value_from_noi,
    calculate_rental_yield,
    calculate_vacancy_loss,
    value_property_multiple_approaches,
)
from .scenario_lineage import (
    LineageAction,
    LineageDiff,
    ScenarioLineage,
    ScenarioLineageService,
    ScenarioVersion,
    get_scenario_lineage_service,
)
from .jurisdiction_financing import (
    BorrowerType,
    FinancingConstraints,
    JurisdictionCode,
    JurisdictionFinancingProfile,
    JurisdictionFinancingService,
    PropertyType,
    StampDutyRates,
    get_jurisdiction_financing_service,
    JURISDICTION_PROFILES,
)

__all__ = [
    # Asset modelling (Phase 2C)
    "AssetFinanceInput",
    "build_asset_financials",
    "serialise_breakdown",
    "summarise_asset_financials",
    # Original calculator functions
    "dscr_timeline",
    "escalate_amount",
    "irr",
    "npv",
    "price_sensitivity_grid",
    # Real estate metrics
    "calculate_noi",
    "calculate_cap_rate",
    "calculate_cash_on_cash_return",
    "calculate_gross_rent_multiplier",
    "calculate_debt_yield",
    "calculate_loan_to_value",
    "calculate_property_value_from_noi",
    "calculate_rental_yield",
    "calculate_vacancy_loss",
    "calculate_operating_expense_ratio",
    "calculate_comprehensive_metrics",
    "value_property_multiple_approaches",
    "PropertyValuation",
    "REFinancialMetrics",
    # ARGUS export
    "ARGUSExportService",
    "ARGUSExportBundle",
    "ARGUSPropertyRecord",
    "ARGUSTenantRecord",
    "ARGUSRevenueRecord",
    "ARGUSExpenseRecord",
    "ARGUSMarketRecord",
    "ARGUSValuationRecord",
    "get_argus_export_service",
    # Scenario lineage
    "ScenarioLineageService",
    "ScenarioLineage",
    "ScenarioVersion",
    "LineageAction",
    "LineageDiff",
    "get_scenario_lineage_service",
    # Multi-jurisdiction financing
    "JurisdictionCode",
    "PropertyType",
    "BorrowerType",
    "FinancingConstraints",
    "StampDutyRates",
    "JurisdictionFinancingProfile",
    "JurisdictionFinancingService",
    "get_jurisdiction_financing_service",
    "JURISDICTION_PROFILES",
]
