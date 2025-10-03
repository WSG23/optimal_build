"""Helper routines for PostGIS-enabled buildable calculations."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefParcel, RefZoningLayer


def _coerce_float(value: object) -> float | None:
    """Coerce ``value`` into a ``float`` if possible."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


async def parcel_area(session: AsyncSession, parcel: RefParcel | None) -> float | None:
    """Return the parcel area using PostGIS geometry columns when available."""

    if parcel is None:
        return None

    geometry_column = getattr(RefParcel, "geometry", None)
    if geometry_column is None or session is None or parcel.id is None:
        return _coerce_float(getattr(parcel, "area_m2", None))

    stmt: Select[tuple[float | None]] = select(func.ST_Area(geometry_column)).where(
        RefParcel.id == parcel.id
    )
    try:
        area = await session.scalar(stmt)
    except Exception:  # pragma: no cover - falls back when PostGIS isn't available
        return _coerce_float(getattr(parcel, "area_m2", None))

    if area is None:
        return _coerce_float(getattr(parcel, "area_m2", None))

    try:
        return float(area)
    except (TypeError, ValueError):
        return _coerce_float(getattr(parcel, "area_m2", None))


async def load_layers_for_zone(
    session: AsyncSession, zone_code: str
) -> list[RefZoningLayer]:
    """Load zoning layers, ensuring geometry columns are fetched when present."""

    geometry_column = getattr(RefZoningLayer, "geometry", None)
    stmt = select(RefZoningLayer).where(RefZoningLayer.zone_code == zone_code)
    if geometry_column is not None:
        stmt = stmt.add_columns(geometry_column)

    try:
        result = await session.execute(stmt)
    except Exception:  # pragma: no cover - defensive fallback
        # If the geometry column or PostGIS functions aren't available, fall back to
        # the default JSON-backed loader behaviour.
        fallback = select(RefZoningLayer).where(RefZoningLayer.zone_code == zone_code)
        result = await session.execute(fallback)
        return list(result.scalars().all())

    if geometry_column is not None:
        return [row[0] for row in result.all()]
    return list(result.scalars().all())


__all__ = ["load_layers_for_zone", "parcel_area"]


class PostGISService:
    """Convenience façade exposing helper routines as methods."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def parcel_area(self, parcel: RefParcel | None) -> float | None:
        return await parcel_area(self._session, parcel)

    async def load_layers_for_zone(self, zone_code: str) -> list[RefZoningLayer]:
        return await load_layers_for_zone(self._session, zone_code)


__all__ = ["PostGISService", "load_layers_for_zone", "parcel_area"]
