import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.models.rkp import RefParcel
from backend.app.schemas.buildable import BuildableDefaults
from backend.app.services.buildable import (
    ResolvedZone,
    calculate_buildable,
    load_layers_for_zone,
)
from backend.scripts.seed_screening import seed_screening_sample_data


PARCEL_ZONE_CASES: tuple[tuple[str, str], ...] = (
    ("MK01-01234", "R2"),
    ("MK02-00021", "C1"),
    ("MK03-04567", "B1"),
)

DEFAULTS = BuildableDefaults(
    plot_ratio=3.5,
    site_area_m2=1000.0,
    site_coverage=0.45,
    floor_height_m=4.0,
    efficiency_factor=0.82,
)


async def _parcel_metrics(
    async_session_factory,
    use_postgis: bool,
    parcel_ref: str,
    zone_code: str,
) -> dict[str, int]:
    previous_flag = settings.BUILDABLE_USE_POSTGIS
    settings.BUILDABLE_USE_POSTGIS = use_postgis
    try:
        async with async_session_factory() as session:
            parcel = (
                await session.execute(
                    select(RefParcel).where(RefParcel.parcel_ref == parcel_ref)
                )
            ).scalar_one()
            layers = await load_layers_for_zone(session, zone_code)
            resolved = ResolvedZone(
                zone_code=zone_code,
                parcel=parcel,
                zone_layers=layers,
                input_kind="address",
            )
            calculation = await calculate_buildable(
                session=session,
                resolved=resolved,
                defaults=DEFAULTS,
                typ_floor_to_floor_m=DEFAULTS.floor_height_m,
                efficiency_ratio=DEFAULTS.efficiency_factor,
            )
        return calculation.metrics.model_dump()
    finally:
        settings.BUILDABLE_USE_POSTGIS = previous_flag


async def test_postgis_flag_produces_identical_metrics(async_session_factory) -> None:
    async with async_session_factory() as session:
        await seed_screening_sample_data(session, commit=True)

    original_flag = settings.BUILDABLE_USE_POSTGIS
    try:
        for parcel_ref, zone_code in PARCEL_ZONE_CASES:
            baseline = await _parcel_metrics(
                async_session_factory, False, parcel_ref, zone_code
            )
            with_postgis = await _parcel_metrics(
                async_session_factory, True, parcel_ref, zone_code
            )
            assert with_postgis == baseline
    finally:
        settings.BUILDABLE_USE_POSTGIS = original_flag
