"""Pytest fixtures for migration tests."""

import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


@pytest.fixture
def alembic_config():
    """Get Alembic configuration for testing."""
    repo_root = Path(__file__).resolve().parents[3]
    alembic_ini = repo_root / "alembic.ini"

    if not alembic_ini.exists():
        pytest.skip("alembic.ini not found - skipping migration tests")

    config = Config(str(alembic_ini))
    return config


@pytest.fixture
def migrated_test_db(alembic_config):
    """Create a temporary database with all migrations applied.

    This fixture:
    1. Creates a temporary SQLite database
    2. Runs all Alembic migrations (upgrade head)
    3. Returns the database URL for testing
    4. Cleans up the database after the test

    Use this to verify that migrations produce the expected schema.
    """
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name

    db_url = f"sqlite:///{db_path}"

    # Configure Alembic to use test database
    alembic_config.set_main_option("sqlalchemy.url", db_url)

    try:
        # Run all migrations
        command.upgrade(alembic_config, "head")

        # Return database URL for testing
        yield db_url

    finally:
        # Clean up
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def db_inspector(migrated_test_db):
    """Get SQLAlchemy inspector for the migrated test database."""
    engine = create_engine(migrated_test_db)
    return inspect(engine)
