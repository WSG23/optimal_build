"""Ensure camelCase buildable requests remain backwards compatible."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from httpx import AsyncClient

from app.core.config import settings
from app.schemas.buildable import (
    BuildableCalculation,
    BuildableDefaults,
    BuildableMetrics,
    ZoneSource,
)


@pytest.mark.asyncio
async def test_buildable_endpoint_accepts_camel_case(
    app_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sending camelCase keys should be treated the same as snake_case."""

    monkeypatch.setattr(settings, "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.5)
    monkeypatch.setattr(settings, "BUILDABLE_EFFICIENCY_RATIO", 0.81)

    captured: dict[str, object] = {}

    async def _fake_calculate_buildable(
        *,
        session,
        resolved,
        defaults,
        typ_floor_to_floor_m,
        efficiency_ratio,
    ) -> BuildableCalculation:
        captured.update(
            {
                "defaults": defaults,
                "typ_floor_to_floor_m": typ_floor_to_floor_m,
                "efficiency_ratio": efficiency_ratio,
            }
        )
        return BuildableCalculation(
            metrics=BuildableMetrics(
                gfa_cap_m2=1234,
                floors_max=5,
                footprint_m2=456,
                nsa_est_m2=789,
            ),
            zone_source=ZoneSource(kind="unknown"),
            rules=[],
        )

    monkeypatch.setattr(
        "app.api.v1.screen.calculate_buildable", _fake_calculate_buildable
    )

    response = await app_client.post(
        "/api/v1/screen/buildable",
        json={
            "address": "123 Camel Case Rd",
            "typFloorToFloorM": 5.2,
            "efficiencyRatio": 0.76,
            "defaults": {
                "plotRatio": 4.1,
                "siteAreaM2": 980.0,
                "siteCoverage": 52,
                "floorHeightM": 5.1,
                "efficiencyFactor": 0.73,
            },
        },
        headers={"X-Role": "viewer"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["gfa_cap_m2"] == 1234

    assert captured["typ_floor_to_floor_m"] == pytest.approx(5.2)
    assert captured["efficiency_ratio"] == pytest.approx(0.76)

    defaults = captured["defaults"]
    assert isinstance(defaults, BuildableDefaults)
    assert defaults.plot_ratio == pytest.approx(4.1)
    assert defaults.site_area_m2 == pytest.approx(980.0)
    assert defaults.site_coverage == pytest.approx(0.52)
    assert defaults.floor_height_m == pytest.approx(5.1)
    assert defaults.efficiency_factor == pytest.approx(0.73)
