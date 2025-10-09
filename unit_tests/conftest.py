"""Pytest configuration for unit_tests."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--db-url",
        action="store",
        default=None,
        help="Postgres database URL for integration tests.",
    )
