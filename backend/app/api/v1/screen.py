"""Buildable screening endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.rkp import RefGeocodeCache, RefParcel, RefZoningLayer


router = APIRouter(prefix="/screen")


class BuildableRequest(BaseModel):
    address: Optional[str] = None
    geometry: Optional[Dict[str, object]] = None
    project_type: Optional[str] = None

    @model_validator(mode="after")
    def _validate_payload(cls, values: "BuildableRequest") -> "BuildableRequest":
        if not values.address and not values.geometry:
            raise ValueError("Either address or geometry must be provided")
        return values


@router.post("/buildable")
async def screen_buildable(
    payload: BuildableRequest,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, object]:
    zone_code = await _resolve_zone_code(session, payload)
    overlays: List[str] = []
    hints: List[str] = []
    if zone_code:
        zoning_lookup = await _load_layers_for_zone(session, zone_code)
        for layer in zoning_lookup:
            attributes = layer.attributes or {}
            overlays.extend(attributes.get("overlays", []))
            hints.extend(attributes.get("advisory_hints", []))
    overlays = list(dict.fromkeys(filter(None, overlays)))
    hints = list(dict.fromkeys(filter(None, hints)))
    return {
        "input_kind": "address" if payload.address else "geometry",
        "zone_code": zone_code,
        "overlays": overlays,
        "advisory_hints": hints,
    }


async def _resolve_zone_code(
    session: AsyncSession, payload: BuildableRequest
) -> Optional[str]:
    if payload.address:
        stmt = select(RefGeocodeCache).where(RefGeocodeCache.address == payload.address)
        geocode = (await session.execute(stmt)).scalar_one_or_none()
        if geocode and geocode.parcel_id:
            parcel = await session.get(RefParcel, geocode.parcel_id)
            if parcel and isinstance(parcel.bounds_json, dict):
                zone_code = parcel.bounds_json.get("zone_code")
                if zone_code:
                    return str(zone_code)
    if payload.geometry and isinstance(payload.geometry, dict):
        properties = payload.geometry.get("properties")
        if isinstance(properties, dict) and properties.get("zone_code"):
            return str(properties["zone_code"])
    return None


async def _load_layers_for_zone(
    session: AsyncSession, zone_code: str
) -> List[RefZoningLayer]:
    stmt = select(RefZoningLayer).where(RefZoningLayer.zone_code == zone_code)
    result = await session.execute(stmt)
    return list(result.scalars().all())


__all__ = ["router"]
