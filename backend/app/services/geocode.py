"""Geocoding helpers with deterministic fixtures and caching."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.utils.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefGeocodeCache, RefParcel, RefZoningLayer

logger = get_logger(__name__)

DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "geocode_samples.json"


@dataclass
class GeocodeResult:
    """Normalized geocode result returned by the adapter and service."""

    address: str
    lat: float
    lon: float
    confidence: float
    parcel_id: Optional[int]
    zoning_codes: List[str]
    provenance: Dict[str, Any]


class FixtureGeocoder:
    """Deterministic adapter that returns results from JSON fixtures."""

    def __init__(self, fixture_path: Path = DEFAULT_FIXTURE_PATH) -> None:
        self._fixture_path = fixture_path
        with fixture_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self._parcel = payload["parcel"]
        self._addresses = {entry["address"].lower(): entry for entry in payload["addresses"]}

    @property
    def parcel(self) -> Dict[str, Any]:
        return self._parcel

    def addresses(self) -> Iterable[str]:
        return self._addresses.keys()

    def lookup(self, address: str) -> Optional[Dict[str, Any]]:
        return self._addresses.get(address.lower())


class GeocodeService:
    """Service that manages the cache and parcel/zoning joins."""

    def __init__(self, session: AsyncSession, adapter: Optional[FixtureGeocoder] = None, *, ttl_hours: int = 24) -> None:
        self._session = session
        self._adapter = adapter or FixtureGeocoder()
        self._ttl = timedelta(hours=ttl_hours)

    async def seed_cache(self) -> None:
        """Seed parcels, zoning layers, and cache entries from the fixture file."""

        parcel_payload = self._adapter.parcel
        parcel_ref = parcel_payload["parcel_ref"]

        parcel = await self._session.scalar(
            select(RefParcel).where(RefParcel.parcel_ref == parcel_ref)
        )
        if parcel is None:
            parcel = RefParcel(
                jurisdiction=parcel_payload.get("jurisdiction", "SG"),
                parcel_ref=parcel_ref,
                geometry=parcel_payload.get("geometry"),
                bounds_json=parcel_payload.get("geometry"),
                centroid_lat=Decimal(str(parcel_payload["centroid"][1])),
                centroid_lon=Decimal(str(parcel_payload["centroid"][0])),
                area_m2=Decimal(str(parcel_payload["area_m2"])),
                source="fixture",
            )
            self._session.add(parcel)
            await self._session.flush()

        for zone in parcel_payload.get("zoning_layers", []):
            existing_zone = await self._session.scalar(
                select(RefZoningLayer).where(RefZoningLayer.zone_code == zone["zone_code"])
            )
            if existing_zone is None:
                effective = zone.get("effective_date")
                effective_date = (
                    datetime.fromisoformat(effective) if effective else datetime.utcnow()
                )
                self._session.add(
                    RefZoningLayer(
                        jurisdiction=zone.get("jurisdiction", "SG"),
                        layer_name=zone.get("layer_name", "Fixture"),
                        zone_code=zone["zone_code"],
                        attributes=zone.get("attributes", {}),
                        geometry=zone.get("geometry"),
                        bounds_json=zone.get("geometry"),
                        effective_date=effective_date,
                        expiry_date=None,
                    )
                )

        await self._session.flush()

        for address_key in self._adapter.addresses():
            payload = self._adapter.lookup(address_key)
            if payload is None:
                continue
            await self._upsert_cache_entry(address_key, payload, parcel)

        await self._session.commit()

    async def geocode(self, address: str) -> Optional[GeocodeResult]:
        """Geocode an address, storing and retrieving from the cache."""

        normalized = address.strip().lower()
        if not normalized:
            return None

        cached = await self._session.scalar(
            select(RefGeocodeCache).where(RefGeocodeCache.address == normalized)
        )
        if cached and (cached.cache_expires_at is None or cached.cache_expires_at > datetime.utcnow()):
            logger.info("cache_hit", address=address)
            zoning_codes = await self._zoning_codes_for_parcel(cached.parcel_id)
            return GeocodeResult(
                address=address,
                lat=float(cached.lat) if cached.lat is not None else 0.0,
                lon=float(cached.lon) if cached.lon is not None else 0.0,
                confidence=float(cached.confidence_score or 0),
                parcel_id=cached.parcel_id,
                zoning_codes=zoning_codes,
                provenance={"cached": True},
            )

        payload = self._adapter.lookup(address)
        if payload is None:
            logger.warning("geocode_miss", address=address)
            return None

        parcel_ref = payload.get("parcel_ref")
        parcel = None
        if parcel_ref:
            parcel = await self._session.scalar(
                select(RefParcel).where(RefParcel.parcel_ref == parcel_ref)
            )
        result = await self._upsert_cache_entry(normalized, payload, parcel)
        zoning_codes = await self._zoning_codes_for_parcel(result.parcel_id)
        return GeocodeResult(
            address=address,
            lat=result.lat,
            lon=result.lon,
            confidence=result.confidence,
            parcel_id=result.parcel_id,
            zoning_codes=zoning_codes,
            provenance={"cached": False, "fixture": True},
        )

    async def _upsert_cache_entry(
        self,
        normalized_address: str,
        payload: Dict[str, Any],
        parcel: Optional[RefParcel],
    ) -> GeocodeResult:
        expiration = datetime.utcnow() + self._ttl
        lat = float(payload["lat"])
        lon = float(payload["lon"])
        confidence = float(payload.get("confidence", 0.9))

        cache = await self._session.scalar(
            select(RefGeocodeCache).where(RefGeocodeCache.address == normalized_address)
        )
        if cache is None:
            cache = RefGeocodeCache(address=normalized_address)
            self._session.add(cache)

        cache.lat = Decimal(str(lat))
        cache.lon = Decimal(str(lon))
        cache.confidence_score = Decimal(str(confidence))
        cache.parcel = parcel
        cache.cache_expires_at = expiration
        cache.is_verified = True

        await self._session.flush()

        logger.info("cache_update", address=normalized_address, parcel_id=cache.parcel_id)
        return GeocodeResult(
            address=normalized_address,
            lat=lat,
            lon=lon,
            confidence=confidence,
            parcel_id=cache.parcel_id,
            zoning_codes=[],
            provenance={"cached": True},
        )

    async def _zoning_codes_for_parcel(self, parcel_id: Optional[int]) -> List[str]:
        if parcel_id is None:
            return []
        parcel = await self._session.get(RefParcel, parcel_id)
        if parcel is None:
            return []
        zones = await self._session.scalars(select(RefZoningLayer))
        results: List[str] = []
        for zone in zones:
            attrs = zone.attributes or {}
            parcel_refs = attrs.get("parcel_refs") if isinstance(attrs, dict) else None
            if parcel_refs is None or parcel.parcel_ref in parcel_refs:
                results.append(zone.zone_code)
        return list(dict.fromkeys(results))
