"""Schemas for screening endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class BuildableResponse(BaseModel):
    address: str
    parcel_ref: Optional[str]
    zoning_codes: List[str]
    site_area_m2: float
    allowable_coverage_m2: float
    gross_floor_area_m2: float
    max_height_m: Optional[float]
    metrics: Dict[str, float]
    provenance: Dict[str, str]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[Dict[str, object]]
