"""Buildable screening endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.rkp import RefGeocodeCache, RefParcel, RefZoningLayer
from app.services.buildable import BuildableMetrics, calculate_buildable_metrics


router = APIRouter(prefix="/screen")


DEFAULT_PLOT_RATIO = 3.5


@dataclass(slots=True)
class SiteContext:
    """Resolved parcel and geometry context for buildable calculations."""

    zone_code: Optional[str]
    site_area_sqm: Optional[float]
    floorplate_sqm: Optional[float]
    max_height_m: Optional[float]
    plot_ratio: Optional[float]

class BuildableRequest(BaseModel):
    address: Optional[str] = None
    geometry: Optional[Dict[str, object]] = None
    project_type: Optional[str] = None
    typ_floor_to_floor_m: float = Field(
        default_factory=lambda: settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M
    )
    efficiency_ratio: float = Field(
        default_factory=lambda: settings.BUILDABLE_EFFICIENCY_RATIO
    )

    @model_validator(mode="before")
    def _populate_metric_defaults(cls, data: object) -> object:
        if isinstance(data, dict):
            if data.get("typ_floor_to_floor_m") is None:
                data["typ_floor_to_floor_m"] = settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M
            if data.get("efficiency_ratio") is None:
                data["efficiency_ratio"] = settings.BUILDABLE_EFFICIENCY_RATIO
        return data

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
    context = await _resolve_site_context(session, payload)
    zone_code = context.zone_code
    overlays: List[str] = []
    hints: List[str] = []
    zoning_layers: List[RefZoningLayer] = []
    if zone_code:
        zoning_layers = await _load_layers_for_zone(session, zone_code)
        for layer in zoning_layers:
            attributes = layer.attributes or {}
            overlays.extend(attributes.get("overlays", []))
            hints.extend(attributes.get("advisory_hints", []))
    overlays = list(dict.fromkeys(filter(None, overlays)))
    hints = list(dict.fromkeys(filter(None, hints)))

    plot_ratio = context.plot_ratio
    if plot_ratio is None:
        plot_ratio = _determine_plot_ratio(zoning_layers) or DEFAULT_PLOT_RATIO

    buildable_metrics: Optional[BuildableMetrics] = None
    if context.site_area_sqm and context.site_area_sqm > 0:
        buildable_metrics = calculate_buildable_metrics(
            site_area_sqm=context.site_area_sqm,
            plot_ratio=plot_ratio,
            typ_floor_to_floor_m=payload.typ_floor_to_floor_m,
            efficiency_ratio=payload.efficiency_ratio,
            floorplate_sqm=context.floorplate_sqm,
            max_height_m=context.max_height_m,
        )

    return {
        "input_kind": "address" if payload.address else "geometry",
        "zone_code": zone_code,
        "overlays": overlays,
        "advisory_hints": hints,
        "buildable_metrics": buildable_metrics.as_dict() if buildable_metrics else None,
    }


async def _resolve_site_context(
    session: AsyncSession, payload: BuildableRequest
) -> SiteContext:
    zone_code: Optional[str] = None
    site_area: Optional[float] = None
    floorplate: Optional[float] = None
    max_height: Optional[float] = None
    plot_ratio: Optional[float] = None

    if payload.address:
        stmt = select(RefGeocodeCache).where(RefGeocodeCache.address == payload.address)
        geocode = (await session.execute(stmt)).scalar_one_or_none()
        if geocode and geocode.parcel_id:
            parcel = await session.get(RefParcel, geocode.parcel_id)
            if parcel and isinstance(parcel.bounds_json, dict):
                zone = parcel.bounds_json.get("zone_code")
                if zone:
                    zone_code = str(zone)
            if parcel and parcel.area_m2 is not None:
                try:
                    site_area = float(parcel.area_m2)
                    floorplate = site_area
                except (TypeError, ValueError):
                    site_area = None
    if payload.geometry and isinstance(payload.geometry, dict):
        properties = payload.geometry.get("properties")
        if isinstance(properties, dict):
            if zone_code is None and properties.get("zone_code"):
                zone_code = str(properties["zone_code"])
            if plot_ratio is None:
                plot_ratio = _first_numeric(
                    properties,
                    "plot_ratio",
                    "gross_plot_ratio",
                    "max_plot_ratio",
                    "far",
                )
            if site_area is None:
                site_area = _first_numeric(
                    properties,
                    "site_area_sqm",
                    "site_area",
                    "area_sqm",
                )
            if floorplate is None:
                floorplate = _first_numeric(
                    properties,
                    "floorplate_sqm",
                    "avg_floorplate_sqm",
                )
            if max_height is None:
                max_height = _first_numeric(
                    properties,
                    "max_height_m",
                    "height_limit_m",
                    "height_m",
                )

    if floorplate is None and site_area is not None:
        floorplate = site_area

    return SiteContext(
        zone_code=zone_code,
        site_area_sqm=site_area,
        floorplate_sqm=floorplate,
        max_height_m=max_height,
        plot_ratio=plot_ratio,
    )


async def _load_layers_for_zone(
    session: AsyncSession, zone_code: str
) -> List[RefZoningLayer]:
    stmt = select(RefZoningLayer).where(RefZoningLayer.zone_code == zone_code)
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _first_numeric(data: Dict[str, object], *keys: str) -> Optional[float]:
    for key in keys:
        if key in data:
            numeric = _safe_float(data.get(key))
            if numeric is not None:
                return numeric
    return None


def _safe_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _determine_plot_ratio(layers: List[RefZoningLayer]) -> Optional[float]:
    for layer in layers:
        attributes = layer.attributes or {}
        numeric = _first_numeric(
            attributes,
            "plot_ratio",
            "gross_plot_ratio",
            "max_plot_ratio",
            "far",
        )
        if numeric is not None:
            return numeric
    return None


__all__ = ["router"]
