"""Buildable envelope calculation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional


_DECIMAL_ONE = Decimal("1")
_DECIMAL_TWO_PLACES = Decimal("0.01")


def _round_half_up(value: float) -> int:
    """Round positive values using the half-up strategy."""

    return int(Decimal(value).quantize(_DECIMAL_ONE, rounding=ROUND_HALF_UP))


def _round_height(value: float) -> float:
    """Round height measurements to two decimal places."""

    return float(Decimal(value).quantize(_DECIMAL_TWO_PLACES, rounding=ROUND_HALF_UP))


@dataclass(slots=True)
class BuildableMetrics:
    """Summary of buildable area calculations."""

    site_area_sqm: float
    plot_ratio: float
    assumed_floorplate_sqm: float
    gross_floor_area_sqm: int
    net_floor_area_sqm: int
    estimated_storeys: int
    estimated_height_m: float
    efficiency_ratio: float
    typ_floor_to_floor_m: float

    def as_dict(self) -> Dict[str, float | int]:
        """Serialise the metrics for API responses."""

        return {
            "site_area_sqm": self.site_area_sqm,
            "plot_ratio": self.plot_ratio,
            "assumed_floorplate_sqm": self.assumed_floorplate_sqm,
            "gross_floor_area_sqm": self.gross_floor_area_sqm,
            "net_floor_area_sqm": self.net_floor_area_sqm,
            "estimated_storeys": self.estimated_storeys,
            "estimated_height_m": self.estimated_height_m,
            "efficiency_ratio": self.efficiency_ratio,
            "typ_floor_to_floor_m": self.typ_floor_to_floor_m,
        }


def calculate_buildable_metrics(
    *,
    site_area_sqm: float,
    plot_ratio: float,
    efficiency_ratio: float,
    typ_floor_to_floor_m: float,
    floorplate_sqm: Optional[float] = None,
    max_height_m: Optional[float] = None,
) -> BuildableMetrics:
    """Calculate buildable area metrics for the supplied parameters."""

    if site_area_sqm <= 0:
        raise ValueError("site_area_sqm must be positive")
    if plot_ratio <= 0:
        raise ValueError("plot_ratio must be positive")
    if efficiency_ratio <= 0:
        raise ValueError("efficiency_ratio must be positive")
    if typ_floor_to_floor_m <= 0:
        raise ValueError("typ_floor_to_floor_m must be positive")

    floorplate = floorplate_sqm if floorplate_sqm and floorplate_sqm > 0 else site_area_sqm

    gross_floor_area = site_area_sqm * plot_ratio
    storeys_by_gfa = max(1, _round_half_up(gross_floor_area / floorplate))

    if max_height_m is not None and max_height_m > 0:
        height_based_storeys = max(1, int(max_height_m / typ_floor_to_floor_m))
        estimated_storeys = min(storeys_by_gfa, height_based_storeys)
    else:
        estimated_storeys = storeys_by_gfa

    achievable_gross = min(gross_floor_area, estimated_storeys * floorplate)
    gross_int = _round_half_up(achievable_gross)
    net_int = _round_half_up(achievable_gross * efficiency_ratio)
    estimated_height = _round_height(estimated_storeys * typ_floor_to_floor_m)

    return BuildableMetrics(
        site_area_sqm=float(site_area_sqm),
        plot_ratio=float(plot_ratio),
        assumed_floorplate_sqm=float(floorplate),
        gross_floor_area_sqm=gross_int,
        net_floor_area_sqm=net_int,
        estimated_storeys=estimated_storeys,
        estimated_height_m=estimated_height,
        efficiency_ratio=float(efficiency_ratio),
        typ_floor_to_floor_m=float(typ_floor_to_floor_m),
    )


__all__ = ["BuildableMetrics", "calculate_buildable_metrics"]
