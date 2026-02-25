"""Root-level pytest configuration to share stubs and fixtures across suites."""

# Re-export everything from the main test configuration so unit_tests also
# receive the dependency stubs (FastAPI, shapely, etc.).
from tests.conftest import *  # noqa: F401,F403

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run AnyIO tests on asyncio only to avoid mixed-backend loop teardown issues."""

    return "asyncio"
