"""Parser implementation for the Singapore BCA plug-in."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from html import unescape
from pathlib import Path
from typing import Iterable, List

from core.canonical_models import CanonicalReg, ProvenanceRecord
from core.registry import JurisdictionParser

from . import fetch


def _strip_html(html: str) -> str:
    """Convert an HTML fragment into normalised plain text."""

    text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", "", html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _parse_optional_date(raw: str | None) -> date | None:
    if not raw:
        return None
    return date.fromisoformat(raw)


def _normalise_tags(tags: Iterable[str]) -> List[str]:
    normalised: List[str] = []
    for tag in tags:
        slug = re.sub(r"[^a-z0-9]+", "_", tag.lower()).strip("_")
        normalised.append(slug or tag.lower())
    return normalised


@dataclass(slots=True)
class SGBCAPARSER:
    """Concrete parser for the SG BCA jurisdiction."""

    code: str = "sg_bca"

    def fetch_raw(self, since: date) -> Iterable[ProvenanceRecord]:
        return fetch.fetch(since)

    def parse(self, records: Iterable[ProvenanceRecord]) -> Iterable[CanonicalReg]:
        regulations: List[CanonicalReg] = []
        for record in records:
            try:
                payload = json.loads(record.raw_content)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Malformed regulation payload for {record.regulation_external_id}"
                ) from exc

            if not isinstance(payload, dict):
                raise ValueError(
                    f"Malformed regulation payload for {record.regulation_external_id}"
                )

            title = payload.get("title")
            if not title:
                raise ValueError(
                    f"Missing title for regulation {record.regulation_external_id}"
                )

            html_body = payload.get("html_body", "")
            text = _strip_html(html_body)

            issued_on = _parse_optional_date(payload.get("issued_on"))
            effective_on = _parse_optional_date(payload.get("effective_on"))

            metadata = {
                "source_uri": record.source_uri,
                "section": payload.get("section"),
                "detail_url": payload.get("detail_url"),
            }

            raw_tags = payload.get("tags") or []
            if not isinstance(raw_tags, list):
                raise ValueError(
                    f"Malformed tags for regulation {record.regulation_external_id}"
                )

            regulations.append(
                CanonicalReg(
                    jurisdiction_code=self.code,
                    external_id=record.regulation_external_id,
                    title=title,
                    text=text,
                    issued_on=issued_on,
                    effective_on=effective_on,
                    metadata=metadata,
                    global_tags=_normalise_tags(tag for tag in raw_tags if isinstance(tag, str)),
                )
            )
        return regulations

    def map_overrides_path(self) -> Path | None:
        return Path(__file__).resolve().parent / "map_overrides.yaml"


PARSER: JurisdictionParser = SGBCAPARSER()
