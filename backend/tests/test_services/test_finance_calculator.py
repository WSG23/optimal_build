"""Unit tests for the lightweight finance calculator utilities."""

from __future__ import annotations

import importlib.util
import sys
import types
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

import pytest

_ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, relative_path: str):
    module_path = _ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@dataclass
class RefCostIndex:
    jurisdiction: str
    series_name: str
    category: str
    period: str
    value: Decimal
    unit: str
    provider: str
    source: str

    @classmethod
    def latest(
        cls,
        indices: Iterable["RefCostIndex"],
        *,
        jurisdiction: str | None = None,
        provider: str | None = None,
        series_name: str | None = None,
    ) -> "RefCostIndex" | None:
        filtered: list[RefCostIndex] = []
        for index in indices:
            if jurisdiction and index.jurisdiction != jurisdiction:
                continue
            if provider and index.provider != provider:
                continue
            if series_name and index.series_name != series_name:
                continue
            filtered.append(index)
        if not filtered:
            return None
        return filtered[-1]


_models_pkg = types.ModuleType("app.models")
_models_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules.setdefault("app.models", _models_pkg)
_rkp_module = types.ModuleType("app.models.rkp")
_rkp_module.RefCostIndex = RefCostIndex
sys.modules["app.models.rkp"] = _rkp_module

_services_pkg = types.ModuleType("app.services")
_services_pkg.__path__ = []  # type: ignore[attr-defined]
sys.modules.setdefault("app.services", _services_pkg)

calculator = _load_module(
    "finance_calculator_stub", "backend/app/services/finance/calculator.py"
)

sys.modules.pop("app.models", None)
sys.modules.pop("app.models.rkp", None)
sys.modules.pop("app.services", None)


def test_npv_basic_case() -> None:
    rate = Decimal("0.05")
    cash_flows = [Decimal("-1000"), Decimal("400"), Decimal("400"), Decimal("400")]
    result = calculator.npv(rate, cash_flows)
    assert result.quantize(Decimal("0.01")) == Decimal("89.30")


def test_irr_newton_with_fallback() -> None:
    cash_flows = [Decimal("-1000"), Decimal("300"), Decimal("420"), Decimal("680")]
    result = calculator.irr(cash_flows)
    assert result.quantize(Decimal("0.0001")) == Decimal("0.1634")


def test_dscr_timeline_handles_zero_debt() -> None:
    incomes = [Decimal("1200.00"), Decimal("1000.00")]
    debts = [Decimal("1000.00"), Decimal("0")]
    timeline = calculator.dscr_timeline(
        incomes, debts, period_labels=["Y1", "Y2"], currency="SGD"
    )
    assert timeline[0].noi == Decimal("1200.00")
    assert timeline[0].dscr == Decimal("1.2000")
    assert timeline[0].currency == "SGD"
    assert timeline[1].dscr == Decimal("Infinity")


def test_price_sensitivity_grid_returns_quantized_values() -> None:
    grid = calculator.price_sensitivity_grid(
        base_price=Decimal("100"),
        base_volume=Decimal("10"),
        price_deltas=[Decimal("-0.10"), Decimal("0"), Decimal("0.10")],
        volume_deltas=[Decimal("-0.10"), Decimal("0"), Decimal("0.10")],
        currency="USD",
    )
    assert grid.currency == "USD"
    assert grid.prices == (
        Decimal("90.00"),
        Decimal("100.00"),
        Decimal("110.00"),
    )
    assert grid.grid[1][1] == Decimal("1000.00")


def test_escalate_amount_uses_latest_index() -> None:
    indices = [
        RefCostIndex(
            jurisdiction="SG",
            series_name="concrete",
            category="material",
            period="2023-Q4",
            value=Decimal("100"),
            unit="SGD/m3",
            provider="internal",
            source="seed",
        ),
        RefCostIndex(
            jurisdiction="SG",
            series_name="concrete",
            category="material",
            period="2024-Q1",
            value=Decimal("110"),
            unit="SGD/m3",
            provider="internal",
            source="seed",
        ),
    ]
    escalated = calculator.escalate_amount(
        Decimal("100.00"),
        base_period="2023-Q4",
        indices=indices,
        series_name="concrete",
        jurisdiction="SG",
        provider="internal",
    )
    assert escalated == Decimal("110.00")


@pytest.mark.parametrize(
    "cash_flows",
    [
        [Decimal("100"), Decimal("200")],
        [Decimal("-300"), Decimal("-200")],
    ],
)
def test_irr_requires_sign_change(cash_flows):
    with pytest.raises(ValueError):
        calculator.irr(cash_flows)
