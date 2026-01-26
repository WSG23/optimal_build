"""Geocoding API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

import structlog
from app.services.agents.ura_integration import URAIntegrationService
from app.services.geocoding import GeocodingService

router = APIRouter(prefix="/geocoding", tags=["geocoding"])
geocoding_service = GeocodingService()
ura_service = URAIntegrationService()
logger = structlog.get_logger()


class GeocodeResponse(BaseModel):
    """Normalized geocoding response."""

    model_config = ConfigDict(populate_by_name=True)

    latitude: float
    longitude: float
    formatted_address: str = Field(serialization_alias="formattedAddress")


class SmartSearchSuggestionResponse(BaseModel):
    """Suggestion payload enriched with zoning metadata."""

    model_config = ConfigDict(populate_by_name=True)

    address: str
    latitude: float
    longitude: float
    zoning: str | None = None
    zoning_description: str | None = Field(
        default=None, serialization_alias="zoningDescription"
    )
    site_area_sqm: float | None = Field(default=None, serialization_alias="siteArea")


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


@router.get("/suggestions", response_model=list[SmartSearchSuggestionResponse])
async def smart_search_suggestions(
    address: str = Query(..., min_length=3),
) -> list[SmartSearchSuggestionResponse]:
    """Return geocoded address suggestions enriched with zoning metadata."""

    try:
        result = await geocoding_service.geocode_details(address)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if result is None:
        return []

    latitude, longitude, formatted = result
    formatted_address = formatted or address

    zoning_info = None
    property_info = None
    try:
        zoning_info = await ura_service.get_zoning_info(formatted_address)
        property_info = await ura_service.get_property_info(formatted_address)
    except RuntimeError as exc:
        logger.warning("smart_search.ura_unavailable", error=str(exc))

    if zoning_info is None and property_info is None:
        return []

    zoning_description = None
    zoning_label = None
    if zoning_info is not None:
        zoning_description = zoning_info.zone_description
        zoning_label = zoning_info.zone_description or zoning_info.zone_code

    site_area = None
    if property_info is not None:
        site_area = property_info.site_area_sqm

    return [
        SmartSearchSuggestionResponse(
            address=formatted_address,
            latitude=latitude,
            longitude=longitude,
            zoning=zoning_label,
            zoning_description=zoning_description,
            site_area_sqm=site_area,
        )
    ]


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
