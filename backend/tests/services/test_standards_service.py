"""Tests for material standards service helpers."""

from __future__ import annotations

import pytest

from app.models.rkp import RefMaterialStandard
from app.services import standards


@pytest.mark.asyncio
async def test_upsert_material_standard_creates_and_updates(db_session) -> None:
    payload = {
        "jurisdiction": "SG",
        "standard_code": "SS EN 206",
        "material_type": "concrete",
        "standard_body": "SPRING",
        "property_key": "compressive_strength_mpa",
        "value": "30",
        "unit": "MPa",
        "section": "4.2",
    }

    created = await standards.upsert_material_standard(db_session, payload)
    assert created.value == "30"
    assert created.section == "4.2"

    payload_update = {**payload, "value": "32", "context": {"exposure": "XC1"}}
    updated = await standards.upsert_material_standard(db_session, payload_update)

    assert updated.id == created.id
    assert updated.value == "32"
    assert updated.context == {"exposure": "XC1"}


@pytest.mark.asyncio
async def test_lookup_material_standards_filters(db_session) -> None:
    entries = [
        RefMaterialStandard(
            jurisdiction="SG",
            standard_code="SS EN 206",
            material_type="concrete",
            standard_body="SPRING",
            property_key="compressive_strength_mpa",
            value="32",
        ),
        RefMaterialStandard(
            jurisdiction="SG",
            standard_code="SS EN 10025",
            material_type="steel",
            standard_body="SPRING",
            property_key="yield_strength_mpa",
            value="275",
        ),
    ]
    db_session.add_all(entries)
    await db_session.commit()

    results = await standards.lookup_material_standards(
        db_session, standard_code="SS EN 206"
    )

    assert len(results) == 1
    assert results[0].material_type == "concrete"

    results_by_type = await standards.lookup_material_standards(
        db_session, material_type="steel"
    )
    assert len(results_by_type) == 1
    assert results_by_type[0].standard_code == "SS EN 10025"


@pytest.mark.asyncio
async def test_upsert_with_edition_filter(db_session) -> None:
    """Test upsert_material_standard with edition in payload."""
    payload = {
        "jurisdiction": "SG",
        "standard_code": "SS EN 206",
        "material_type": "concrete",
        "standard_body": "SPRING",
        "property_key": "compressive_strength_mpa",
        "value": "30",
        "unit": "MPa",
        "edition": "2022",
    }

    created = await standards.upsert_material_standard(db_session, payload)
    assert created.edition == "2022"

    # Update the same edition
    payload_update = {**payload, "value": "35"}
    updated = await standards.upsert_material_standard(db_session, payload_update)
    assert updated.id == created.id
    assert updated.value == "35"


@pytest.mark.asyncio
async def test_lookup_with_standard_body_and_section(db_session) -> None:
    """Test lookup_material_standards with standard_body and section filters."""
    entry = RefMaterialStandard(
        jurisdiction="SG",
        standard_code="SS 544",
        material_type="steel",
        standard_body="SPRING",
        property_key="yield_strength",
        value="300",
        section="5.2.1",
    )
    db_session.add(entry)
    await db_session.commit()

    # Filter by standard_body
    results = await standards.lookup_material_standards(
        db_session, standard_body="SPRING"
    )
    assert len(results) >= 1
    assert any(r.standard_body == "SPRING" for r in results)

    # Filter by section
    results_section = await standards.lookup_material_standards(
        db_session, section="5.2.1"
    )
    assert len(results_section) == 1
    assert results_section[0].section == "5.2.1"
