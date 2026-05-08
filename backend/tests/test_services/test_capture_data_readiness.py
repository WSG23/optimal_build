from __future__ import annotations

import pytest

from app.models.rkp import RefBuildingFootprint, RefParcel, RefRule, RefZoningLayer
from app.services.capture_data_readiness import get_capture_data_readiness


@pytest.mark.asyncio
async def test_capture_data_readiness_reports_missing_without_source_layers(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        readiness = await get_capture_data_readiness(session, jurisdiction="SG")

    assert readiness["status"] == "missing"
    assert readiness["capturePlanningGfaReady"] is False
    assert readiness["counts"]["zoningLayers"] == 0
    assert readiness["counts"]["parcels"] == 0
    assert readiness["counts"]["buildingFootprints"] == 0
    assert "Ingest URA Master Plan land-use polygons." in readiness["nextActions"]
    assert "Ingest SLA cadastral parcels." in readiness["nextActions"]
    assert (
        "Ingest URA Master Plan building footprints for vacant/developed parcel detection."
        in readiness["nextActions"]
    )


@pytest.mark.asyncio
async def test_capture_data_readiness_reports_ready_with_zoning_and_parcels(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        session.add_all(
            [
                RefZoningLayer(
                    jurisdiction="SG",
                    layer_name="MasterPlanImported",
                    zone_code="SG:commercial",
                    attributes={"LU_DESC": "Commercial", "GPR": "4.2"},
                ),
                RefParcel(
                    jurisdiction="SG",
                    parcel_ref="SG:LOT:MK01-00001",
                    bounds_json={"type": "Polygon", "coordinates": []},
                    area_m2=1200.0,
                    source="sla_data_gov",
                ),
                RefRule(
                    jurisdiction="SG",
                    authority="URA",
                    topic="zoning",
                    parameter_key="zoning.setback.front_min_m",
                    operator=">=",
                    value="6",
                    unit="m",
                    applicability={"zone_code": "SG:commercial"},
                    review_status="approved",
                    is_published=True,
                ),
                RefBuildingFootprint(
                    jurisdiction="SG",
                    layer_name="MasterPlanBuilding",
                    footprint_ref="SG:BUILDING:1",
                    bounds_json={"type": "Polygon", "coordinates": []},
                    area_m2=500.0,
                    source="ura_data_gov",
                ),
            ]
        )
        await session.flush()

        readiness = await get_capture_data_readiness(session, jurisdiction="SG")

    assert readiness["status"] == "ready"
    assert readiness["capturePlanningGfaReady"] is True
    assert readiness["counts"]["zoningLayers"] == 1
    assert readiness["counts"]["zoningPlotRatioLayers"] == 1
    assert readiness["counts"]["parcels"] == 1
    assert readiness["counts"]["approvedRules"] == 1
    assert readiness["counts"]["buildingFootprints"] == 1
    assert readiness["nextActions"] == []
