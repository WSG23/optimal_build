"""Tests for the buildable envelope calculator."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import pytest

from app.core.config import settings
from app.services.buildable import calculate_buildable_metrics


def _round_half_up(value: float) -> int:
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def test_calculator_uses_default_parameters() -> None:
    """Default configuration values are applied when no overrides are supplied."""

    metrics = calculate_buildable_metrics(
        site_area_sqm=1250.0,
        plot_ratio=3.5,
        typ_floor_to_floor_m=settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M,
        efficiency_ratio=settings.BUILDABLE_EFFICIENCY_RATIO,
    )

    expected_gross = _round_half_up(1250.0 * 3.5)
    expected_net = _round_half_up(expected_gross * settings.BUILDABLE_EFFICIENCY_RATIO)

    assert metrics.gross_floor_area_sqm == expected_gross
    assert metrics.net_floor_area_sqm == expected_net
    assert metrics.estimated_storeys == _round_half_up(expected_gross / 1250.0)
    assert metrics.estimated_height_m == pytest.approx(
        metrics.estimated_storeys * settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M
    )
    assert metrics.efficiency_ratio == settings.BUILDABLE_EFFICIENCY_RATIO
    assert metrics.typ_floor_to_floor_m == settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M


def test_calculator_honours_explicit_overrides() -> None:
    """Explicit overrides take precedence over configuration defaults."""

    metrics = calculate_buildable_metrics(
        site_area_sqm=950.0,
        plot_ratio=2.8,
        typ_floor_to_floor_m=3.2,
        efficiency_ratio=0.73,
        floorplate_sqm=500.0,
        max_height_m=15.0,
    )

    assert metrics.estimated_storeys == 4
    assert metrics.gross_floor_area_sqm == 2000
    assert metrics.net_floor_area_sqm == _round_half_up(2000 * 0.73)
    assert metrics.estimated_height_m == pytest.approx(12.8)
    assert metrics.typ_floor_to_floor_m == pytest.approx(3.2)
    assert metrics.efficiency_ratio == pytest.approx(0.73)


def test_calculator_limits_by_height() -> None:
    """Height limits reduce achievable gross floor area when restrictive."""

    metrics = calculate_buildable_metrics(
        site_area_sqm=900.0,
        plot_ratio=4.0,
        typ_floor_to_floor_m=3.0,
        efficiency_ratio=0.75,
        floorplate_sqm=600.0,
        max_height_m=5.0,
    )

    assert metrics.estimated_storeys == 1
    assert metrics.gross_floor_area_sqm == 600
    assert metrics.net_floor_area_sqm == _round_half_up(600 * 0.75)
    assert metrics.estimated_height_m == pytest.approx(3.0)
