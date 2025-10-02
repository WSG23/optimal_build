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


def test_unicode_columns_are_normalised(upload_module) -> None:
    records = [{"Náme": "Site A", "Value": 3}]
    normalised = upload_module.normalize_column_names(records)
    assert normalised == [{"name": "Site A", "value": 3}]
