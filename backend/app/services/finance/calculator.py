"""Deterministic financial calculators built on :class:`~decimal.Decimal`."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from types import MappingProxyType
from typing import Any, Union

from app.models.rkp import RefCostIndex
from backend._compat import compat_zip

NumberLike = Union[Decimal, int, float, str]
CURRENCY_QUANTIZER = Decimal("0.01")
DSCR_QUANTIZER = Decimal("0.0001")
RATIO_QUANTIZER = Decimal("0.0001")
DEFAULT_PRECISION = 28


@dataclass(frozen=True)
class DscrEntry:
    """Single period DSCR breakdown."""

    period: int | str
    noi: Decimal
    debt_service: Decimal
    dscr: Decimal | None
    currency: str


@dataclass(frozen=True)
class PriceSensitivityResult:
    """Immutable representation of a 2D price sensitivity analysis."""

    currency: str
    price_deltas: tuple[Decimal, ...]
    volume_deltas: tuple[Decimal, ...]
    prices: tuple[Decimal, ...]
    grid: tuple[tuple[Decimal, ...], ...]


@dataclass(frozen=True)
class CapitalStackComponent:
    """Single capital stack slice with computed share metadata."""

    name: str
    source_type: str
    category: str
    amount: Decimal
    share: Decimal
    rate: Decimal | None
    tranche_order: int | None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class CapitalStackSummary:
    """Aggregated view of the submitted capital stack."""

    currency: str
    total: Decimal
    equity_total: Decimal
    debt_total: Decimal
    other_total: Decimal
    equity_ratio: Decimal | None
    debt_ratio: Decimal | None
    other_ratio: Decimal | None
    loan_to_cost: Decimal | None
    weighted_average_debt_rate: Decimal | None
    slices: tuple[CapitalStackComponent, ...]


@dataclass(frozen=True)
class FinancingDrawdownEntry:
    """Drawdown amounts and cumulative financing exposure for a period."""

    period: str
    equity_draw: Decimal
    debt_draw: Decimal
    total_draw: Decimal
    cumulative_equity: Decimal
    cumulative_debt: Decimal
    outstanding_debt: Decimal


@dataclass(frozen=True)
class FinancingDrawdownSchedule:
    """Complete financing drawdown schedule with summary metrics."""

    currency: str
    entries: tuple[FinancingDrawdownEntry, ...]
    total_equity: Decimal
    total_debt: Decimal
    peak_debt_balance: Decimal
    final_debt_balance: Decimal


def _to_decimal(value: NumberLike) -> Decimal:
    """Convert *value* into a :class:`Decimal` using string casting for stability."""

    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        return Decimal(value)
    return Decimal(str(value))


def _quantize_currency(value: Decimal) -> Decimal:
    """Quantise a monetary value to cents using half-up rounding."""

    return value.quantize(CURRENCY_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_ratio(value: Decimal) -> Decimal:
    """Quantise a ratio to four decimal places using half-up rounding."""

    return value.quantize(RATIO_QUANTIZER, rounding=ROUND_HALF_UP)


def _normalise_cash_flows(cash_flows: Sequence[NumberLike]) -> tuple[Decimal, ...]:
    """Normalise an iterable of cash flows into a tuple of :class:`Decimal`."""

    return tuple(_to_decimal(cash) for cash in cash_flows)


def npv(
    rate: NumberLike,
    cash_flows: Sequence[NumberLike],
    *,
    precision: int = DEFAULT_PRECISION,
) -> Decimal:
    """Compute the net present value of ``cash_flows`` discounted by ``rate``.

    Parameters
    ----------
    rate:
        Periodic discount rate expressed as a decimal fraction (``0.05`` for 5%).
    cash_flows:
        Ordered sequence of cash flows where index ``0`` represents the present period.
    precision:
        Decimal precision to use for the calculation.
    """

    cash_values = _normalise_cash_flows(cash_flows)
    discount_rate = _to_decimal(rate)
    one = Decimal("1")
    npv_total = Decimal("0")
    with localcontext() as ctx:
        ctx.prec = precision
        for period, cash in enumerate(cash_values):
            discount_factor = (one + discount_rate) ** period
            if discount_factor == 0:
                raise ZeroDivisionError(
                    "Discount factor evaluated to zero; rate cannot be -1 for positive periods."
                )
            npv_total += cash / discount_factor
    return npv_total


def _npv_derivative(
    rate: Decimal, cash_flows: Sequence[Decimal], precision: int
) -> Decimal:
    """Derivative of NPV with respect to ``rate`` for Newton iterations."""

    one = Decimal("1")
    derivative = Decimal("0")
    with localcontext() as ctx:
        ctx.prec = precision
        for period, cash in enumerate(cash_flows):
            if period == 0:
                continue
            denominator = (one + rate) ** (period + 1)
            if denominator == 0:
                raise ZeroDivisionError(
                    "Encountered zero denominator while differentiating NPV."
                )
            derivative -= (period * cash) / denominator
    return derivative


def _has_sign_change(values: Sequence[Decimal]) -> bool:
    """Return ``True`` if ``values`` contain both positive and negative amounts."""

    has_positive = any(value > 0 for value in values)
    has_negative = any(value < 0 for value in values)
    return has_positive and has_negative


def _freeze_metadata(metadata: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return an immutable mapping for metadata payloads."""

    if metadata is None:
        return MappingProxyType({})
    if isinstance(metadata, Mapping):
        return MappingProxyType({**metadata})
    return MappingProxyType({})


def _classify_capital_source(source_type: str) -> str:
    """Categorise a capital stack source as equity, debt or other."""

    label = (source_type or "").strip().lower()
    if not label:
        return "other"
    if "equity" in label:
        return "equity"
    if any(term in label for term in ("debt", "loan", "credit", "mezz")):
        return "debt"
    return "other"


def irr(
    cash_flows: Sequence[NumberLike],
    *,
    guess: NumberLike = Decimal("0.1"),
    precision: int = DEFAULT_PRECISION,
    tolerance: NumberLike = Decimal("1e-7"),
    max_iterations: int = 64,
    lower_bound: NumberLike = Decimal("-0.999999"),
    upper_bound: NumberLike = Decimal("10"),
) -> Decimal:
    """Compute the internal rate of return using Newton's method with a fallback."""

    flows = _normalise_cash_flows(cash_flows)
    if not flows:
        raise ValueError("IRR requires at least one cash flow.")
    if not _has_sign_change(flows):
        raise ValueError("IRR requires cash flows with at least one sign change.")

    with localcontext() as ctx:
        ctx.prec = precision
        rate = _to_decimal(guess)
        tolerance_value = _to_decimal(tolerance)
        lower = _to_decimal(lower_bound)
        upper = _to_decimal(upper_bound)

        for _ in range(max_iterations):
            value = npv(rate, flows, precision=ctx.prec)
            if abs(value) <= tolerance_value:
                return rate
            derivative = _npv_derivative(rate, flows, ctx.prec)
            if derivative == 0:
                break
            step = value / derivative
            rate -= step
            if abs(step) <= tolerance_value:
                return rate
            if rate <= lower or rate >= upper:
                break

        # Fallback to a bisection search within the provided bounds.
        lower_value = npv(lower, flows, precision=ctx.prec)
        upper_value = npv(upper, flows, precision=ctx.prec)

        if lower_value == 0:
            return lower
        if upper_value == 0:
            return upper
        if lower_value * upper_value > 0:
            raise ValueError("Failed to bracket a root for the IRR calculation.")

        for _ in range(max_iterations):
            midpoint = (lower + upper) / 2
            midpoint_value = npv(midpoint, flows, precision=ctx.prec)
            if abs(midpoint_value) <= tolerance_value:
                return midpoint
            if lower_value * midpoint_value < 0:
                upper = midpoint
                upper_value = midpoint_value
            else:
                lower = midpoint
                lower_value = midpoint_value
        return midpoint


def dscr_timeline(
    net_operating_incomes: Sequence[NumberLike],
    debt_services: Sequence[NumberLike],
    *,
    period_labels: Sequence[int | str] | None = None,
    currency: str = "SGD",
    precision: int = DEFAULT_PRECISION,
) -> list[DscrEntry]:
    """Generate a DSCR timeline ensuring monetary values are rounded to cents."""

    incomes = _normalise_cash_flows(net_operating_incomes)
    services = _normalise_cash_flows(debt_services)
    if len(incomes) != len(services):
        raise ValueError(
            "net_operating_incomes and debt_services must be of equal length."
        )
    if period_labels and len(period_labels) != len(incomes):
        raise ValueError("period_labels must match the length of the cash flow series.")

    entries: list[DscrEntry] = []
    with localcontext() as ctx:
        ctx.prec = precision
        for idx, (noi, debt) in enumerate(compat_zip(incomes, services, strict=False)):
            period = period_labels[idx] if period_labels else idx
            quantized_noi = _quantize_currency(noi)
            quantized_debt = _quantize_currency(debt)
            if debt == 0:
                dscr_value: Decimal | None
                if noi > 0:
                    dscr_value = Decimal("Infinity")
                elif noi < 0:
                    dscr_value = Decimal("-Infinity")
                else:
                    dscr_value = None
            else:
                dscr_value = (noi / debt).quantize(
                    DSCR_QUANTIZER, rounding=ROUND_HALF_UP
                )
            entries.append(
                DscrEntry(
                    period=period,
                    noi=quantized_noi,
                    debt_service=quantized_debt,
                    dscr=dscr_value,
                    currency=currency,
                )
            )
    return entries


def price_sensitivity_grid(
    base_price: NumberLike,
    base_volume: NumberLike,
    price_deltas: Sequence[NumberLike],
    volume_deltas: Sequence[NumberLike],
    *,
    currency: str = "SGD",
    precision: int = DEFAULT_PRECISION,
) -> PriceSensitivityResult:
    """Build a price sensitivity revenue grid quantised to cents."""

    price_adjustments = tuple(_to_decimal(delta) for delta in price_deltas)
    volume_adjustments = tuple(_to_decimal(delta) for delta in volume_deltas)
    price = _to_decimal(base_price)
    volume = _to_decimal(base_volume)

    price_points: list[Decimal] = []
    grid_rows: list[tuple[Decimal, ...]] = []

    with localcontext() as ctx:
        ctx.prec = precision
        for price_delta in price_adjustments:
            adjusted_price = _quantize_currency(price * (Decimal("1") + price_delta))
            price_points.append(adjusted_price)
            row: list[Decimal] = []
            for volume_delta in volume_adjustments:
                adjusted_volume = volume * (Decimal("1") + volume_delta)
                revenue = _quantize_currency(adjusted_price * adjusted_volume)
                row.append(revenue)
            grid_rows.append(tuple(row))

    return PriceSensitivityResult(
        currency=currency,
        price_deltas=price_adjustments,
        volume_deltas=volume_adjustments,
        prices=tuple(price_points),
        grid=tuple(grid_rows),
    )


def capital_stack_summary(
    slices: Sequence[Mapping[str, Any]],
    *,
    currency: str = "SGD",
    total_development_cost: NumberLike | None = None,
    precision: int = DEFAULT_PRECISION,
) -> CapitalStackSummary:
    """Compute totals, ratios and weighted averages for capital stack inputs."""

    raw_items: list[dict[str, Any]] = []
    total_amount = Decimal("0")

    with localcontext() as ctx:
        ctx.prec = precision
        for index, payload in enumerate(slices):
            if not isinstance(payload, Mapping):
                raise TypeError("capital stack entries must be mappings")

            name = str(payload.get("name", f"Tranche {index + 1}"))
            source_type = str(payload.get("source_type", "other"))
            amount = _quantize_currency(_to_decimal(payload.get("amount", 0)))
            rate_value = payload.get("rate")
            rate = None if rate_value is None else _to_decimal(rate_value)
            tranche_order = payload.get("tranche_order")
            try:
                order_value = int(tranche_order) if tranche_order is not None else None
            except (TypeError, ValueError):
                order_value = None
            metadata = payload.get("metadata")
            category = _classify_capital_source(source_type)

            raw_items.append(
                {
                    "name": name,
                    "source_type": source_type,
                    "category": category,
                    "amount": amount,
                    "rate": rate,
                    "tranche_order": order_value,
                    "metadata": _freeze_metadata(metadata),
                }
            )
            total_amount += amount

    components: list[CapitalStackComponent] = []
    running_share = Decimal("0")
    for idx, item in enumerate(raw_items):
        share = Decimal("0")
        if total_amount > 0:
            if idx == len(raw_items) - 1:
                share = _quantize_ratio(max(Decimal("0"), Decimal("1") - running_share))
            else:
                share = _quantize_ratio(item["amount"] / total_amount)
                running_share += share

        components.append(
            CapitalStackComponent(
                name=item["name"],
                source_type=item["source_type"],
                category=item["category"],
                amount=item["amount"],
                share=share,
                rate=item["rate"],
                tranche_order=item["tranche_order"],
                metadata=item["metadata"],
            )
        )

    if components and total_amount > 0:
        share_total = sum(component.share for component in components)
        if share_total != Decimal("1"):
            delta = _quantize_ratio(Decimal("1") - share_total)
            final_component = components[-1]
            components[-1] = CapitalStackComponent(
                name=final_component.name,
                source_type=final_component.source_type,
                category=final_component.category,
                amount=final_component.amount,
                share=_quantize_ratio(final_component.share + delta),
                rate=final_component.rate,
                tranche_order=final_component.tranche_order,
                metadata=final_component.metadata,
            )

    equity_total = sum(
        component.amount for component in components if component.category == "equity"
    )
    debt_total = sum(
        component.amount for component in components if component.category == "debt"
    )
    other_total = sum(
        component.amount for component in components if component.category == "other"
    )
    debt_like_total = debt_total + other_total

    equity_ratio: Decimal | None = None
    debt_ratio: Decimal | None = None
    other_ratio: Decimal | None = None
    if total_amount > 0:
        equity_ratio = _quantize_ratio(equity_total / total_amount)
        debt_ratio = _quantize_ratio(debt_total / total_amount)
        other_ratio = _quantize_ratio(other_total / total_amount)

    loan_to_cost: Decimal | None = None
    if total_development_cost is not None:
        cost_value = _to_decimal(total_development_cost)
        if cost_value != 0:
            loan_to_cost = _quantize_ratio(debt_like_total / cost_value)

    weighted_debt_rate: Decimal | None = None
    if debt_total > 0:
        numerator = Decimal("0")
        for component in components:
            if component.category != "debt" or component.rate is None:
                continue
            numerator += component.amount * component.rate
        if numerator != 0:
            weighted_debt_rate = _quantize_ratio(numerator / debt_total)

    return CapitalStackSummary(
        currency=currency,
        total=total_amount,
        equity_total=equity_total,
        debt_total=debt_total,
        other_total=other_total,
        equity_ratio=equity_ratio,
        debt_ratio=debt_ratio,
        other_ratio=other_ratio,
        loan_to_cost=loan_to_cost,
        weighted_average_debt_rate=weighted_debt_rate,
        slices=tuple(components),
    )


def drawdown_schedule(
    entries: Sequence[Mapping[str, Any]],
    *,
    currency: str = "SGD",
    precision: int = DEFAULT_PRECISION,
) -> FinancingDrawdownSchedule:
    """Compute drawdown timeline metrics for equity and debt funding."""

    schedule_entries: list[FinancingDrawdownEntry] = []
    cumulative_equity = Decimal("0")
    cumulative_debt = Decimal("0")
    outstanding_debt = Decimal("0")
    peak_debt_balance = Decimal("0")

    with localcontext() as ctx:
        ctx.prec = precision
        for index, payload in enumerate(entries):
            if not isinstance(payload, Mapping):
                raise TypeError("drawdown schedule entries must be mappings")

            period = str(payload.get("period", index))
            equity_draw = _quantize_currency(_to_decimal(payload.get("equity_draw", 0)))
            debt_draw = _quantize_currency(_to_decimal(payload.get("debt_draw", 0)))
            total_draw = _quantize_currency(equity_draw + debt_draw)

            cumulative_equity = _quantize_currency(cumulative_equity + equity_draw)
            cumulative_debt = _quantize_currency(cumulative_debt + debt_draw)
            outstanding_debt = _quantize_currency(outstanding_debt + debt_draw)
            peak_debt_balance = max(peak_debt_balance, outstanding_debt)

            schedule_entries.append(
                FinancingDrawdownEntry(
                    period=period,
                    equity_draw=equity_draw,
                    debt_draw=debt_draw,
                    total_draw=total_draw,
                    cumulative_equity=cumulative_equity,
                    cumulative_debt=cumulative_debt,
                    outstanding_debt=outstanding_debt,
                )
            )

    final_debt_balance = outstanding_debt

    return FinancingDrawdownSchedule(
        currency=currency,
        entries=tuple(schedule_entries),
        total_equity=cumulative_equity,
        total_debt=cumulative_debt,
        peak_debt_balance=peak_debt_balance,
        final_debt_balance=final_debt_balance,
    )


def escalate_amount(
    amount: NumberLike,
    *,
    base_period: str,
    indices: Iterable[RefCostIndex],
    series_name: str | None = None,
    jurisdiction: str | None = None,
    provider: str | None = None,
    precision: int = DEFAULT_PRECISION,
) -> Decimal:
    """Escalate ``amount`` by comparing base and latest cost indices."""

    base_value = _to_decimal(amount)
    indices_list = list(indices)
    latest = RefCostIndex.latest(
        indices_list,
        jurisdiction=jurisdiction,
        provider=provider,
        series_name=series_name,
    )
    if latest is None:
        return _quantize_currency(base_value)

    base_index = None
    for index in indices_list:
        if base_period and index.period == base_period:
            if series_name and index.series_name != series_name:
                continue
            if jurisdiction and index.jurisdiction != jurisdiction:
                continue
            if provider and index.provider != provider:
                continue
            base_index = index
            break

    if base_index is None:
        return _quantize_currency(base_value)

    try:
        with localcontext() as ctx:
            ctx.prec = precision
            latest_value = _to_decimal(latest.value)
            base_value_index = _to_decimal(base_index.value)
            if base_value_index == 0:
                raise ZeroDivisionError(
                    "Base index value cannot be zero for escalation."
                )
            scalar = latest_value / base_value_index
            return _quantize_currency(base_value * scalar)
    except (InvalidOperation, ZeroDivisionError):
        return _quantize_currency(base_value)


class FinanceCalculator:
    """Object oriented façade over the module-level finance helpers."""

    def npv(
        self,
        rate: NumberLike,
        cash_flows: Sequence[NumberLike],
        *,
        precision: int = DEFAULT_PRECISION,
    ) -> Decimal:
        return npv(rate, cash_flows, precision=precision)

    def irr(
        self,
        cash_flows: Sequence[NumberLike],
        *,
        guess: NumberLike = Decimal("0.1"),
        precision: int = DEFAULT_PRECISION,
        tolerance: NumberLike = Decimal("1e-7"),
        max_iterations: int = 64,
        lower_bound: NumberLike = Decimal("-0.999999"),
        upper_bound: NumberLike = Decimal("10"),
    ) -> Decimal:
        return irr(
            cash_flows,
            guess=guess,
            precision=precision,
            tolerance=tolerance,
            max_iterations=max_iterations,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

    def dscr_timeline(
        self,
        net_operating_incomes: Sequence[NumberLike],
        debt_services: Sequence[NumberLike],
        *,
        period_labels: Sequence[NumberLike] | None = None,
        currency: str = "SGD",
    ) -> tuple[DscrEntry, ...]:
        return dscr_timeline(
            net_operating_incomes,
            debt_services,
            period_labels=period_labels,
            currency=currency,
        )

    def escalate_amount(
        self,
        amount: NumberLike,
        *,
        base_period: str,
        indices: Sequence[RefCostIndex],
        series_name: str | None = None,
        jurisdiction: str | None = None,
        provider: str | None = None,
    ) -> Decimal:
        return escalate_amount(
            amount,
            base_period=base_period,
            indices=indices,
            series_name=series_name,
            jurisdiction=jurisdiction,
            provider=provider,
        )

    def price_sensitivity_grid(
        self,
        base_price: NumberLike,
        base_volume: NumberLike,
        price_deltas: Sequence[NumberLike],
        volume_deltas: Sequence[NumberLike],
        *,
        currency: str = "SGD",
        precision: int = DEFAULT_PRECISION,
    ) -> PriceSensitivityResult:
        return price_sensitivity_grid(
            base_price,
            base_volume,
            price_deltas,
            volume_deltas,
            currency=currency,
            precision=precision,
        )

    def capital_stack_summary(
        self,
        slices: Sequence[Mapping[str, Any]],
        *,
        currency: str = "SGD",
        total_development_cost: NumberLike | None = None,
        precision: int = DEFAULT_PRECISION,
    ) -> CapitalStackSummary:
        return capital_stack_summary(
            slices,
            currency=currency,
            total_development_cost=total_development_cost,
            precision=precision,
        )

    def drawdown_schedule(
        self,
        entries: Sequence[Mapping[str, Any]],
        *,
        currency: str = "SGD",
        precision: int = DEFAULT_PRECISION,
    ) -> FinancingDrawdownSchedule:
        return drawdown_schedule(
            entries,
            currency=currency,
            precision=precision,
        )


__all__ = [
    "FinanceCalculator",
    "CapitalStackComponent",
    "CapitalStackSummary",
    "DscrEntry",
    "FinancingDrawdownEntry",
    "FinancingDrawdownSchedule",
    "PriceSensitivityResult",
    "capital_stack_summary",
    "dscr_timeline",
    "drawdown_schedule",
    "escalate_amount",
    "irr",
    "npv",
    "price_sensitivity_grid",
]
