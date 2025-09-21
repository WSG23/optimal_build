"""Screening endpoints for buildable calculations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.rkp import RefParcel
from app.schemas import BuildableResponse, GeoJSONFeatureCollection
from app.services.buildable import BuildableService
from app.services.geocode import GeocodeService

router = APIRouter(prefix="/screen", tags=["screen"])


async def _resolve_buildable(
    address: str,
    session: AsyncSession,
) -> BuildableResponse:
    geocode_service = GeocodeService(session)
    await geocode_service.seed_cache()
    geocode_result = await geocode_service.geocode(address)
    if geocode_result is None:
        raise HTTPException(status_code=404, detail="Address not found")

    buildable_service = BuildableService(session)
    summary = await buildable_service.calculate(geocode_result)
    if summary is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    return BuildableResponse(
        address=address,
        parcel_ref=summary.parcel_ref,
        zoning_codes=summary.zoning_codes,
        site_area_m2=summary.site_area_m2,
        allowable_coverage_m2=summary.allowable_coverage_m2,
        gross_floor_area_m2=summary.gross_floor_area_m2,
        max_height_m=summary.max_height_m,
        metrics=summary.metrics,
        provenance=summary.provenance,
    )


@router.get("/buildable", response_model=BuildableResponse)
async def buildable_endpoint(
    address: str = Query(..., description="Address to evaluate"),
    session: AsyncSession = Depends(get_session),
) -> BuildableResponse:
    return await _resolve_buildable(address, session)


@router.get("/buildable-geojson", response_model=GeoJSONFeatureCollection)
async def buildable_geojson(
    address: str = Query(..., description="Address to evaluate"),
    session: AsyncSession = Depends(get_session),
) -> GeoJSONFeatureCollection:
    summary = await _resolve_buildable(address, session)
    parcel = None
    if summary.parcel_ref:
        parcel = await session.scalar(
            select(RefParcel).where(RefParcel.parcel_ref == summary.parcel_ref)
        )
    geometry = getattr(parcel, "bounds_json", None) if parcel is not None else None
    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "address": summary.address,
            "parcel_ref": summary.parcel_ref,
            **summary.metrics,
        },
    }
    return GeoJSONFeatureCollection(features=[feature])
