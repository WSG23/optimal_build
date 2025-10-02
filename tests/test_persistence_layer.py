from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def test_persistence_layer_stores_results() -> None:
    module = importlib.import_module("src.services.analytics.persistence_layer")
    storage = module.AnalyticsPersistence()

    storage.save("foo", 2.5)
    storage.save("bar", 3.5)

    assert {result.key for result in storage.list_results()} == {"foo", "bar"}
    assert storage.get("missing") is None
