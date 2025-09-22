"""Tests for buildable capacity calculations."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from app.schemas.buildable import BuildableDefaults
from app.services.buildable import ResolvedZone, calculate_buildable


class _LayerStub:
    """Lightweight stand-in for a zoning layer."""

    def __init__(self, attributes: dict[str, float]) -> None:
        self.attributes = attributes
        self.layer_name = "TestLayer"
        self.jurisdiction = "SG"


@pytest.mark.asyncio
async def test_calculate_buildable_honours_overrides(async_session_factory) -> None:
    defaults = BuildableDefaults(
        plot_ratio=2.5,
        site_area_m2=900.0,
        site_coverage=0.25,
        floor_height_m=4.0,
        efficiency_factor=0.8,
    )
    resolved = ResolvedZone(
        zone_code=None,
        parcel=None,
        zone_layers=[_LayerStub({"height_m": 30.0})],
        input_kind="geometry",
    )

    async with async_session_factory() as session:
        baseline = await calculate_buildable(session, resolved, defaults)
        assert baseline.metrics.floors_max == 7
        assert baseline.metrics.nsa_est_m2 == 1800

        overrides = await calculate_buildable(
            session,
            resolved,
            defaults,
            typ_floor_to_floor_m=5.0,
            efficiency_ratio=0.65,
        )
        assert overrides.metrics.floors_max == 6
        assert overrides.metrics.nsa_est_m2 == 1463
