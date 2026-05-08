"""Readiness checks for Capture jurisdiction source datasets."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefBuildingFootprint, RefParcel, RefRule, RefZoningLayer

PLOT_RATIO_KEYS = {
    "gpr",
    "GPR",
    "plot_ratio",
    "plotRatio",
    "gross_plot_ratio",
    "max_far",
}


def _has_plot_ratio_attribute(attributes: Any) -> bool:
    if not isinstance(attributes, dict):
        return False
    return any(
        key in attributes and attributes[key] not in (None, "", " ")
        for key in PLOT_RATIO_KEYS
    )


def _status_from_required_checks(checks: list[dict[str, Any]]) -> str:
    required = [check for check in checks if check.get("required")]
    ready_count = sum(1 for check in required if check.get("status") == "ready")
    if ready_count == len(required):
        return "ready"
    if ready_count > 0:
        return "partial"
    return "missing"


async def get_capture_data_readiness(
    session: AsyncSession,
    *,
    jurisdiction: str = "SG",
) -> dict[str, Any]:
    """Return whether Capture has the data needed for planning-envelope GFA."""

    normalized_jurisdiction = jurisdiction.strip().upper() or "SG"
    zoning_count = int(
        await session.scalar(
            select(func.count(RefZoningLayer.id)).where(
                RefZoningLayer.jurisdiction == normalized_jurisdiction
            )
        )
        or 0
    )
    parcel_count = int(
        await session.scalar(
            select(func.count(RefParcel.id)).where(
                RefParcel.jurisdiction == normalized_jurisdiction
            )
        )
        or 0
    )
    approved_rule_count = int(
        await session.scalar(
            select(func.count(RefRule.id)).where(
                RefRule.jurisdiction == normalized_jurisdiction,
                RefRule.review_status == "approved",
                RefRule.is_published.is_(True),
            )
        )
        or 0
    )
    building_footprint_count = int(
        await session.scalar(
            select(func.count(RefBuildingFootprint.id)).where(
                RefBuildingFootprint.jurisdiction == normalized_jurisdiction
            )
        )
        or 0
    )

    layer_attrs = (
        await session.execute(
            select(RefZoningLayer.attributes).where(
                RefZoningLayer.jurisdiction == normalized_jurisdiction
            )
        )
    ).scalars()
    zoning_plot_ratio_count = sum(
        1 for attributes in layer_attrs if _has_plot_ratio_attribute(attributes)
    )

    checks = [
        {
            "key": "zoning_layers",
            "label": "URA Master Plan zoning polygons",
            "status": "ready" if zoning_count > 0 else "missing",
            "count": zoning_count,
            "required": True,
        },
        {
            "key": "zoning_plot_ratio_layers",
            "label": "Zoning polygons with plot ratio attributes",
            "status": "ready" if zoning_plot_ratio_count > 0 else "missing",
            "count": zoning_plot_ratio_count,
            "required": True,
        },
        {
            "key": "parcel_boundaries",
            "label": "SLA cadastral parcels",
            "status": "ready" if parcel_count > 0 else "missing",
            "count": parcel_count,
            "required": True,
        },
        {
            "key": "approved_rules",
            "label": "Approved RefRule controls",
            "status": "ready" if approved_rule_count > 0 else "missing",
            "count": approved_rule_count,
            "required": False,
        },
        {
            "key": "building_footprints",
            "label": "URA Master Plan building footprints",
            "status": "ready" if building_footprint_count > 0 else "missing",
            "count": building_footprint_count,
            "required": False,
        },
    ]

    planning_gfa_ready = zoning_plot_ratio_count > 0 and parcel_count > 0
    status = _status_from_required_checks(checks)
    return {
        "jurisdiction": normalized_jurisdiction,
        "status": status,
        "capturePlanningGfaReady": planning_gfa_ready,
        "currentGfaSourceReady": False,
        "counts": {
            "zoningLayers": zoning_count,
            "zoningPlotRatioLayers": zoning_plot_ratio_count,
            "parcels": parcel_count,
            "approvedRules": approved_rule_count,
            "buildingFootprints": building_footprint_count,
        },
        "checks": checks,
        "nextActions": [
            action
            for action in (
                (
                    "Ingest URA Master Plan land-use polygons."
                    if zoning_count == 0
                    else None
                ),
                ("Ingest SLA cadastral parcels." if parcel_count == 0 else None),
                (
                    "Verify plot ratio attributes in the zoning layer."
                    if zoning_count > 0 and zoning_plot_ratio_count == 0
                    else None
                ),
                (
                    "Ingest URA Master Plan building footprints for vacant/developed parcel detection."
                    if building_footprint_count == 0
                    else None
                ),
            )
            if action
        ],
    }
