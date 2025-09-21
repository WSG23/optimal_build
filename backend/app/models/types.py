"""Utility SQLAlchemy types with PostGIS fallbacks."""

from __future__ import annotations

import importlib.util
import os
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.sql.type_api import TypeEngine

_JSONB_SPEC = importlib.util.find_spec("sqlalchemy.dialects.postgresql")
if _JSONB_SPEC is not None:
    from sqlalchemy.dialects.postgresql import JSONB as _PGJSONB  # type: ignore
else:
    _PGJSONB = None  # type: ignore

_GEO_SPEC = importlib.util.find_spec("geoalchemy2")
if _GEO_SPEC is not None:
    from geoalchemy2 import Geometry as _GeoGeometry  # type: ignore
else:
    _GeoGeometry = None  # type: ignore


def jsonb_type() -> TypeEngine[Any]:
    """Return a JSON-capable type with PostgreSQL JSONB when available."""

    if os.getenv("SQLALCHEMY_DISABLE_JSONB", "").lower() in {"1", "true", "yes"}:
        return JSON

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        try:  # Avoid circular imports when models load early.
            from app.core.config import settings  # type: ignore import
        except Exception:  # pragma: no cover - defensive fallback
            database_url = ""
        else:
            database_url = settings.SQLALCHEMY_DATABASE_URI

    use_jsonb = bool(database_url and database_url.startswith("postgresql"))
    if use_jsonb and _PGJSONB is not None:
        return _PGJSONB
    return JSON


def geometry_type(geometry: str = "GEOMETRY", srid: int = 4326) -> TypeEngine[Any]:
    """Return a geometry type or a GeoJSON text fallback."""

    if _GeoGeometry is not None:
        return _GeoGeometry(geometry_type=geometry, srid=srid)  # type: ignore[arg-type]
    return JSON


__all__ = ["jsonb_type", "geometry_type"]
