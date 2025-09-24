"""Tests for the PWP pro-forma cost adjustments."""

from __future__ import annotations

from decimal import Decimal

import pytest

pytest.importorskip("sqlalchemy")

from backend.app.models.rkp import RefCostIndex
from backend.app.services.pwp import adjust_pro_forma_cost
from backend.app.utils import metrics


@pytest.mark.asyncio
async def test_adjust_pro_forma_cost(session):
    """Pro-forma cost adjustments scale by the cost index."""

    session.add(
        RefCostIndex(
            jurisdiction="SG",
            series_name="steel",
            category="material",
            subcategory="rebar",
            period="2023-Q4",
            value=Decimal("1.15"),
            unit="scalar",
            source="test",
            provider="official",
        )
    )
    await session.commit()

    adjusted = await adjust_pro_forma_cost(
        session,
        base_cost=Decimal("1000"),
        series_name="steel",
        provider="official",
    )

    assert adjusted == Decimal("1150.00")
    gauge = metrics.COST_ADJUSTMENT_GAUGE.labels(series="steel")
    assert gauge._value.get() == 1.15
