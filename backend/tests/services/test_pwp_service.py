from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import pwp as pwp_service


class _StubSession:
    pass


@pytest.mark.asyncio
async def test_adjust_pro_forma_cost_without_index(monkeypatch):
    async def _no_index(*args, **kwargs):
        return None

    monkeypatch.setattr(pwp_service, "get_latest_cost_index", _no_index)
    monkeypatch.setattr(pwp_service, "log_event", lambda *args, **kwargs: None)
    result = await pwp_service.adjust_pro_forma_cost(
        _StubSession(),
        base_cost=Decimal("100.00"),
        series_name="SG_BCA",
    )
    assert result == Decimal("100.00")


@pytest.mark.asyncio
async def test_adjust_pro_forma_cost_with_index(monkeypatch):
    index = SimpleNamespace(value=Decimal("1.08"))

    async def fake_get_latest_cost_index(*args, **kwargs):
        return index

    monkeypatch.setattr(
        pwp_service, "get_latest_cost_index", fake_get_latest_cost_index
    )
    events: list[tuple] = []
    monkeypatch.setattr(
        pwp_service, "log_event", lambda *args, **kwargs: events.append(args)
    )
    pwp_service.metrics.reset_metrics()

    result = await pwp_service.adjust_pro_forma_cost(
        _StubSession(),
        base_cost=Decimal("120.00"),
        series_name="SG_BCA",
    )
    assert result == Decimal("129.60")
    assert events
