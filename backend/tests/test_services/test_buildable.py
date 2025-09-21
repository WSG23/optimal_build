from __future__ import annotations

import pytest

from app.services.buildable import BuildableService
from app.services.geocode import GeocodeService


@pytest.mark.asyncio
async def test_buildable_calculation(session) -> None:
    geocode_service = GeocodeService(session)
    await geocode_service.seed_cache()
    geocode_result = await geocode_service.geocode("1 Marina Boulevard, Singapore")
    buildable_service = BuildableService(session)
    summary = await buildable_service.calculate(geocode_result)
    assert summary is not None
    assert summary.gross_floor_area_m2 > summary.allowable_coverage_m2
    assert summary.metrics["buildable.plot_ratio"] == pytest.approx(12.0)
