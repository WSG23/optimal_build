from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def test_profile_memory_usage_records_snapshot() -> None:
    module = importlib.import_module("src.services.analytics.memory_profile")

    with module.profile_memory_usage():
        data = [i for i in range(1000)]
        assert sum(data) == 499500

    snapshot = module.profile_memory_usage.last_snapshot
    assert snapshot["current"] >= 0
    assert "peak" in snapshot
