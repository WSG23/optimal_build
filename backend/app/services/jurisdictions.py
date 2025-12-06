"""Jurisdiction registry for currency/unit defaults and engineering parameters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class GFAtoNIABand:
    """Accuracy bands for GFA to NIA conversion."""

    low: float
    mid: float
    high: float


@dataclass(frozen=True)
class EngineeringDefaults:
    """Engineering defaults for a jurisdiction by asset type."""

    floor_to_floor: Mapping[str, float]  # meters or feet depending on jurisdiction
    efficiency_ratio: Mapping[str, float]
    gfa_to_nia_bands: Mapping[str, GFAtoNIABand]
    structural_grid: Mapping[str, float]  # meters or feet
    core_ratio_pct: Mapping[str, float]
    parking_ratio: Mapping[str, float]
    basement_levels_typical: int


@dataclass(frozen=True)
class JurisdictionConfig:
    """Immutable configuration describing a supported jurisdiction."""

    code: str
    name: str
    currency_code: str
    currency_symbol: str
    area_units: str
    rent_metric: str
    market_data: Mapping[str, Any]
    engineering_defaults: Optional[EngineeringDefaults] = None


def _normalise_code(value: str | None) -> str:
    if not value:
        return "SG"
    cleaned = value.strip().upper()
    return cleaned or "SG"


def _parse_engineering_defaults(
    payload: Mapping[str, Any]
) -> Optional[EngineeringDefaults]:
    """Parse engineering defaults from jurisdiction payload."""
    eng = payload.get("engineering_defaults")
    if not eng:
        return None

    # Handle floor_to_floor in meters or feet
    floor_to_floor = eng.get("floor_to_floor_m") or eng.get("floor_to_floor_ft") or {}

    # Parse GFA to NIA bands
    gfa_bands_raw = eng.get("gfa_to_nia_bands", {})
    gfa_bands: dict[str, GFAtoNIABand] = {}
    for asset_type, band in gfa_bands_raw.items():
        if isinstance(band, dict):
            gfa_bands[asset_type] = GFAtoNIABand(
                low=float(band.get("low", 0.75)),
                mid=float(band.get("mid", 0.82)),
                high=float(band.get("high", 0.88)),
            )

    # Handle structural grid in meters or feet
    structural_grid = (
        eng.get("structural_grid_m") or eng.get("structural_grid_ft") or {}
    )

    return EngineeringDefaults(
        floor_to_floor=floor_to_floor,
        efficiency_ratio=eng.get("efficiency_ratio", {}),
        gfa_to_nia_bands=gfa_bands,
        structural_grid=structural_grid,
        core_ratio_pct=eng.get("core_ratio_pct", {}),
        parking_ratio=eng.get("parking_ratio", {}),
        basement_levels_typical=int(eng.get("basement_levels_typical", 2)),
    )


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, JurisdictionConfig]:
    try:
        text = (
            resources.files("app.data")
            .joinpath("jurisdictions.json")
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Missing jurisdiction registry file") from exc
    except OSError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to read jurisdiction registry") from exc

    try:
        raw_registry: Mapping[str, Mapping[str, Any]] = json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Invalid jurisdiction registry JSON") from exc

    registry: dict[str, JurisdictionConfig] = {}
    for raw_code, payload in raw_registry.items():
        code = _normalise_code(str(payload.get("code") or raw_code))
        registry[code] = JurisdictionConfig(
            code=code,
            name=str(payload.get("name", code)),
            currency_code=str(payload.get("currency_code", "SGD")),
            currency_symbol=str(payload.get("currency_symbol", "S$")),
            area_units=str(payload.get("area_units", "sqm")),
            rent_metric=str(payload.get("rent_metric", "psm_month")),
            market_data=payload.get("market_data", {}),
            engineering_defaults=_parse_engineering_defaults(payload),
        )
    if "SG" not in registry:
        registry["SG"] = JurisdictionConfig(
            code="SG",
            name="Singapore",
            currency_code="SGD",
            currency_symbol="S$",
            area_units="sqm",
            rent_metric="psm_month",
            market_data={},
            engineering_defaults=None,
        )
    return registry


def get_jurisdiction_config(code: str | None) -> JurisdictionConfig:
    """Return the configuration for the requested jurisdiction."""

    registry = _load_registry()
    normalised = _normalise_code(code)
    return registry.get(normalised, registry["SG"])


def get_engineering_defaults(
    code: str | None, asset_type: str = "residential"
) -> dict[str, Any]:
    """Get engineering defaults for a jurisdiction and asset type.

    Returns a dictionary with:
    - floor_to_floor: Floor-to-floor height (meters or feet)
    - efficiency_ratio: GFA to NIA efficiency ratio
    - gfa_to_nia_band: Low/mid/high accuracy bands
    - structural_grid: Typical structural grid spacing
    - core_ratio_pct: Core area as percentage of GFA
    - parking_ratio: Parking spaces per unit/1000sqft
    - basement_levels_typical: Typical basement levels
    """
    config = get_jurisdiction_config(code)
    defaults = config.engineering_defaults

    if not defaults:
        # Return sensible defaults if no engineering data available
        return {
            "floor_to_floor": 3.5,
            "efficiency_ratio": 0.82,
            "gfa_to_nia_band": {"low": 0.75, "mid": 0.82, "high": 0.88},
            "structural_grid": 9.0,
            "core_ratio_pct": 15.0,
            "parking_ratio": 1.0,
            "basement_levels_typical": 2,
            "area_units": config.area_units,
        }

    asset_key = asset_type.lower().replace("-", "_").replace(" ", "_")

    # Get the GFA to NIA band for the asset type
    gfa_band = defaults.gfa_to_nia_bands.get(asset_key)
    gfa_band_dict = (
        {"low": gfa_band.low, "mid": gfa_band.mid, "high": gfa_band.high}
        if gfa_band
        else {"low": 0.75, "mid": 0.82, "high": 0.88}
    )

    return {
        "floor_to_floor": defaults.floor_to_floor.get(asset_key, 3.5),
        "efficiency_ratio": defaults.efficiency_ratio.get(asset_key, 0.82),
        "gfa_to_nia_band": gfa_band_dict,
        "structural_grid": defaults.structural_grid.get(asset_key, 9.0),
        "core_ratio_pct": defaults.core_ratio_pct.get(asset_key, 15.0),
        "parking_ratio": defaults.parking_ratio.get(asset_key, 1.0),
        "basement_levels_typical": defaults.basement_levels_typical,
        "area_units": config.area_units,
    }


def get_all_jurisdictions() -> list[dict[str, Any]]:
    """Return a list of all supported jurisdictions with their details."""
    registry = _load_registry()
    return [
        {
            "code": config.code,
            "name": config.name,
            "currency_code": config.currency_code,
            "currency_symbol": config.currency_symbol,
            "area_units": config.area_units,
        }
        for config in registry.values()
    ]


__all__ = [
    "JurisdictionConfig",
    "EngineeringDefaults",
    "GFAtoNIABand",
    "get_jurisdiction_config",
    "get_engineering_defaults",
    "get_all_jurisdictions",
]
