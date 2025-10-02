from __future__ import annotations

import importlib
import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[3] / "backend"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def _load_service():
    module = importlib.import_module("src.services.analytics.threat_intel")
    return module


def test_ingest_streaming_filters_low_confidence() -> None:
    threat_module = _load_service()
    ingestor = threat_module.ThreatIntelIngestor()

    signals = [
        threat_module.ThreatSignal("malicious.io", 0.9),
        threat_module.ThreatSignal("benign.io", 0.2),
    ]

    ingestor.ingest(signals)
    snapshot = ingestor.snapshot()

    assert len(snapshot) == 1
    assert snapshot[0].indicator == "malicious.io"
