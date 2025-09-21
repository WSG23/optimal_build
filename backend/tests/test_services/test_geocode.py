from __future__ import annotations

import pytest

from app.services.geocode import GeocodeService


@pytest.mark.asyncio
async def test_geocode_seed_and_lookup(session) -> None:
    service = GeocodeService(session, ttl_hours=-1)
    await service.seed_cache()
    result = await service.geocode("1 Marina Boulevard, Singapore")
    assert result is not None
    assert result.parcel_id is not None
    assert result.zoning_codes
    assert result.provenance["cached"] is False

    fresh_service = GeocodeService(session)
    second = await fresh_service.geocode("1 Marina Boulevard, Singapore")
    assert second is not None
    assert second.provenance["cached"] is False

    cached = await fresh_service.geocode("1 Marina Boulevard, Singapore")
    assert cached is not None
    assert cached.provenance["cached"] is True
