import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

from app.core.config import settings
from app.models.rkp import RefParcel
from app.schemas.buildable import BuildableDefaults
from app.services.buildable import (
    ResolvedZone,
    calculate_buildable,
    load_layers_for_zone,
)
from scripts.seed_screening import seed_screening_sample_data
from sqlalchemy import select

PARCEL_ZONE_CASES = (
    ("MK01-01234", "R2"),
    ("MK02-00021", "C1"),
    ("MK03-04567", "B1"),
)


@pytest.mark.asyncio
async def test_buildable_postgis_flag_consistency(async_session_factory, monkeypatch):
    async with async_session_factory() as session:
        await seed_screening_sample_data(session, commit=True)

    defaults = BuildableDefaults(
        plot_ratio=3.5,
        site_area_m2=1000.0,
        site_coverage=0.45,
        floor_height_m=4.0,
        efficiency_factor=0.82,
    )

    async def _compute_metrics(
        use_postgis: bool, parcel_ref: str, zone_code: str
    ) -> dict:
        monkeypatch.setattr(settings, "BUILDABLE_USE_POSTGIS", use_postgis)
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
                defaults=defaults,
                typ_floor_to_floor_m=4.0,
                efficiency_ratio=0.82,
            )
            return calculation.metrics.model_dump()

    for parcel_ref, zone_code in PARCEL_ZONE_CASES:
        baseline = await _compute_metrics(False, parcel_ref, zone_code)
        with_postgis = await _compute_metrics(True, parcel_ref, zone_code)
        assert with_postgis == baseline
