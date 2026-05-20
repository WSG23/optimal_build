"""Tests for SQLite-only development schema repair."""

from __future__ import annotations

import sqlalchemy as sa

from app.main import _repair_sqlite_schema_from_metadata


def test_sqlite_schema_repair_adds_missing_nullable_columns() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    metadata = sa.MetaData()

    sa.Table(
        "properties",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
    )

    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE properties ("
                "id INTEGER PRIMARY KEY, "
                "name VARCHAR NOT NULL"
                ")"
            )
        )

        repaired = _repair_sqlite_schema_from_metadata(conn, metadata)
        columns = {
            column["name"] for column in sa.inspect(conn).get_columns("properties")
        }

    assert repaired == ["properties.deleted_at", "properties.organization_id"]
    assert {"id", "name", "deleted_at", "organization_id"} <= columns


def test_sqlite_schema_repair_skips_missing_required_columns() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    metadata = sa.MetaData()

    sa.Table(
        "projects",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
    )

    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE projects (id INTEGER PRIMARY KEY)"))

        repaired = _repair_sqlite_schema_from_metadata(conn, metadata)
        columns = {
            column["name"] for column in sa.inspect(conn).get_columns("projects")
        }

    assert repaired == []
    assert "created_by" not in columns
