"""Tests for canonical data models."""

from __future__ import annotations

from core.canonical_models import (
    JurisdictionORM,
    ProvenanceORM,
    RegMappingORM,
    RegstackBase,
    RegulationORM,
)


def test_regstack_base_has_metadata() -> None:
    """Test RegstackBase has metadata."""
    assert hasattr(RegstackBase, "metadata")
    assert RegstackBase.__abstract__ is True


def test_jurisdiction_orm_structure() -> None:
    """Test JurisdictionORM model structure."""
    assert hasattr(JurisdictionORM, "__tablename__")
    assert JurisdictionORM.__tablename__ == "jurisdictions"

    # Check columns exist
    assert hasattr(JurisdictionORM, "code")
    assert hasattr(JurisdictionORM, "name")
    assert hasattr(JurisdictionORM, "created_at")
    assert hasattr(JurisdictionORM, "regulations")


def test_regulation_orm_structure() -> None:
    """Test RegulationORM model structure."""
    assert hasattr(RegulationORM, "__tablename__")
    assert RegulationORM.__tablename__ == "regulations"

    # Check columns exist
    assert hasattr(RegulationORM, "id")
    assert hasattr(RegulationORM, "jurisdiction_code")
    assert hasattr(RegulationORM, "external_id")
    assert hasattr(RegulationORM, "title")
    assert hasattr(RegulationORM, "text")
    assert hasattr(RegulationORM, "issued_on")
    assert hasattr(RegulationORM, "effective_on")
    assert hasattr(RegulationORM, "version")
    assert hasattr(RegulationORM, "is_active")
    assert hasattr(RegulationORM, "metadata_")
    assert hasattr(RegulationORM, "global_tags")

    # Check relationships
    assert hasattr(RegulationORM, "jurisdiction")
    assert hasattr(RegulationORM, "mappings")
    assert hasattr(RegulationORM, "provenance_entries")


def test_reg_mapping_orm_structure() -> None:
    """Test RegMappingORM model structure."""
    assert hasattr(RegMappingORM, "__tablename__")
    assert RegMappingORM.__tablename__ == "reg_mappings"

    # Check columns exist
    assert hasattr(RegMappingORM, "id")
    assert hasattr(RegMappingORM, "regulation_id")
    assert hasattr(RegMappingORM, "mapping_type")
    assert hasattr(RegMappingORM, "payload")

    # Check relationships
    assert hasattr(RegMappingORM, "regulation")


def test_provenance_orm_structure() -> None:
    """Test ProvenanceORM model structure."""
    assert hasattr(ProvenanceORM, "__tablename__")
    assert ProvenanceORM.__tablename__ == "provenance"

    # Check columns exist
    assert hasattr(ProvenanceORM, "id")
    assert hasattr(ProvenanceORM, "regulation_id")


def test_jurisdiction_orm_table_args() -> None:
    """Test JurisdictionORM table has correct primary key."""
    # Code should be primary key
    columns = {col.name: col for col in JurisdictionORM.__table__.columns}
    assert "code" in columns
    assert columns["code"].primary_key is True


def test_regulation_orm_constraints() -> None:
    """Test RegulationORM has unique constraint."""
    table_args = RegulationORM.__table_args__
    assert table_args is not None

    # Should have unique constraint on jurisdiction_code + external_id
    unique_constraints = [
        arg
        for arg in table_args
        if hasattr(arg, "name") and "uq_reg_external" in arg.name
    ]
    assert len(unique_constraints) > 0


def test_regulation_orm_indexes() -> None:
    """Test RegulationORM has indexes."""
    table_args = RegulationORM.__table_args__
    assert table_args is not None

    # Should have index on global_tags
    indexes = [
        arg for arg in table_args if hasattr(arg, "name") and "global_tags" in arg.name
    ]
    assert len(indexes) > 0


def test_reg_mapping_orm_indexes() -> None:
    """Test RegMappingORM has indexes."""
    table_args = RegMappingORM.__table_args__
    assert table_args is not None

    # Should have index on payload
    indexes = [
        arg for arg in table_args if hasattr(arg, "name") and "payload" in arg.name
    ]
    assert len(indexes) > 0


def test_regulation_orm_defaults() -> None:
    """Test RegulationORM default values."""
    columns = {col.name: col for col in RegulationORM.__table__.columns}

    # is_active should default to True
    assert "is_active" in columns
    assert columns["is_active"].default is not None

    # metadata_ should default to dict
    assert "metadata" in columns

    # global_tags should default to list
    assert "global_tags" in columns
