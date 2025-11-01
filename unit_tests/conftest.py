"""Pytest configuration for unit_tests."""

from tests.conftest import *  # noqa: F401,F403 - re-export shared fixtures and plugins

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--db-url",
        action="store",
        default=None,
        help="Postgres database URL for integration tests.",
    )
