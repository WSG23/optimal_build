"""Geocoding API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import RequestIdentity, require_viewer
from app.schemas.external_sources import ExternalSourceMetadata
from app.services.geocoding import GeocodingService

router = APIRouter(prefix="/geocoding", tags=["geocoding"])
geocoding_service = GeocodingService()


class GeocodeResponse(BaseModel):
    """Normalized geocoding response."""

    model_config = ConfigDict(populate_by_name=True)

    latitude: float
    longitude: float
    formatted_address: str = Field(serialization_alias="formattedAddress")
    source: ExternalSourceMetadata


@router.get("/forward", response_model=GeocodeResponse)
async def forward_geocode(
    address: str = Query(..., min_length=3),
    jurisdiction_code: str | None = Query(default=None, alias="jurisdictionCode"),
    _identity: RequestIdentity = Depends(require_viewer),
) -> GeocodeResponse:
    """Translate a free-form address into coordinates."""

    try:
        result = await geocoding_service.geocode_lookup(
            address,
            jurisdiction_code=jurisdiction_code,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="No results for this address")

    return GeocodeResponse(
        latitude=result.latitude,
        longitude=result.longitude,
        formatted_address=result.formatted_address or address,
        source=result.source,
    )


@router.get("/reverse", response_model=GeocodeResponse)
async def reverse_geocode(
    latitude: float = Query(...),
    longitude: float = Query(...),
    _identity: RequestIdentity = Depends(require_viewer),
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
        source=geocoding_service.get_google_geocoding_metadata(),
    )
