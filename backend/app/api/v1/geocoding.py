"""Geocoding API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.services.geocoding import GeocodingService

router = APIRouter(prefix="/geocoding", tags=["geocoding"])
geocoding_service = GeocodingService()


class GeocodeResponse(BaseModel):
    """Normalized geocoding response."""

    model_config = ConfigDict(populate_by_name=True)

    latitude: float
    longitude: float
    formatted_address: str = Field(serialization_alias="formattedAddress")


@router.get("/forward", response_model=GeocodeResponse)
async def forward_geocode(
    address: str = Query(..., min_length=3),
) -> GeocodeResponse:
    """Translate a free-form address into coordinates."""

    try:
        result = await geocoding_service.geocode_details(address)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="No results for this address")

    latitude, longitude, formatted = result
    return GeocodeResponse(
        latitude=latitude,
        longitude=longitude,
        formatted_address=formatted or address,
    )


@router.get("/reverse", response_model=GeocodeResponse)
async def reverse_geocode(
    latitude: float = Query(...),
    longitude: float = Query(...),
) -> GeocodeResponse:
    """Translate coordinates into a formatted address."""

    try:
        address = await geocoding_service.reverse_geocode(latitude, longitude)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if address is None:
        raise HTTPException(status_code=404, detail="No results for these coordinates")

    return GeocodeResponse(
        latitude=latitude,
        longitude=longitude,
        formatted_address=address.full_address,
    )
