"""Mock fetcher for SG BCA regulations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List

from core.canonical_models import ProvenanceRecord


@dataclass(slots=True)
class FetchConfig:
    """Configuration for the mocked fetcher."""

    source_uri: str = "https://example.gov.sg/bca/mock-regulation"


class Fetcher:
    """Return deterministic provenance records for offline testing."""

    def __init__(self, config: FetchConfig | None = None) -> None:
        self.config = config or FetchConfig()

    def fetch_raw(self, since: date) -> List[ProvenanceRecord]:
        """Return a single sample record newer than ``since``."""

        sample_text = (
            "Section 1.1 Fire Safety - A smoke detector must be installed in every "
            "residential unit to ensure compliance with fire evacuation procedures."
        )
        return [
            ProvenanceRecord(
                regulation_external_id="sg-bca-2025-fire-safety",
                source_uri=self.config.source_uri,
                fetched_at=datetime.utcnow(),
                fetch_parameters={"since": since.isoformat()},
                raw_content=sample_text,
            )
        ]


def fetch(since: date) -> Iterable[ProvenanceRecord]:
    """Module-level helper to align with the parser interface."""

    return Fetcher().fetch_raw(since)
