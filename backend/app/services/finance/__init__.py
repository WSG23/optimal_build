"""Finance related service helpers."""

from .calculator import dscr_timeline, escalate_amount, irr, npv, price_sensitivity_grid
from .re_metrics import (
    calculate_noi,
    calculate_cap_rate,
    calculate_cash_on_cash_return,
    calculate_gross_rent_multiplier,
    calculate_debt_yield,
    calculate_loan_to_value,
    calculate_property_value_from_noi,
    calculate_rental_yield,
    calculate_vacancy_loss,
    calculate_operating_expense_ratio,
    calculate_comprehensive_metrics,
    value_property_multiple_approaches,
    PropertyValuation,
    REFinancialMetrics,
)

__all__ = [
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
]
