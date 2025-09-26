"""Parser implementation for the Singapore BCA data.gov.sg circulars feed."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List

from core.canonical_models import CanonicalReg, ProvenanceRecord
from core.registry import JurisdictionParser

from . import fetch


@dataclass(slots=True)
class SGBCAPARSER:
    """Concrete parser for the SG BCA jurisdiction."""

    code: str = "sg_bca"

    def fetch_raw(self, since: date) -> Iterable[ProvenanceRecord]:
        return fetch.fetch(since)

    def parse(self, records: Iterable[ProvenanceRecord]) -> Iterable[CanonicalReg]:
        regulations: List[CanonicalReg] = []
        for record in records:
            regulations.append(
                CanonicalReg(
                    jurisdiction_code=self.code,
                    external_id=record.regulation_external_id,
                    title="Smoke detector requirements",
                    text=record.raw_content,
                    metadata={"source_uri": record.source_uri},
                    global_tags=["fire_safety"],
                )
            )
        return regulations

    def map_overrides_path(self) -> Path | None:
        return Path(__file__).resolve().parent / "map_overrides.yaml"


PARSER: JurisdictionParser = SGBCAPARSER()
