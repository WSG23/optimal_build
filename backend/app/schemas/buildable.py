"""Pydantic schemas for buildable screening."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Mapping, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings


class BuildableDefaults(BaseModel):
    """Default assumptions for buildable calculations."""

    plot_ratio: float = Field(default=3.5, gt=0)
    site_area_m2: float = Field(default=1000.0, gt=0)
    site_coverage: float = Field(default=0.45, gt=0)
    floor_height_m: float = Field(
        default=settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M, gt=0
    )
    efficiency_factor: float = Field(
        default=settings.BUILDABLE_EFFICIENCY_RATIO, gt=0
    )

    @field_validator("site_coverage")
    @classmethod
    def _normalise_site_coverage(cls, value: float) -> float:
        """Allow site coverage to be provided as a fraction or percentage."""

        if value > 1:
            value = value / 100.0
        return max(0.0, min(value, 1.0))

    @field_validator("efficiency_factor")
    @classmethod
    def _limit_efficiency(cls, value: float) -> float:
        """Ensure efficiency factor stays within a 0-1 range."""

        return max(0.0, min(value, 1.0))


class BuildableRequest(BaseModel):
    """Request payload for buildable screening."""

    address: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    project_type: Optional[str] = None
    defaults: BuildableDefaults = Field(default_factory=BuildableDefaults)
    typ_floor_to_floor_m: Optional[float] = Field(
        default=settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M, gt=0
    )
    efficiency_ratio: Optional[float] = Field(
        default=settings.BUILDABLE_EFFICIENCY_RATIO, gt=0
    )

    @classmethod
    def model_validate(
        cls, obj: Any, *args: Any, **kwargs: Any
    ) -> "BuildableRequest":
        """Normalise known camelCase keys before delegating to Pydantic."""

        if isinstance(obj, Mapping):
            data = dict(obj)
            aliases = {
                "typFloorToFloorM": "typ_floor_to_floor_m",
                "efficiencyRatio": "efficiency_ratio",
                "defaults": "defaults",
            }
            for alias, field_name in aliases.items():
                if alias in data and field_name not in data:
                    data[field_name] = data.pop(alias)

            defaults_value = data.get("defaults")
            if isinstance(defaults_value, Mapping):
                defaults_aliases = {
                    "plotRatio": "plot_ratio",
                    "siteAreaM2": "site_area_m2",
                    "siteCoverage": "site_coverage",
                    "floorHeightM": "floor_height_m",
                    "efficiencyFactor": "efficiency_factor",
                }
                normalised_defaults = dict(defaults_value)
                for alias, field_name in defaults_aliases.items():
                    if alias in normalised_defaults and field_name not in normalised_defaults:
                        normalised_defaults[field_name] = normalised_defaults.pop(alias)
                data["defaults"] = normalised_defaults

            obj = data

        return super().model_validate(obj, *args, **kwargs)

    @field_validator("geometry")
    @classmethod
    def _ensure_geojson_dict(cls, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Only accept dictionaries for GeoJSON payloads."""

        if value is None:
            return None
        if not isinstance(value, dict):
            raise TypeError("geometry must be a GeoJSON feature dictionary")
        return value

    @field_validator("address")
    @classmethod
    def _strip_address(cls, value: Optional[str]) -> Optional[str]:
        """Normalise the address string."""

        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("project_type")
    @classmethod
    def _strip_project_type(cls, value: Optional[str]) -> Optional[str]:
        """Normalise the project type string."""

        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("efficiency_ratio")
    @classmethod
    def _limit_efficiency_ratio(cls, value: Optional[float]) -> Optional[float]:
        """Ensure the efficiency ratio remains within a sensible range."""

        if value is None:
            return None
        return max(0.0, min(value, 1.0)) or None

    @model_validator(mode="after")
    def _require_location(cls, instance: "BuildableRequest") -> "BuildableRequest":
        """Ensure an address or geometry payload is supplied."""

        if not instance.address and not instance.geometry:
            raise ValueError("Either address or geometry must be provided")
        return instance


class BuildableMetrics(BaseModel):
    """Calculated buildable metrics for the site."""

    gfa_cap_m2: int
    floors_max: int
    footprint_m2: int
    nsa_est_m2: int


class BuildableRuleProvenance(BaseModel):
    """Provenance information for a rule."""

    rule_id: int
    clause_ref: Optional[str] = None
    document_id: Optional[int] = None
    pages: Optional[List[int]] = None
    seed_tag: Optional[str] = None


class BuildableRule(BaseModel):
    """Rule entry surfaced in buildable screening."""

    id: int
    authority: str
    parameter_key: str
    operator: str
    value: str
    unit: Optional[str] = None
    provenance: BuildableRuleProvenance


class ZoneSource(BaseModel):
    """Metadata describing the source of the zoning information."""

    kind: Literal["parcel", "geometry", "unknown"]
    layer_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    parcel_ref: Optional[str] = None
    parcel_source: Optional[str] = None
    note: Optional[str] = None


class BuildableCalculation(BaseModel):
    """Intermediate calculation payload returned by the service."""

    metrics: BuildableMetrics
    zone_source: ZoneSource
    rules: List[BuildableRule]


class BuildableResponse(BaseModel):
    """Response payload returned by the buildable screening endpoint."""

    input_kind: Literal["address", "geometry"]
    zone_code: Optional[str] = None
    overlays: List[str]
    advisory_hints: List[str]
    metrics: BuildableMetrics
    zone_source: ZoneSource
    rules: List[BuildableRule]


__all__ = [
    "BuildableCalculation",
    "BuildableDefaults",
    "BuildableMetrics",
    "BuildableRequest",
    "BuildableResponse",
    "BuildableRule",
    "BuildableRuleProvenance",
    "ZoneSource",
]
