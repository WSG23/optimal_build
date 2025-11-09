"""Tests for Real Estate financial metrics."""

from __future__ import annotations

from decimal import Decimal

from app.services.finance.re_metrics import (
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


class TestCalculateNOI:
    """Test Net Operating Income calculations."""

    def test_basic_noi(self) -> None:
        """Test basic NOI calculation."""
        result = calculate_noi(
            gross_rental_income=100000,
            operating_expenses=30000,
        )
        assert result == Decimal("70000.00")

    def test_noi_with_other_income(self) -> None:
        """Test NOI with additional income."""
        result = calculate_noi(
            gross_rental_income=100000,
            other_income=10000,
            operating_expenses=30000,
        )
        assert result == Decimal("80000.00")

    def test_noi_with_vacancy(self) -> None:
        """Test NOI with vacancy rate."""
        result = calculate_noi(
            gross_rental_income=100000,
            vacancy_rate=0.05,  # 5% vacancy
            operating_expenses=30000,
        )
        # 100000 * 0.95 - 30000 = 65000
        assert result == Decimal("65000.00")

    def test_noi_comprehensive(self) -> None:
        """Test NOI with all parameters."""
        result = calculate_noi(
            gross_rental_income=100000,
            other_income=5000,
            vacancy_rate=0.10,  # 10% vacancy
            operating_expenses=25000,
        )
        # (100000 + 5000) * 0.90 - 25000 = 94500 - 25000 = 69500
        assert result == Decimal("69500.00")

    def test_noi_with_decimals(self) -> None:
        """Test NOI with Decimal inputs."""
        result = calculate_noi(
            gross_rental_income=Decimal("100000.50"),
            other_income=Decimal("5000.25"),
            vacancy_rate=Decimal("0.05"),
            operating_expenses=Decimal("30000.00"),
        )
        expected = Decimal("100000.50") + Decimal("5000.25")
        expected = expected * Decimal("0.95") - Decimal("30000.00")
        assert result == expected.quantize(Decimal("0.01"))


class TestCalculateCapRate:
    """Test Capitalization Rate calculations."""

    def test_basic_cap_rate(self) -> None:
        """Test basic cap rate calculation."""
        result = calculate_cap_rate(noi=70000, property_value=1000000)
        # 70000 / 1000000 = 0.07 = 7%
        assert result == Decimal("0.07")

    def test_cap_rate_different_values(self) -> None:
        """Test cap rate with different values."""
        result = calculate_cap_rate(noi=50000, property_value=500000)
        assert result == Decimal("0.10")  # 10%

    def test_cap_rate_zero_property_value(self) -> None:
        """Test cap rate with zero property value returns None."""
        result = calculate_cap_rate(noi=70000, property_value=0)
        assert result is None

    def test_cap_rate_decimal_inputs(self) -> None:
        """Test cap rate with Decimal inputs."""
        result = calculate_cap_rate(
            noi=Decimal("75000"), property_value=Decimal("1200000")
        )
        assert result == Decimal("0.0625")  # 6.25%


class TestCalculateCashOnCashReturn:
    """Test Cash-on-Cash Return calculations."""

    def test_basic_cash_on_cash(self) -> None:
        """Test basic cash-on-cash return."""
        result = calculate_cash_on_cash_return(
            annual_cash_flow=20000, initial_cash_investment=200000
        )
        # 20000 / 200000 = 0.10 = 10%
        assert result == Decimal("0.10")

    def test_cash_on_cash_different_values(self) -> None:
        """Test cash-on-cash with different values."""
        result = calculate_cash_on_cash_return(
            annual_cash_flow=15000, initial_cash_investment=150000
        )
        assert result == Decimal("0.10")  # 10%

    def test_cash_on_cash_zero_investment(self) -> None:
        """Test cash-on-cash with zero investment returns None."""
        result = calculate_cash_on_cash_return(
            annual_cash_flow=20000, initial_cash_investment=0
        )
        assert result is None

    def test_cash_on_cash_negative_cash_flow(self) -> None:
        """Test cash-on-cash with negative cash flow."""
        result = calculate_cash_on_cash_return(
            annual_cash_flow=-5000, initial_cash_investment=100000
        )
        assert result == Decimal("-0.05")  # -5%


class TestCalculateGrossRentMultiplier:
    """Test Gross Rent Multiplier calculations."""

    def test_basic_grm(self) -> None:
        """Test basic GRM calculation."""
        result = calculate_gross_rent_multiplier(
            property_value=500000, annual_gross_income=50000
        )
        # 500000 / 50000 = 10
        assert result == Decimal("10.00")

    def test_grm_zero_income(self) -> None:
        """Test GRM with zero income returns None."""
        result = calculate_gross_rent_multiplier(
            property_value=500000, annual_gross_income=0
        )
        assert result is None

    def test_grm_different_values(self) -> None:
        """Test GRM with different values."""
        result = calculate_gross_rent_multiplier(
            property_value=1000000, annual_gross_income=80000
        )
        assert result == Decimal("12.50")


class TestCalculateDebtYield:
    """Test Debt Yield calculations."""

    def test_basic_debt_yield(self) -> None:
        """Test basic debt yield calculation."""
        result = calculate_debt_yield(noi=70000, loan_amount=700000)
        # 70000 / 700000 = 0.10 = 10%
        assert result == Decimal("0.10")

    def test_debt_yield_zero_loan(self) -> None:
        """Test debt yield with zero loan returns None."""
        result = calculate_debt_yield(noi=70000, loan_amount=0)
        assert result is None

    def test_debt_yield_different_values(self) -> None:
        """Test debt yield with different values."""
        result = calculate_debt_yield(noi=50000, loan_amount=500000)
        assert result == Decimal("0.10")  # 10%


class TestCalculateLoanToValue:
    """Test Loan-to-Value ratio calculations."""

    def test_basic_ltv(self) -> None:
        """Test basic LTV calculation."""
        result = calculate_loan_to_value(loan_amount=700000, property_value=1000000)
        # 700000 / 1000000 = 0.70 = 70%
        assert result == Decimal("0.70")

    def test_ltv_zero_property_value(self) -> None:
        """Test LTV with zero property value returns None."""
        result = calculate_loan_to_value(loan_amount=700000, property_value=0)
        assert result is None

    def test_ltv_different_values(self) -> None:
        """Test LTV with different values."""
        result = calculate_loan_to_value(loan_amount=400000, property_value=500000)
        assert result == Decimal("0.80")  # 80%


class TestCalculatePropertyValueFromNOI:
    """Test property valuation from NOI."""

    def test_basic_property_value(self) -> None:
        """Test basic property value calculation."""
        result = calculate_property_value_from_noi(noi=70000, cap_rate=0.07)
        # 70000 / 0.07 = 1000000
        assert result == Decimal("1000000.00")

    def test_property_value_zero_cap_rate(self) -> None:
        """Test property value with zero cap rate returns None."""
        result = calculate_property_value_from_noi(noi=70000, cap_rate=0)
        assert result is None

    def test_property_value_different_values(self) -> None:
        """Test property value with different values."""
        result = calculate_property_value_from_noi(noi=80000, cap_rate=0.08)
        assert result == Decimal("1000000.00")


class TestCalculateRentalYield:
    """Test Rental Yield calculations."""

    def test_basic_rental_yield(self) -> None:
        """Test basic rental yield calculation."""
        result = calculate_rental_yield(
            annual_rental_income=50000, property_value=1000000
        )
        # 50000 / 1000000 = 0.05 = 5%
        assert result == Decimal("0.05")

    def test_rental_yield_zero_property_value(self) -> None:
        """Test rental yield with zero property value returns None."""
        result = calculate_rental_yield(annual_rental_income=50000, property_value=0)
        assert result is None

    def test_rental_yield_different_values(self) -> None:
        """Test rental yield with different values."""
        result = calculate_rental_yield(
            annual_rental_income=60000, property_value=800000
        )
        assert result == Decimal("0.075")  # 7.5%


class TestCalculateVacancyLoss:
    """Test Vacancy Loss calculations."""

    def test_basic_vacancy_loss(self) -> None:
        """Test basic vacancy loss calculation."""
        result = calculate_vacancy_loss(
            potential_gross_income=100000, vacancy_rate=0.05
        )
        # 100000 * 0.05 = 5000
        assert result == Decimal("5000.00")

    def test_vacancy_loss_zero_rate(self) -> None:
        """Test vacancy loss with zero rate."""
        result = calculate_vacancy_loss(potential_gross_income=100000, vacancy_rate=0)
        assert result == Decimal("0.00")

    def test_vacancy_loss_different_values(self) -> None:
        """Test vacancy loss with different values."""
        result = calculate_vacancy_loss(potential_gross_income=80000, vacancy_rate=0.10)
        assert result == Decimal("8000.00")  # 10%


class TestCalculateOperatingExpenseRatio:
    """Test Operating Expense Ratio calculations."""

    def test_basic_oer(self) -> None:
        """Test basic OER calculation."""
        result = calculate_operating_expense_ratio(
            operating_expenses=30000, effective_gross_income=100000
        )
        # 30000 / 100000 = 0.30 = 30%
        assert result == Decimal("0.30")

    def test_oer_zero_income(self) -> None:
        """Test OER with zero income returns None."""
        result = calculate_operating_expense_ratio(
            operating_expenses=30000, effective_gross_income=0
        )
        assert result is None

    def test_oer_different_values(self) -> None:
        """Test OER with different values."""
        result = calculate_operating_expense_ratio(
            operating_expenses=40000, effective_gross_income=80000
        )
        assert result == Decimal("0.50")  # 50%


class TestPropertyValuation:
    """Test PropertyValuation dataclass."""

    def test_property_valuation_basic(self) -> None:
        """Test basic PropertyValuation creation."""
        valuation = PropertyValuation(income_approach_value=Decimal("1000000"))
        assert valuation.income_approach_value == Decimal("1000000")
        assert valuation.comparable_sales_value is None
        assert valuation.replacement_cost_value is None
        assert valuation.currency == "SGD"

    def test_property_valuation_all_fields(self) -> None:
        """Test PropertyValuation with all fields."""
        valuation = PropertyValuation(
            income_approach_value=Decimal("1000000"),
            comparable_sales_value=Decimal("950000"),
            replacement_cost_value=Decimal("1100000"),
            recommended_value=Decimal("1000000"),
            currency="USD",
        )
        assert valuation.income_approach_value == Decimal("1000000")
        assert valuation.comparable_sales_value == Decimal("950000")
        assert valuation.replacement_cost_value == Decimal("1100000")
        assert valuation.recommended_value == Decimal("1000000")
        assert valuation.currency == "USD"


class TestREFinancialMetrics:
    """Test REFinancialMetrics dataclass."""

    def test_re_financial_metrics_basic(self) -> None:
        """Test basic REFinancialMetrics creation."""
        metrics = REFinancialMetrics(
            noi=Decimal("70000"),
            cap_rate=Decimal("0.07"),
            cash_on_cash_return=None,
            gross_rent_multiplier=None,
            debt_yield=None,
            ltv_ratio=None,
            dscr=None,
            rental_yield=None,
            operating_expense_ratio=None,
        )
        assert metrics.noi == Decimal("70000")
        assert metrics.cap_rate == Decimal("0.07")
        assert metrics.currency == "SGD"

    def test_re_financial_metrics_all_fields(self) -> None:
        """Test REFinancialMetrics with all fields."""
        metrics = REFinancialMetrics(
            noi=Decimal("70000"),
            cap_rate=Decimal("0.07"),
            cash_on_cash_return=Decimal("0.10"),
            gross_rent_multiplier=Decimal("12.5"),
            debt_yield=Decimal("0.10"),
            ltv_ratio=Decimal("0.70"),
            dscr=Decimal("1.25"),
            rental_yield=Decimal("0.05"),
            operating_expense_ratio=Decimal("0.30"),
            currency="USD",
        )
        assert metrics.noi == Decimal("70000")
        assert metrics.cap_rate == Decimal("0.07")
        assert metrics.cash_on_cash_return == Decimal("0.10")
        assert metrics.gross_rent_multiplier == Decimal("12.5")
        assert metrics.debt_yield == Decimal("0.10")
        assert metrics.ltv_ratio == Decimal("0.70")
        assert metrics.dscr == Decimal("1.25")
        assert metrics.rental_yield == Decimal("0.05")
        assert metrics.operating_expense_ratio == Decimal("0.30")
        assert metrics.currency == "USD"


class TestCalculateComprehensiveMetrics:
    """Test comprehensive metrics calculation."""

    def test_comprehensive_metrics_minimal(self) -> None:
        """Test comprehensive metrics with minimal inputs."""
        metrics = calculate_comprehensive_metrics(
            gross_rental_income=100000,
            operating_expenses=30000,
            property_value=1000000,
            vacancy_rate=0,
        )
        assert metrics.noi == Decimal("70000.00")
        assert metrics.cap_rate == Decimal("0.07")
        assert metrics.rental_yield == Decimal("0.07")  # NOI / property_value
        assert metrics.operating_expense_ratio == Decimal("0.30")  # 30000/100000

    def test_comprehensive_metrics_with_financing(self) -> None:
        """Test comprehensive metrics with financing."""
        metrics = calculate_comprehensive_metrics(
            gross_rental_income=100000,
            operating_expenses=30000,
            property_value=1000000,
            loan_amount=700000,
            annual_debt_service=50000,
            vacancy_rate=0,
        )
        assert metrics.noi == Decimal("70000.00")
        assert metrics.ltv_ratio == Decimal("0.70")
        assert metrics.debt_yield == Decimal("0.10")
        assert metrics.dscr == Decimal("1.40")  # 70000 / 50000


class TestValuePropertyMultipleApproaches:
    """Test property valuation using multiple approaches."""

    def test_value_property_income_approach(self) -> None:
        """Test property valuation with income approach."""
        valuation = value_property_multiple_approaches(noi=70000, market_cap_rate=0.07)
        assert valuation.income_approach_value == Decimal("1000000.00")
        assert valuation.comparable_sales_value is None
        assert valuation.replacement_cost_value is None

    def test_value_property_all_approaches(self) -> None:
        """Test property valuation with all approaches."""
        valuation = value_property_multiple_approaches(
            noi=70000,
            market_cap_rate=0.07,
            comparable_psf=950,
            property_size_sqf=1000,
            replacement_cost_psf=1000,
            land_value=100000,
        )
        assert valuation.income_approach_value == Decimal("1000000.00")
        assert valuation.comparable_sales_value == Decimal("950000.00")
        assert valuation.replacement_cost_value == Decimal(
            "900000.00"
        )  # 1000*1000*0.8 + 100000
        # Recommended value should be weighted average or similar
        assert valuation.recommended_value > Decimal("0")
