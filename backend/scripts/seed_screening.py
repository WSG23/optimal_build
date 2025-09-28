"""Seed sample screening data for buildable overlays."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import structlog
from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseModel
from app.models.rkp import RefGeocodeCache, RefParcel, RefSource, RefZoningLayer
from sqlalchemy import Column, Integer, String, Table, select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


@dataclass
class SeedSummary:
    """Summary of seeded reference records."""

    parcels: int
    geocode_cache: int
    zoning_layers: int
    sources: int

    def as_dict(self) -> dict[str, int]:
        """Return the summary as a dictionary for logging or testing."""

        return {
            "parcels": self.parcels,
            "geocode_cache": self.geocode_cache,
            "zoning_layers": self.zoning_layers,
            "sources": self.sources,
        }


_SAMPLE_REF_SOURCES: Sequence[dict[str, object]] = (
    {
        "jurisdiction": "SG",
        "authority": "URA",
        "topic": "zoning",
        "doc_title": "URA Master Plan Planning Parameters",
        "landing_url": "https://www.ura.gov.sg/Corporate/Planning/Master-Plan",
        "fetch_kind": "html",
        "update_freq_hint": "biennial",
    },
    {
        "jurisdiction": "SG",
        "authority": "BCA",
        "topic": "building",
        "doc_title": "BCA Building Control Regulations",
        "landing_url": "https://www1.bca.gov.sg/buildsg/bca-codes/building-control-act",
        "fetch_kind": "pdf",
        "update_freq_hint": "annual",
    },
    {
        "jurisdiction": "SG",
        "authority": "SCDF",
        "topic": "fire",
        "doc_title": "SCDF Fire Code 2018",
        "landing_url": "https://www.scdf.gov.sg/home/fire-safety/fire-code",
        "fetch_kind": "pdf",
        "update_freq_hint": "biennial",
    },
    {
        "jurisdiction": "SG",
        "authority": "PUB",
        "topic": "drainage",
        "doc_title": "PUB Code of Practice on Surface Water Drainage",
        "landing_url": "https://www.pub.gov.sg/Documents/COP_SurfaceWaterDrainage.pdf",
        "fetch_kind": "pdf",
        "update_freq_hint": "annual",
    },
)


_SAMPLE_ZONING_LAYERS: Sequence[dict[str, object]] = (
    {
        "jurisdiction": "SG",
        "layer_name": "MasterPlan",
        "zone_code": "R2",
        "attributes": {
            "label": "Residential (R2)",
            "overlays": ["heritage", "daylight"],
            "advisory_hints": [
                "Heritage impact assessment required before façade alterations.",
                "Respect daylight plane controls along the street frontage.",
            ],
        },
        "bounds_json": {
            "type": "Polygon",
            "zone_code": "R2",
            "coordinates": [
                [
                    [103.8495, 1.2988],
                    [103.8506, 1.2991],
                    [103.8504, 1.3002],
                    [103.8492, 1.2998],
                    [103.8495, 1.2988],
                ]
            ],
        },
    },
    {
        "jurisdiction": "SG",
        "layer_name": "MasterPlan",
        "zone_code": "C1",
        "attributes": {
            "label": "Commercial (C1)",
            "overlays": ["airport"],
            "advisory_hints": [
                "Coordinate with CAAS on height limits under the airport safeguarding zone.",
            ],
        },
        "bounds_json": {
            "type": "Polygon",
            "zone_code": "C1",
            "coordinates": [
                [
                    [103.8521, 1.3011],
                    [103.8532, 1.3014],
                    [103.8530, 1.3026],
                    [103.8518, 1.3022],
                    [103.8521, 1.3011],
                ]
            ],
        },
    },
    {
        "jurisdiction": "SG",
        "layer_name": "MasterPlan",
        "zone_code": "B1",
        "attributes": {
            "label": "Business Park (B1)",
            "overlays": ["coastal"],
            "advisory_hints": [
                "Implement coastal flood resilience measures for ground floors.",
                "Consult PUB on shoreline protection obligations.",
            ],
        },
        "bounds_json": {
            "type": "Polygon",
            "zone_code": "B1",
            "coordinates": [
                [
                    [103.8535, 1.3032],
                    [103.8546, 1.3035],
                    [103.8544, 1.3047],
                    [103.8532, 1.3043],
                    [103.8535, 1.3032],
                ]
            ],
        },
    },
)

_SAMPLE_PARCELS: Sequence[dict[str, object]] = (
    {
        "jurisdiction": "SG",
        "parcel_ref": "MK01-01234",
        "bounds_json": {
            "type": "Polygon",
            "zone_code": "R2",
            "coordinates": [
                [
                    [103.8496, 1.2990],
                    [103.8503, 1.2991],
                    [103.8502, 1.2997],
                    [103.8494, 1.2996],
                    [103.8496, 1.2990],
                ]
            ],
        },
        "centroid_lat": 1.2994,
        "centroid_lon": 103.8499,
        "area_m2": 1250.0,
        "source": "sample_loader",
    },
    {
        "jurisdiction": "SG",
        "parcel_ref": "MK02-00021",
        "bounds_json": {
            "type": "Polygon",
            "zone_code": "C1",
            "coordinates": [
                [
                    [103.8523, 1.3015],
                    [103.8529, 1.3017],
                    [103.8527, 1.3021],
                    [103.8521, 1.3019],
                    [103.8523, 1.3015],
                ]
            ],
        },
        "centroid_lat": 1.3018,
        "centroid_lon": 103.8525,
        "area_m2": 980.0,
        "source": "sample_loader",
    },
    {
        "jurisdiction": "SG",
        "parcel_ref": "MK03-04567",
        "bounds_json": {
            "type": "Polygon",
            "zone_code": "B1",
            "coordinates": [
                [
                    [103.8537, 1.3036],
                    [103.8543, 1.3037],
                    [103.8541, 1.3043],
                    [103.8534, 1.3041],
                    [103.8537, 1.3036],
                ]
            ],
        },
        "centroid_lat": 1.3039,
        "centroid_lon": 103.8539,
        "area_m2": 1120.0,
        "source": "sample_loader",
    },
)

_SAMPLE_GEOCODES: Sequence[dict[str, object]] = (
    {
        "address": "123 Example Ave",
        "lat": 1.2994,
        "lon": 103.8499,
        "parcel_ref": "MK01-01234",
        "confidence_score": 0.95,
        "is_verified": True,
    },
    {
        "address": "456 River Road",
        "lat": 1.3018,
        "lon": 103.8525,
        "parcel_ref": "MK02-00021",
        "confidence_score": 0.87,
    },
    {
        "address": "789 Coastal Way",
        "lat": 1.3039,
        "lon": 103.8539,
        "parcel_ref": "MK03-04567",
        "confidence_score": 0.9,
        "is_verified": True,
    },
)


async def ensure_schema() -> None:
    """Ensure all database tables exist prior to seeding."""

    _ensure_stub_tables()
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


def _ensure_stub_tables() -> None:
    """Inject lightweight tables required by foreign keys when absent."""

    if "projects" not in BaseModel.metadata.tables:
        Table(
            "projects",
            BaseModel.metadata,
            Column("id", Integer, primary_key=True),
            Column(
                "name",
                String(120),
                nullable=False,
                server_default=text("'Sample Project'"),
            ),
        )


async def _upsert_ref_sources(session: AsyncSession) -> list[RefSource]:
    sources: list[RefSource] = []
    await session.execute(RefSource.__table__.delete())

    for payload in _SAMPLE_REF_SOURCES:
        source = RefSource(**payload)
        session.add(source)
        sources.append(source)
    await session.flush()
    return sources


async def _upsert_zoning_layers(session: AsyncSession) -> list[RefZoningLayer]:
    layers: list[RefZoningLayer] = []
    for payload in _SAMPLE_ZONING_LAYERS:
        stmt = select(RefZoningLayer).where(
            RefZoningLayer.layer_name == payload["layer_name"],
            RefZoningLayer.zone_code == payload["zone_code"],
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            layers.append(existing)
        else:
            layer = RefZoningLayer(**payload)
            session.add(layer)
            layers.append(layer)
    await session.flush()
    return layers


async def _upsert_parcels(session: AsyncSession) -> list[RefParcel]:
    parcels: list[RefParcel] = []
    for payload in _SAMPLE_PARCELS:
        stmt = select(RefParcel).where(RefParcel.parcel_ref == payload["parcel_ref"])
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            parcels.append(existing)
        else:
            parcel = RefParcel(**payload)
            session.add(parcel)
            parcels.append(parcel)
    await session.flush()
    return parcels


async def _upsert_geocode_entries(
    session: AsyncSession, parcels: Iterable[RefParcel]
) -> list[RefGeocodeCache]:
    parcel_lookup = {parcel.parcel_ref: parcel.id for parcel in parcels}
    geocodes: list[RefGeocodeCache] = []
    missing_parcels: list[str] = []

    for payload in _SAMPLE_GEOCODES:
        entry = dict(payload)
        parcel_ref = entry.pop("parcel_ref", None)
        parcel_id = parcel_lookup.get(parcel_ref) if parcel_ref else None
        if parcel_ref and parcel_id is None:
            missing_parcels.append(parcel_ref)
        entry["parcel_id"] = parcel_id

        stmt = select(RefGeocodeCache).where(
            RefGeocodeCache.address == entry["address"]
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            for key, value in entry.items():
                setattr(existing, key, value)
            geocodes.append(existing)
        else:
            geocode = RefGeocodeCache(**entry)
            session.add(geocode)
            geocodes.append(geocode)

    if missing_parcels:
        raise RuntimeError(
            "Missing parcel references for geocode entries: "
            + ", ".join(sorted(set(missing_parcels)))
        )

    await session.flush()
    return geocodes


async def seed_screening_sample_data(
    session: AsyncSession,
    *,
    commit: bool = True,
) -> SeedSummary:
    """Seed the reference tables required for buildable screening."""

    sources = await _upsert_ref_sources(session)
    zoning_layers = await _upsert_zoning_layers(session)
    parcels = await _upsert_parcels(session)
    geocodes = await _upsert_geocode_entries(session, parcels)

    if commit:
        await session.commit()

    return SeedSummary(
        parcels=len(parcels),
        geocode_cache=len(geocodes),
        zoning_layers=len(zoning_layers),
        sources=len(sources),
    )


async def _cli_main() -> SeedSummary:
    await ensure_schema()
    async with AsyncSessionLocal() as session:
        summary = await seed_screening_sample_data(session, commit=True)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed sample parcels, geocodes, and zoning layers for buildable screening.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> SeedSummary:
    """Entry point for command-line execution."""

    parser = _build_parser()
    parser.parse_args(argv)
    summary = asyncio.run(_cli_main())
    logger.info(
        "seed_screening.summary",
        zoning_layers=summary.zoning_layers,
        parcels=summary.parcels,
        geocode_cache=summary.geocode_cache,
        sources=summary.sources,
    )
    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
