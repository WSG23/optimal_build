from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def test_stream_events_normalises_keys() -> None:
    module = importlib.import_module("src.services.analytics.analytics_streaming")
    payload = [("Foo", 1), ("BAR", 2.0)]

    output = list(module.stream_events(payload))
    assert output == [("foo", 1.0), ("bar", 2.0)]
