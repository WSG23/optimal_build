from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


@pytest.fixture()
def upload_module():
    return importlib.import_module("src.services.analytics.upload_analytics")


def test_validate_dataframe_rows(upload_module) -> None:
    rows = [{"name": "Site A", "value": 3}, {"name": "Site B", "value": 4}]
    assert upload_module.validate_dataframe_rows(rows) is True

    rows_with_missing = [{"name": "Site C", "value": ""}]
    assert upload_module.validate_dataframe_rows(rows_with_missing) is False
