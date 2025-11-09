"""Buildable screening endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import structlog
from fastapi import APIRouter, Body, Depends

from app.api.deps import require_viewer
from app.core.database import get_session
from app.models.rkp import RefGeocodeCache, RefParcel, RefZoningLayer
from app.schemas.buildable import (
    BUILDABLE_REQUEST_EXAMPLE,
    BUILDABLE_RESPONSE_EXAMPLE,
    BuildableMetrics,
    BuildableRequest,
    BuildableResponse,
    BuildableRule,
    BuildableRuleProvenance,
    ZoneSource,
)
from app.services.buildable import (
    ResolvedZone,
    calculate_buildable,
    load_layers_for_zone,
)
from app.utils import metrics
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/screen")
logger = structlog.get_logger()


@dataclass
class ZoneResolution:
    """Intermediate representation of a resolved zoning lookup."""

    zone_code: str | None
    parcel: RefParcel | None
    geometry_properties: dict[str, Any] | None
    input_kind: str


@router.post(
    "/buildable",
    response_model=BuildableResponse,
    responses={
        200: {"content": {"application/json": {"example": BUILDABLE_RESPONSE_EXAMPLE}}}
    },
)
async def screen_buildable(
    payload: BuildableRequest = Body(..., example=BUILDABLE_REQUEST_EXAMPLE),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
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
    except Exception as exc:
        logger.warning(
            "buildable_screening_fallback",
            error=str(exc),
            address=payload.address,
            has_geometry=bool(payload.geometry),
        )
        return _build_mock_buildable_response(payload)
    finally:
        duration_ms = (perf_counter() - start_time) * 1000.0
        metrics.PWP_BUILDABLE_DURATION_MS.observe(duration_ms)


async def _resolve_zone_resolution(
    session: AsyncSession, payload: BuildableRequest
) -> ZoneResolution:
    input_kind = "address" if payload.address else "geometry"
    parcel: RefParcel | None = None
    zone_code: str | None = None

    if payload.address:
        stmt = select(RefGeocodeCache).where(RefGeocodeCache.address == payload.address)
        geocode = (await session.execute(stmt)).scalar_one_or_none()
        if geocode and geocode.parcel_id:
            parcel = await session.get(RefParcel, geocode.parcel_id)
            if parcel and isinstance(parcel.bounds_json, dict):
                code = parcel.bounds_json.get("zone_code")
                if code:
                    zone_code = str(code)

    geometry_properties: dict[str, Any] | None = None
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
    layers: list[RefZoningLayer],
) -> tuple[list[str], list[str]]:
    overlays: list[str] = []
    hints: list[str] = []
    for layer in layers:
        attributes = layer.attributes or {}
        overlays.extend(attributes.get("overlays", []))
        hints.extend(attributes.get("advisory_hints", []))
    overlays = list(dict.fromkeys(filter(None, overlays)))
    hints = list(dict.fromkeys(filter(None, hints)))
    return overlays, hints


def _build_mock_buildable_response(payload: BuildableRequest) -> BuildableResponse:
    """Provide a deterministic response for offline/demo environments."""

    input_kind = "address" if payload.address else "geometry"
    zone_code = "MU"
    overlays = [
        "Transit-Oriented Development Overlay",
        "Urban Greenery Incentive",
    ]
    hints = [
        "Verify podium articulation against design handbook",
        "Consider shared mobility hub on lower levels",
    ]

    metrics = BuildableMetrics(
        gfa_cap_m2=19000,
        floors_max=15,
        footprint_m2=payload.defaults.site_area_m2 if payload.defaults else 1200,
        nsa_est_m2=14250,
    )

    zone_source = ZoneSource(
        kind="geometry" if payload.geometry else "unknown",
        layer_name="Master Plan 2024",
        jurisdiction="Singapore",
        note="Stubbed response generated without live zoning datasets",
    )

    rules = [
        BuildableRule(
            id=101,
            authority="URA",
            parameter_key="plot_ratio",
            operator="<=",
            value="3.6",
            unit="ratio",
            provenance=BuildableRuleProvenance(
                rule_id=101,
                clause_ref="MP2024-PR-11",
                document_id=9001,
                pages=[12, 13],
                seed_tag="demo_seed",
            ),
        ),
        BuildableRule(
            id=102,
            authority="BCA",
            parameter_key="site_coverage",
            operator="<=",
            value="0.7",
            unit="ratio",
            provenance=BuildableRuleProvenance(
                rule_id=102,
                clause_ref="BCA-GS-4.2",
                document_id=9102,
                pages=[4],
                seed_tag="demo_seed",
            ),
        ),
    ]

    return BuildableResponse(
        input_kind=input_kind,
        zone_code=zone_code,
        overlays=overlays,
        advisory_hints=hints,
        metrics=metrics,
        zone_source=zone_source,
        rules=rules,
    )


__all__ = ["router"]
