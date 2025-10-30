"""Schema validation tests - verify migrations match model definitions.

These tests ensure that:
1. Migration output matches model definitions (no schema drift)
2. All model columns exist in the database
3. No extra columns exist that aren't in the model

This catches the "stub table" issue that caused the projects table failure.
"""

import pytest


def test_projects_table_exists(db_inspector):
    """Verify projects table was created by migrations."""
    tables = db_inspector.get_table_names()
    assert "projects" in tables, "projects table should exist after migrations"


def test_projects_table_schema_matches_model(db_inspector):
    """Verify projects table has all columns from Project model.

    This test catches the issue where migration created a stub table with only
    'id' column, but the model expected 70+ columns.

    See: SMOKE_TEST_FIX_REPORT.md for the root cause this test prevents.
    """
    # Get columns from database
    try:
        db_columns = {col["name"] for col in db_inspector.get_columns("projects")}
    except Exception:
        pytest.skip("projects table doesn't exist - migration not applied yet")

    # Get columns from model
    try:
        from backend.app.models.projects import Project

        model_columns = {col.name for col in Project.__table__.columns}
    except ImportError:
        pytest.skip("Project model not found - skipping validation")

    # Compare
    missing_in_db = model_columns - db_columns
    extra_in_db = db_columns - model_columns

    # Report detailed failures
    if missing_in_db:
        missing_list = ", ".join(sorted(missing_in_db))
        pytest.fail(
            f"Migration is missing {len(missing_in_db)} columns from Project model:\n"
            f"  Missing: {missing_list}\n\n"
            f"This indicates schema drift - the migration doesn't match the model.\n"
            f"Create a new migration to add these columns."
        )

    if extra_in_db:
        extra_list = ", ".join(sorted(extra_in_db))
        pytest.fail(
            f"Database has {len(extra_in_db)} extra columns not in Project model:\n"
            f"  Extra: {extra_list}\n\n"
            f"This indicates the model is missing columns that exist in the DB.\n"
            f"Update the model or create a migration to remove these columns."
        )


def test_finance_tables_exist(db_inspector):
    """Verify finance tables were created by migrations."""
    tables = db_inspector.get_table_names()

    expected_finance_tables = [
        "fin_projects",
        "fin_scenarios",
        "fin_scenario_cash_flows",
    ]

    missing_tables = [table for table in expected_finance_tables if table not in tables]

    if missing_tables:
        pytest.fail(
            f"Missing {len(missing_tables)} expected finance tables:\n"
            f"  Missing: {', '.join(missing_tables)}\n\n"
            f"This indicates finance migrations haven't been applied or failed."
        )


def test_agent_tables_exist(db_inspector):
    """Verify agent-related tables were created by migrations."""
    tables = db_inspector.get_table_names()

    # We expect at least agent_deals to exist (core agent functionality)
    assert (
        "agent_deals" in tables
    ), "agent_deals table should exist (core agent functionality)"


def test_entitlements_tables_exist(db_inspector):
    """Verify entitlements tables were created by migrations."""
    tables = db_inspector.get_table_names()

    expected_entitlements_tables = [
        "ent_approval_types",
        "ent_property_approvals",
    ]

    missing_tables = [
        table for table in expected_entitlements_tables if table not in tables
    ]

    if missing_tables:
        pytest.fail(
            f"Missing {len(missing_tables)} expected entitlements tables:\n"
            f"  Missing: {', '.join(missing_tables)}\n\n"
            f"This indicates entitlements migrations haven't been applied."
        )


def test_no_duplicate_migrations(alembic_config):
    """Verify there are no duplicate migration revision IDs.

    Duplicate revisions cause migration failures and indicate merge conflicts
    or manual editing of migration files.
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    migrations_dir = repo_root / "backend" / "migrations" / "versions"

    if not migrations_dir.exists():
        pytest.skip("Migrations directory not found")

    # Extract revision IDs from migration files
    revision_pattern = r'revision\s*:\s*str\s*=\s*[\'"]([^\'"]+)[\'"]'
    import re

    revisions = {}
    for migration_file in migrations_dir.glob("*.py"):
        if migration_file.name == "__init__.py":
            continue

        content = migration_file.read_text()
        match = re.search(revision_pattern, content)

        if match:
            revision_id = match.group(1)
            if revision_id in revisions:
                pytest.fail(
                    f"Duplicate migration revision '{revision_id}' found:\n"
                    f"  File 1: {revisions[revision_id]}\n"
                    f"  File 2: {migration_file.name}\n\n"
                    f"This indicates a merge conflict or manual file editing.\n"
                    f"Delete one of the files and regenerate if needed."
                )
            revisions[revision_id] = migration_file.name


def test_migration_naming_convention(alembic_config):
    """Verify migration files follow naming convention: YYYYMMDD_NNNNNN_description.py

    Correct: 20240919_000005_enable_postgis_geometry.py
    Wrong: abc123_migration.py, my_migration.py
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    migrations_dir = repo_root / "backend" / "migrations" / "versions"

    if not migrations_dir.exists():
        pytest.skip("Migrations directory not found")

    # Pattern: YYYYMMDD_NNNNNN_description.py or short_hash_description.py
    import re

    valid_pattern = re.compile(r"^(\d{8}_\d{6}_.*|[a-f0-9]{12}_.*|__init__)\.py$")

    invalid_files = []
    for migration_file in migrations_dir.glob("*.py"):
        if not valid_pattern.match(migration_file.name):
            invalid_files.append(migration_file.name)

    if invalid_files:
        pytest.fail(
            f"Found {len(invalid_files)} migrations with invalid names:\n"
            f"  Invalid: {', '.join(invalid_files)}\n\n"
            f"Migrations should follow naming convention:\n"
            f"  - YYYYMMDD_NNNNNN_description.py (preferred)\n"
            f"  - 12charhash_description.py (alembic auto-generated)\n\n"
            f"Use: alembic revision -m 'description'"
        )
