"""Mock fetcher for SG BCA regulations."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
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
        """Return a representative sample record newer than ``since``."""

        regulations = [
            {
                "external_id": "sg-bca-2025-fire-safety",
                "title": "Fire Code 2025 Section 1.1 Smoke Detectors",
                "body": (
                    "Section 1.1 Fire Safety - A smoke detector must be installed in every "
                    "residential unit to ensure compliance with evacuation procedures."
                ),
                "issued_on": "2025-01-15",
                "effective_on": "2025-04-01",
                "version": "2025 Edition",
                "metadata": {
                    "document_type": "Code of Practice",
                    "division": "Fire Safety & Shelter Department",
                },
                "categories": ["Fire Safety"],
                "keywords": ["smoke detector", "residential"],
            },
            {
                "external_id": "sg-bca-2025-accessibility",
                "title": "Universal Design Guide 2025",
                "body": (
                    "Chapter 2 Accessibility - Entrances must incorporate universal design "
                    "principles to provide barrier-free access."
                ),
                "issued_on": "2025-02-01",
                "effective_on": "2025-06-01",
                "version": "2025 Edition",
                "metadata": {
                    "document_type": "Design Guide",
                    "division": "Building Plan & Management Department",
                },
                "categories": ["Accessibility"],
                "keywords": ["universal design", "inclusive"],
            },
        ]

        payload = {"regulations": regulations}

        return [
            ProvenanceRecord(
                regulation_external_id="sg-bca-batch-2025",
                source_uri=self.config.source_uri,
                fetched_at=datetime.now(UTC),
                fetch_parameters={"since": since.isoformat()},
                raw_content=json.dumps(payload),
            )
        ]


def fetch(since: date) -> Iterable[ProvenanceRecord]:
    """Module-level helper to align with the parser interface."""

    return Fetcher().fetch_raw(since)
