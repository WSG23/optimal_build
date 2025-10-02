from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def test_streaming_api_roundtrip() -> None:
    module = importlib.import_module("src.services.analytics.streaming_api")
    api = module.StreamingAnalyticsAPI()

    api.publish("Foo", 1.5)
    api.batch_publish([module.Event("Bar", 2.5)])

    snapshot = api.snapshot()
    assert len(snapshot) == 2
    streamed = list(api.stream())
    assert [(event.key, event.value) for event in streamed] == [("Foo", 1.5), ("Bar", 2.5)]
