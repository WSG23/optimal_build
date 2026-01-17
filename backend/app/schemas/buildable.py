"""Pydantic schemas for buildable screening."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from app.core.config import settings

_BUILDABLE_DEFAULTS_EXAMPLE = {
    "plot_ratio": 3.5,
    "site_area_m2": 1000.0,
    "site_coverage": 0.45,
    "floor_height_m": 4.0,
    "efficiency_factor": 0.82,
}


_BUILDABLE_REQUEST_EXAMPLE = {
    "address": "string",
    "geometry": {"string": None},
    "project_type": "string",
    "defaults": _BUILDABLE_DEFAULTS_EXAMPLE,
    "typ_floor_to_floor_m": 4.0,
    "efficiency_ratio": 0.82,
}


_BUILDABLE_RESPONSE_EXAMPLE = {
    "input_kind": "address",
    "zone_code": "string",
    "overlays": ["string"],
    "advisory_hints": ["string"],
    "metrics": {
        "gfa_cap_m2": 0,
        "floors_max": 0,
        "footprint_m2": 0,
        "nsa_est_m2": 0,
    },
    "zone_source": {
        "kind": "parcel",
        "layer_name": "string",
        "jurisdiction": "string",
        "parcel_ref": "string",
        "parcel_source": "string",
        "note": "string",
    },
    "rules": [
        {
            "id": 0,
            "authority": "string",
            "parameter_key": "string",
            "operator": "string",
            "value": "string",
            "unit": "string",
            "provenance": {
                "rule_id": 0,
                "clause_ref": "string",
                "document_id": 0,
                "pages": [0],
                "seed_tag": "string",
            },
        }
    ],
}

BUILDABLE_REQUEST_EXAMPLE = _BUILDABLE_REQUEST_EXAMPLE
BUILDABLE_RESPONSE_EXAMPLE = _BUILDABLE_RESPONSE_EXAMPLE


class BuildableDefaults(BaseModel):
    """Default assumptions for buildable calculations."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": _BUILDABLE_DEFAULTS_EXAMPLE},
    )

    plot_ratio: float = Field(default=3.5, gt=0, alias="plotRatio")
    site_area_m2: float = Field(default=1000.0, gt=0, alias="siteAreaM2")
    site_coverage: float = Field(default=0.45, gt=0, alias="siteCoverage")
    floor_height_m: float = Field(
        default=settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M,
        gt=0,
        alias="floorHeightM",
    )
    efficiency_factor: float = Field(
        default=settings.BUILDABLE_EFFICIENCY_RATIO,
        gt=0,
        alias="efficiencyFactor",
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

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": _BUILDABLE_REQUEST_EXAMPLE},
    )

    address: str | None = None
    geometry: dict[str, Any] | None = None
    project_type: str | None = None
    defaults: BuildableDefaults = Field(
        default_factory=BuildableDefaults, alias="defaults"
    )
    typ_floor_to_floor_m: float | None = Field(
        default=settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M,
        gt=0,
        alias="typFloorToFloorM",
    )
    efficiency_ratio: float | None = Field(
        default=settings.BUILDABLE_EFFICIENCY_RATIO,
        gt=0,
        alias="efficiencyRatio",
    )

    @field_validator("geometry")
    @classmethod
    def _ensure_geojson_dict(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Only accept dictionaries for GeoJSON payloads."""

        if value is None:
            return None
        if not isinstance(value, dict):
            raise TypeError("geometry must be a GeoJSON feature dictionary")
        return value

    @field_validator("address")
    @classmethod
    def _strip_address(cls, value: str | None) -> str | None:
        """Normalise the address string."""

        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("project_type")
    @classmethod
    def _strip_project_type(cls, value: str | None) -> str | None:
        """Normalise the project type string."""

        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("efficiency_ratio")
    @classmethod
    def _limit_efficiency_ratio(cls, value: float | None) -> float | None:
        """Ensure the efficiency ratio remains within a sensible range."""

        if value is None:
            return None
        return max(0.0, min(value, 1.0)) or None

    @model_validator(mode="after")
    def _require_location(cls, instance: BuildableRequest) -> BuildableRequest:
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
    clause_ref: str | None = None
    document_id: int | None = None
    pages: list[int] | None = None
    seed_tag: str | None = None


class BuildableRule(BaseModel):
    """Rule entry surfaced in buildable screening."""

    id: int
    authority: str
    parameter_key: str
    operator: str
    value: str
    unit: str | None = None
    provenance: BuildableRuleProvenance


class ZoneSource(BaseModel):
    """Metadata describing the source of the zoning information."""

    kind: Literal["parcel", "geometry", "unknown"]
    layer_name: str | None = None
    jurisdiction: str | None = None
    parcel_ref: str | None = None
    parcel_source: str | None = None
    note: str | None = None


class BuildableCalculation(BaseModel):
    """Intermediate calculation payload returned by the service."""

    metrics: BuildableMetrics
    zone_source: ZoneSource
    rules: list[BuildableRule]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def gfa_total(self) -> float:
        """Total gross floor area permitted by the calculation."""
        return float(self.metrics.gfa_cap_m2)


class BuildableResponse(BaseModel):
    """Response payload returned by the buildable screening endpoint."""

    model_config = ConfigDict(
        json_schema_extra={"example": _BUILDABLE_RESPONSE_EXAMPLE}
    )

    input_kind: Literal["address", "geometry"]
    zone_code: str | None = None
    overlays: list[str]
    advisory_hints: list[str]
    metrics: BuildableMetrics
    zone_source: ZoneSource
    rules: list[BuildableRule]


__all__ = [
    "BUILDABLE_REQUEST_EXAMPLE",
    "BUILDABLE_RESPONSE_EXAMPLE",
    "BuildableCalculation",
    "BuildableDefaults",
    "BuildableMetrics",
    "BuildableRequest",
    "BuildableResponse",
    "BuildableRule",
    "BuildableRuleProvenance",
    "ZoneSource",
]
