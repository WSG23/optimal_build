from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def test_estimate_cardinality_bias() -> None:
    module = importlib.import_module("src.services.analytics.hll_utils_extra")
    estimate = module.estimate_cardinality(["a", "b", "a", "c"])

    assert estimate >= 3
    assert module.estimate_cardinality([]) == 0
