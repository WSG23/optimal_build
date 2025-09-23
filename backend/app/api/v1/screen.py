"""Buildable screening endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.rkp import RefGeocodeCache, RefParcel, RefZoningLayer
from app.schemas.buildable import BuildableRequest, BuildableResponse
from app.services.buildable import (
    ResolvedZone,
    calculate_buildable,
    load_layers_for_zone,
)
from app.utils import metrics


router = APIRouter(prefix="/screen")


@dataclass
class ZoneResolution:
    """Intermediate representation of a resolved zoning lookup."""

    zone_code: Optional[str]
    parcel: Optional[RefParcel]
    geometry_properties: Optional[Dict[str, Any]]
    input_kind: str


@router.post("/buildable", response_model=BuildableResponse)
async def screen_buildable(
    payload: BuildableRequest,
    session: AsyncSession = Depends(get_session),
) -> BuildableResponse:
    start_time = perf_counter()
    metrics.PWP_BUILDABLE_TOTAL.inc()
    try:
        resolution = await _resolve_zone_resolution(session, payload)
        zone_layers = (
            await load_layers_for_zone(session, resolution.zone_code)
            if resolution.zone_code
            else []
        )
        overlays, hints = _collect_zone_metadata(zone_layers)
        resolved = ResolvedZone(
            zone_code=resolution.zone_code,
            parcel=resolution.parcel,
            zone_layers=zone_layers,
            input_kind=resolution.input_kind,
            geometry_properties=resolution.geometry_properties,
        )
        calculation = await calculate_buildable(
            session=session,
            resolved=resolved,
            defaults=payload.defaults,
            typ_floor_to_floor_m=payload.typ_floor_to_floor_m,
            efficiency_ratio=payload.efficiency_ratio,
        )
        return BuildableResponse(
            input_kind=resolution.input_kind,
            zone_code=resolution.zone_code,
            overlays=overlays,
            advisory_hints=hints,
            metrics=calculation.metrics,
            zone_source=calculation.zone_source,
            rules=calculation.rules,
        )
    finally:
        duration_ms = (perf_counter() - start_time) * 1000.0
        metrics.PWP_BUILDABLE_DURATION_MS.observe(duration_ms)


async def _resolve_zone_resolution(
    session: AsyncSession, payload: BuildableRequest
) -> ZoneResolution:
    input_kind = "address" if payload.address else "geometry"
    parcel: Optional[RefParcel] = None
    zone_code: Optional[str] = None

    if payload.address:
        stmt = select(RefGeocodeCache).where(RefGeocodeCache.address == payload.address)
        geocode = (await session.execute(stmt)).scalar_one_or_none()
        if geocode and geocode.parcel_id:
            parcel = await session.get(RefParcel, geocode.parcel_id)
            if parcel and isinstance(parcel.bounds_json, dict):
                code = parcel.bounds_json.get("zone_code")
                if code:
                    zone_code = str(code)

    geometry_properties: Optional[Dict[str, Any]] = None
    if payload.geometry:
        properties = payload.geometry.get("properties")
        if isinstance(properties, dict):
            geometry_properties = dict(properties)
            if geometry_properties.get("zone_code") and not zone_code:
                zone_code = str(geometry_properties["zone_code"])

    return ZoneResolution(
        zone_code=zone_code,
        parcel=parcel,
        geometry_properties=geometry_properties,
        input_kind=input_kind,
    )


def _collect_zone_metadata(
    layers: List[RefZoningLayer],
) -> tuple[List[str], List[str]]:
    overlays: List[str] = []
    hints: List[str] = []
    for layer in layers:
        attributes = layer.attributes or {}
        overlays.extend(attributes.get("overlays", []))
        hints.extend(attributes.get("advisory_hints", []))
    overlays = list(dict.fromkeys(filter(None, overlays)))
    hints = list(dict.fromkeys(filter(None, hints)))
    return overlays, hints


__all__ = ["router"]
