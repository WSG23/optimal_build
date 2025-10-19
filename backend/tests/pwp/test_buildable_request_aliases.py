"""Ensure camelCase request payloads are accepted by the buildable API."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

import pytest_asyncio  # noqa: F401
from app.core.config import settings
from app.schemas.buildable import (
    BuildableCalculation,
    BuildableDefaults,
    BuildableMetrics,
    ZoneSource,
)
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_buildable_request_accepts_camel_case(
    app_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "BUILDABLE_TYP_FLOOR_TO_FLOOR_M", 4.8)
    monkeypatch.setattr(settings, "BUILDABLE_EFFICIENCY_RATIO", 0.79)

    captured: dict[str, object] = {}

    async def _fake_calculate_buildable(
        *,
        session,
        resolved,
        defaults,
        typ_floor_to_floor_m,
        efficiency_ratio,
    ):
        captured.update(
            {
                "defaults": defaults,
                "typ_floor_to_floor_m": typ_floor_to_floor_m,
                "efficiency_ratio": efficiency_ratio,
            }
        )
        return BuildableCalculation(
            metrics=BuildableMetrics(
                gfa_cap_m2=4321,
                floors_max=6,
                footprint_m2=543,
                nsa_est_m2=3456,
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
            "address": "123 Example Ave",
            "typFloorToFloorM": 5.6,
            "efficiencyRatio": 0.74,
            "defaults": {
                "plotRatio": 4.2,
                "siteAreaM2": 900.0,
                "siteCoverage": 55,
                "floorHeightM": 5.0,
                "efficiencyFactor": 0.72,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["gfa_cap_m2"] == 4321

    assert captured["typ_floor_to_floor_m"] == pytest.approx(5.6)
    assert captured["efficiency_ratio"] == pytest.approx(0.74)

    defaults = captured["defaults"]
    assert isinstance(defaults, BuildableDefaults)
    assert defaults.plot_ratio == pytest.approx(4.2)
    assert defaults.site_area_m2 == pytest.approx(900.0)
    assert defaults.site_coverage == pytest.approx(0.55)
    assert defaults.floor_height_m == pytest.approx(5.0)
    assert defaults.efficiency_factor == pytest.approx(0.72)
