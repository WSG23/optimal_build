"""Persistence helpers for analytics results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from backend._compat.datetime import utcnow


@dataclass
class StoredResult:
    key: str
    value: float
    stored_at: datetime


@dataclass
class AnalyticsPersistence:
    """Very small in-memory persistence layer used in tests."""

    _results: Dict[str, StoredResult] = field(default_factory=dict)

    def save(self, key: str, value: float) -> StoredResult:
        result = StoredResult(key=key, value=value, stored_at=utcnow())
        self._results[key] = result
        return result

    def list_results(self) -> List[StoredResult]:
        return list(self._results.values())

    def get(self, key: str) -> StoredResult | None:
        return self._results.get(key)
