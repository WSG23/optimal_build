from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def test_available_modules_contains_expected_entries() -> None:
    module = importlib.import_module("src.services.analytics.new_modules")
    available = module.AVAILABLE_ANALYTICS_MODULES

    assert "streaming" in available
    assert available["hll"].summary.startswith("HyperLogLog")
    assert module.iter_module_names() == (
        "hll",
        "memory_profile",
        "persistence",
        "streaming",
    )
