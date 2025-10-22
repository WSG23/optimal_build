from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    transform = importlib.import_module("scripts.heritage.transform")
except Exception as exc:  # pragma: no cover - skip when optional deps missing
    pytest.skip(
        f"Heritage CLI modules not importable in this environment: {exc}",
        allow_module_level=True,
    )


def test_transform_ura_conservation_produces_features() -> None:
    raw_path = Path("data/heritage/raw/ura_conservation/ura_conservation.zip")
    features = list(transform._transform_ura_conservation(raw_path))
    assert features, "Expected at least one heritage feature"
    first = features[0]
    assert first["properties"]["source"] == "URA"
    assert "geometry" in first
