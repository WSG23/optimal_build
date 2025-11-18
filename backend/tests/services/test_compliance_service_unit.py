"""Unit-style tests for the ComplianceService with a stubbed compliance engine."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

import pytest_asyncio
from app.models.compliance import ComplianceStatus
from app.models.singapore_property import (
    PropertyTenure,
    PropertyZoning,
    SingaporeProperty,
)
from app.services import compliance as compliance_service
from app.services.compliance import ComplianceService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def _persist_property(
    session_factory: async_sessionmaker[AsyncSession],
    **overrides,
) -> SingaporeProperty:
    async with session_factory() as session:
        record = SingaporeProperty(
            property_name=overrides.get("property_name", "Stub Residences"),
            address=overrides.get("address", "88 Test Avenue"),
            zoning=overrides.get("zoning", PropertyZoning.RESIDENTIAL),
            tenure=overrides.get("tenure", PropertyTenure.FREEHOLD),
        )
        session.add(record)
        await session.flush()
        await session.commit()
        return record


async def _stubbed_update(record: SingaporeProperty, _) -> SingaporeProperty:
    record.bca_compliance_status = ComplianceStatus.PASSED
    record.ura_compliance_status = ComplianceStatus.WARNING
    record.compliance_notes = "stubbed"
    record.compliance_data = {"checked": True}
    record.compliance_last_checked = datetime.now(timezone.utc)
    return record


@pytest_asyncio.fixture(autouse=True)
async def _patch_update(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        compliance_service,
        "update_property_compliance",
        _stubbed_update,
        raising=True,
    )
    yield


@pytest.mark.asyncio
async def test_run_for_property_returns_compliance_result(async_session_factory):
    stored = await _persist_property(async_session_factory)
    service = ComplianceService(async_session_factory)

    result = await service.run_for_property(stored.id)

    assert result.response.property_id == stored.id
    assert result.response.compliance.bca_status == "passed"
    assert result.response.compliance.ura_status == "warning"
    assert result.response.compliance.notes == "stubbed"


@pytest.mark.asyncio
async def test_run_for_property_missing_raises(async_session_factory):
    service = ComplianceService(async_session_factory)
    missing_id = uuid4()

    with pytest.raises(ValueError, match=str(missing_id)):
        await service.run_for_property(missing_id)


@pytest.mark.asyncio
async def test_run_batch_filters_by_ids(async_session_factory):
    property_a = await _persist_property(async_session_factory, property_name="Tower A")
    await _persist_property(async_session_factory, property_name="Tower B")

    service = ComplianceService(async_session_factory)
    results = await service.run_batch(property_ids=[property_a.id])

    assert [result.response.property_id for result in results] == [property_a.id]


@pytest.mark.asyncio
async def test_run_batch_applies_limit(async_session_factory):
    await _persist_property(async_session_factory, property_name="One")
    await _persist_property(async_session_factory, property_name="Two")
    await _persist_property(async_session_factory, property_name="Three")

    service = ComplianceService(async_session_factory)
    limited = await service.run_batch(limit=2)

    assert len(limited) <= 2
