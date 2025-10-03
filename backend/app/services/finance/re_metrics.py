"""Real Estate specific financial metrics for the Finance Calculator."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext
from typing import Optional, Union, Dict, List

from app.services.finance.calculator import (
    NumberLike, CURRENCY_QUANTIZER, DEFAULT_PRECISION,
    _to_decimal, _quantize_currency
)

__all__ = [
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
    "PropertyValuation",
    "REFinancialMetrics"
]


@dataclass(frozen=True)
class PropertyValuation:
    """Property valuation using different methods."""
    
    income_approach_value: Decimal
    comparable_sales_value: Optional[Decimal] = None
    replacement_cost_value: Optional[Decimal] = None
    recommended_value: Decimal = Decimal("0")
    currency: str = "SGD"


@dataclass(frozen=True) 
class REFinancialMetrics:
    """Comprehensive real estate financial metrics."""
    
    noi: Decimal
    cap_rate: Optional[Decimal]
    cash_on_cash_return: Optional[Decimal]
    gross_rent_multiplier: Optional[Decimal]
    debt_yield: Optional[Decimal]
    ltv_ratio: Optional[Decimal]
    dscr: Optional[Decimal]
    rental_yield: Optional[Decimal]
    operating_expense_ratio: Optional[Decimal]
    currency: str = "SGD"


def calculate_noi(
    gross_rental_income: NumberLike,
    other_income: NumberLike = 0,
    vacancy_rate: NumberLike = 0,
    operating_expenses: NumberLike = 0,
    *,
    precision: int = DEFAULT_PRECISION
) -> Decimal:
    """
    Calculate Net Operating Income (NOI).
    
    Parameters
    ----------
    gross_rental_income:
        Total potential rental income
    other_income:
        Additional income (parking, utilities, etc.)
    vacancy_rate:
        Vacancy rate as decimal (0.05 for 5%)
    operating_expenses:
        Total operating expenses
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    Net Operating Income
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        gross_income = _to_decimal(gross_rental_income)
        other = _to_decimal(other_income)
        vacancy = _to_decimal(vacancy_rate)
        expenses = _to_decimal(operating_expenses)
        
        # Calculate effective gross income
        total_potential_income = gross_income + other
        vacancy_loss = total_potential_income * vacancy
        effective_gross_income = total_potential_income - vacancy_loss
        
        # NOI = Effective Gross Income - Operating Expenses
        noi = effective_gross_income - expenses
        
        return _quantize_currency(noi)


def calculate_cap_rate(
    noi: NumberLike,
    property_value: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate Capitalization Rate (Cap Rate).
    
    Parameters
    ----------
    noi:
        Net Operating Income
    property_value:
        Current market value or purchase price
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    Cap rate as decimal (0.05 = 5%) or None if property_value is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        net_income = _to_decimal(noi)
        value = _to_decimal(property_value)
        
        if value == 0:
            return None
            
        cap_rate = net_income / value
        
        # Return as percentage decimal (4 decimal places)
        return cap_rate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_cash_on_cash_return(
    annual_cash_flow: NumberLike,
    initial_cash_investment: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate Cash-on-Cash Return.
    
    Parameters
    ----------
    annual_cash_flow:
        Annual pre-tax cash flow (NOI - Debt Service)
    initial_cash_investment:
        Total cash invested (down payment + closing costs + initial repairs)
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    Cash-on-cash return as decimal or None if initial investment is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        cash_flow = _to_decimal(annual_cash_flow)
        investment = _to_decimal(initial_cash_investment)
        
        if investment == 0:
            return None
            
        coc_return = cash_flow / investment
        
        return coc_return.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_gross_rent_multiplier(
    property_value: NumberLike,
    annual_gross_income: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate Gross Rent Multiplier (GRM).
    
    Parameters
    ----------
    property_value:
        Current market value or purchase price
    annual_gross_income:
        Annual gross rental income (before expenses)
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    GRM ratio or None if income is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        value = _to_decimal(property_value)
        income = _to_decimal(annual_gross_income)
        
        if income == 0:
            return None
            
        grm = value / income
        
        return grm.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_debt_yield(
    noi: NumberLike,
    loan_amount: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate Debt Yield.
    
    Parameters
    ----------
    noi:
        Net Operating Income
    loan_amount:
        Total loan/mortgage amount
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    Debt yield as decimal or None if loan amount is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        net_income = _to_decimal(noi)
        loan = _to_decimal(loan_amount)
        
        if loan == 0:
            return None
            
        debt_yield = net_income / loan
        
        return debt_yield.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_loan_to_value(
    loan_amount: NumberLike,
    property_value: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate Loan-to-Value (LTV) Ratio.
    
    Parameters
    ----------
    loan_amount:
        Total loan/mortgage amount
    property_value:
        Current market value or purchase price
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    LTV ratio as decimal or None if property value is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        loan = _to_decimal(loan_amount)
        value = _to_decimal(property_value)
        
        if value == 0:
            return None
            
        ltv = loan / value
        
        return ltv.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_property_value_from_noi(
    noi: NumberLike,
    cap_rate: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate property value using income approach.
    
    Parameters
    ----------
    noi:
        Net Operating Income
    cap_rate:
        Market capitalization rate as decimal
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    Estimated property value or None if cap rate is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        net_income = _to_decimal(noi)
        rate = _to_decimal(cap_rate)
        
        if rate == 0:
            return None
            
        value = net_income / rate
        
        return _quantize_currency(value)


def calculate_rental_yield(
    annual_rental_income: NumberLike,
    property_value: NumberLike,
    *,
    gross: bool = True,
    operating_expenses: NumberLike = 0,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate rental yield (gross or net).
    
    Parameters
    ----------
    annual_rental_income:
        Annual rental income
    property_value:
        Current market value or purchase price
    gross:
        If True, calculate gross yield; if False, calculate net yield
    operating_expenses:
        Annual operating expenses (for net yield)
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    Rental yield as decimal or None if property value is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        income = _to_decimal(annual_rental_income)
        value = _to_decimal(property_value)
        
        if value == 0:
            return None
        
        if gross:
            rental_yield = income / value
        else:
            expenses = _to_decimal(operating_expenses)
            net_income = income - expenses
            rental_yield = net_income / value
        
        return rental_yield.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_vacancy_loss(
    potential_gross_income: NumberLike,
    vacancy_rate: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Decimal:
    """
    Calculate vacancy loss amount.
    
    Parameters
    ----------
    potential_gross_income:
        Total potential income if fully occupied
    vacancy_rate:
        Vacancy rate as decimal
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    Vacancy loss amount
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        income = _to_decimal(potential_gross_income)
        rate = _to_decimal(vacancy_rate)
        
        vacancy_loss = income * rate
        
        return _quantize_currency(vacancy_loss)


def calculate_operating_expense_ratio(
    operating_expenses: NumberLike,
    effective_gross_income: NumberLike,
    *,
    precision: int = DEFAULT_PRECISION
) -> Optional[Decimal]:
    """
    Calculate Operating Expense Ratio (OER).
    
    Parameters
    ----------
    operating_expenses:
        Total annual operating expenses
    effective_gross_income:
        Effective gross income (after vacancy)
    precision:
        Decimal precision for calculations
        
    Returns
    -------
    OER as decimal or None if income is zero
    """
    with localcontext() as ctx:
        ctx.prec = precision
        
        expenses = _to_decimal(operating_expenses)
        income = _to_decimal(effective_gross_income)
        
        if income == 0:
            return None
            
        oer = expenses / income
        
        return oer.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def calculate_comprehensive_metrics(
    property_value: NumberLike,
    gross_rental_income: NumberLike,
    operating_expenses: NumberLike,
    loan_amount: Optional[NumberLike] = None,
    annual_debt_service: Optional[NumberLike] = None,
    initial_cash_investment: Optional[NumberLike] = None,
    vacancy_rate: NumberLike = Decimal("0.05"),
    other_income: NumberLike = 0,
    *,
    currency: str = "SGD",
    precision: int = DEFAULT_PRECISION
) -> REFinancialMetrics:
    """
    Calculate comprehensive real estate financial metrics.
    
    Parameters
    ----------
    property_value:
        Current market value or purchase price
    gross_rental_income:
        Annual gross rental income
    operating_expenses:
        Annual operating expenses
    loan_amount:
        Total loan amount (optional)
    annual_debt_service:
        Annual debt service payment (optional)
    initial_cash_investment:
        Initial cash investment (optional)
    vacancy_rate:
        Vacancy rate as decimal
    other_income:
        Other income sources
    currency:
        Currency code
    precision:
        Decimal precision
        
    Returns
    -------
    Comprehensive financial metrics
    """
    # Calculate NOI
    noi = calculate_noi(
        gross_rental_income,
        other_income,
        vacancy_rate,
        operating_expenses,
        precision=precision
    )
    
    # Calculate cap rate
    cap_rate = calculate_cap_rate(noi, property_value, precision=precision)
    
    # Calculate rental yield
    rental_yield = calculate_rental_yield(
        gross_rental_income,
        property_value,
        gross=False,
        operating_expenses=operating_expenses,
        precision=precision
    )
    
    # Calculate debt-related metrics if loan info provided
    ltv_ratio = None
    debt_yield = None
    cash_on_cash = None
    dscr = None
    
    if loan_amount:
        ltv_ratio = calculate_loan_to_value(
            loan_amount, property_value, precision=precision
        )
        debt_yield = calculate_debt_yield(
            noi, loan_amount, precision=precision
        )
    
    if annual_debt_service:
        if _to_decimal(annual_debt_service) > 0:
            annual_cash_flow = noi - _to_decimal(annual_debt_service)
            
            if initial_cash_investment:
                cash_on_cash = calculate_cash_on_cash_return(
                    annual_cash_flow,
                    initial_cash_investment,
                    precision=precision
                )
            
            # Simple DSCR calculation
            with localcontext() as ctx:
                ctx.prec = precision
                dscr = (_to_decimal(noi) / _to_decimal(annual_debt_service)).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
    
    # Calculate other metrics
    grm = calculate_gross_rent_multiplier(
        property_value, gross_rental_income, precision=precision
    )
    
    effective_gross_income = _to_decimal(gross_rental_income) + _to_decimal(other_income) - calculate_vacancy_loss(
        _to_decimal(gross_rental_income) + _to_decimal(other_income),
        vacancy_rate,
        precision=precision
    )
    
    oer = calculate_operating_expense_ratio(
        operating_expenses, effective_gross_income, precision=precision
    )
    
    return REFinancialMetrics(
        noi=noi,
        cap_rate=cap_rate,
        cash_on_cash_return=cash_on_cash,
        gross_rent_multiplier=grm,
        debt_yield=debt_yield,
        ltv_ratio=ltv_ratio,
        dscr=dscr,
        rental_yield=rental_yield,
        operating_expense_ratio=oer,
        currency=currency
    )


def value_property_multiple_approaches(
    noi: NumberLike,
    market_cap_rate: NumberLike,
    comparable_psf: Optional[NumberLike] = None,
    property_size_sqf: Optional[NumberLike] = None,
    replacement_cost_psf: Optional[NumberLike] = None,
    land_value: Optional[NumberLike] = None,
    depreciation_factor: NumberLike = Decimal("0.8"),
    *,
    currency: str = "SGD",
    precision: int = DEFAULT_PRECISION
) -> PropertyValuation:
    """
    Value property using multiple approaches.
    
    Parameters
    ----------
    noi:
        Net Operating Income
    market_cap_rate:
        Market capitalization rate
    comparable_psf:
        Comparable sales price per square foot
    property_size_sqf:
        Property size in square feet
    replacement_cost_psf:
        Replacement cost per square foot
    land_value:
        Land value for cost approach
    depreciation_factor:
        Depreciation factor for cost approach (0.8 = 20% depreciation)
    currency:
        Currency code
    precision:
        Decimal precision
        
    Returns
    -------
    Property valuation using different methods
    """
    # Income approach
    income_value = calculate_property_value_from_noi(
        noi, market_cap_rate, precision=precision
    )
    
    # Sales comparison approach
    comparable_value = None
    if comparable_psf and property_size_sqf:
        with localcontext() as ctx:
            ctx.prec = precision
            psf = _to_decimal(comparable_psf)
            size = _to_decimal(property_size_sqf)
            comparable_value = _quantize_currency(psf * size)
    
    # Cost approach
    replacement_value = None
    if replacement_cost_psf and property_size_sqf:
        with localcontext() as ctx:
            ctx.prec = precision
            cost_psf = _to_decimal(replacement_cost_psf)
            size = _to_decimal(property_size_sqf)
            depreciation = _to_decimal(depreciation_factor)
            
            building_value = cost_psf * size * depreciation
            
            if land_value:
                land = _to_decimal(land_value)
                replacement_value = _quantize_currency(building_value + land)
            else:
                replacement_value = _quantize_currency(building_value)
    
    # Determine recommended value (weighted average or selection logic)
    values = []
    if income_value:
        values.append(income_value)
    if comparable_value:
        values.append(comparable_value)
    if replacement_value:
        values.append(replacement_value)
    
    if values:
        # Simple average for now - could implement weighted average
        with localcontext() as ctx:
            ctx.prec = precision
            recommended = sum(values) / len(values)
            recommended_value = _quantize_currency(recommended)
    else:
        recommended_value = Decimal("0")
    
    return PropertyValuation(
        income_approach_value=income_value or Decimal("0"),
        comparable_sales_value=comparable_value,
        replacement_cost_value=replacement_value,
        recommended_value=recommended_value,
        currency=currency
    )