"""Threat intelligence utilities for streaming ingest tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class ThreatSignal:
    indicator: str
    confidence: float


class ThreatIntelIngestor:
    """Aggregate threat signals from streaming sources."""

    def __init__(self) -> None:
        self._signals: List[ThreatSignal] = []

    def ingest(self, signals: Iterable[ThreatSignal]) -> None:
        for signal in signals:
            if signal.confidence >= 0.5:
                self._signals.append(signal)

    def snapshot(self) -> List[ThreatSignal]:
        return list(self._signals)
