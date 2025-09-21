"""Buildable area calculations based on parcel and zoning data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING

import importlib.util
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefParcel, RefZoningLayer
from app.utils.logging import get_logger

_PINT_SPEC = importlib.util.find_spec("pint")
if _PINT_SPEC is not None:  # pragma: no cover
    from pint import UnitRegistry  # type: ignore
else:  # pragma: no cover
    UnitRegistry = None  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - used only for typing
    from app.services.geocode import GeocodeResult

logger = get_logger(__name__)


@dataclass
class BuildableSummary:
    """Summarised buildable envelope numbers."""

    parcel_ref: Optional[str]
    zoning_codes: List[str]
    site_area_m2: float
    allowable_coverage_m2: float
    gross_floor_area_m2: float
    max_height_m: Optional[float]
    metrics: Dict[str, float]
    provenance: Dict[str, str]


class BuildableService:
    """Compute buildable metrics for an address or parcel."""

    def __init__(self, session: AsyncSession, unit_registry: Optional[UnitRegistry] = None) -> None:
        self._session = session
        if UnitRegistry is not None:
            self._ureg = unit_registry or UnitRegistry()
            if not hasattr(self._ureg, "percent"):
                self._ureg.define("percent = 0.01*count")
        else:
            self._ureg = None

    async def calculate(self, geocode: "GeocodeResult") -> Optional[BuildableSummary]:
        if geocode.parcel_id is None:
            return None

        parcel = await self._session.get(RefParcel, geocode.parcel_id)
        if parcel is None or parcel.area_m2 is None:
            return None

        zone_rows = await self._session.scalars(
            select(RefZoningLayer).where(RefZoningLayer.zone_code.in_(geocode.zoning_codes))
        )
        zones = list(zone_rows)
        attributes: Dict[str, float] = {}
        max_height_m: Optional[float] = None

        for zone in zones:
            attrs = zone.attributes or {}
            if "plot_ratio" in attrs:
                attributes.setdefault("plot_ratio", float(attrs["plot_ratio"]))
            if "max_site_coverage" in attrs:
                attributes.setdefault("max_site_coverage", float(attrs["max_site_coverage"]))
            if "max_height" in attrs:
                max_height_m = self._parse_length(attrs["max_height"], default_unit="meter")
            elif "max_height_m" in attrs:
                max_height_m = float(attrs["max_height_m"])

        area_m2 = float(parcel.area_m2)
        coverage_ratio = attributes.get("max_site_coverage", 0.6)
        plot_ratio = attributes.get("plot_ratio", 2.8)

        allowable_coverage = area_m2 * coverage_ratio
        gross_floor_area = area_m2 * plot_ratio

        metrics = {
            "buildable.site_area_m2": area_m2,
            "buildable.coverage_ratio": coverage_ratio,
            "buildable.allowable_coverage_m2": allowable_coverage,
            "buildable.plot_ratio": plot_ratio,
            "buildable.gross_floor_area_m2": gross_floor_area,
        }
        if max_height_m is not None:
            metrics["buildable.max_height_m"] = max_height_m

        logger.info(
            "buildable_calculation",
            parcel_id=parcel.id,
            coverage_ratio=coverage_ratio,
            plot_ratio=plot_ratio,
            gross_floor_area=gross_floor_area,
        )

        return BuildableSummary(
            parcel_ref=parcel.parcel_ref,
            zoning_codes=geocode.zoning_codes,
            site_area_m2=area_m2,
            allowable_coverage_m2=allowable_coverage,
            gross_floor_area_m2=gross_floor_area,
            max_height_m=max_height_m,
            metrics=metrics,
            provenance={"source": "fixture" if geocode.provenance.get("fixture") else "cache"},
        )

    def _parse_length(self, value: object, default_unit: str = "meter") -> Optional[float]:
        try:
            if self._ureg is not None:
                if isinstance(value, (int, float)):
                    quantity = value * self._ureg(default_unit)
                elif isinstance(value, str):
                    quantity = self._ureg(value)
                else:
                    return None
                return quantity.to(self._ureg.meter).magnitude
            magnitude: float
            unit = default_unit
            if isinstance(value, (int, float)):
                magnitude = float(value)
            elif isinstance(value, str):
                parts = value.strip().split()
                if not parts:
                    return None
                magnitude = float(parts[0])
                if len(parts) > 1:
                    unit = parts[1].lower()
            else:
                return None
            conversion = {"m": 1.0, "meter": 1.0, "meters": 1.0, "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001}
            factor = conversion.get(unit.lower(), 1.0)
            return magnitude * factor
        except Exception:  # pragma: no cover
            return None
