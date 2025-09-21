"""Buildable screening endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.rkp import RefGeocodeCache, RefParcel, RefZoningLayer
from app.services.buildable_screening import (
    compose_buildable_response,
    zone_code_from_geometry,
    zone_code_from_parcel,
)

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
    layers = await _load_layers_for_zone(session, zone_code) if zone_code else []
    return compose_buildable_response(
        address=payload.address,
        geometry=payload.geometry,
        zone_code=zone_code,
        layers=layers,
    )


async def _resolve_zone_code(
    session: AsyncSession, payload: BuildableRequest
) -> Optional[str]:
    if payload.address:
        stmt = select(RefGeocodeCache).where(RefGeocodeCache.address == payload.address)
        geocode = (await session.execute(stmt)).scalar_one_or_none()
        if geocode and geocode.parcel_id:
            parcel = await session.get(RefParcel, geocode.parcel_id)
            zone = zone_code_from_parcel(parcel)
            if zone:
                return zone
    return zone_code_from_geometry(payload.geometry)


async def _load_layers_for_zone(
    session: AsyncSession, zone_code: str
) -> List[RefZoningLayer]:
    stmt = select(RefZoningLayer).where(RefZoningLayer.zone_code == zone_code)
    result = await session.execute(stmt)
    return list(result.scalars().all())


__all__ = ["router"]
