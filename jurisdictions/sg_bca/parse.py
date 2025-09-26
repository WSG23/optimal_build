"""Parser implementation for the Singapore BCA data.gov.sg circulars feed."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import json
import re
from pathlib import Path
from typing import Iterable, List

from core.canonical_models import CanonicalReg, ProvenanceRecord
from core.mapping import GLOBAL_MAPPING_FILE, load_yaml, merge_mappings
from core.registry import JurisdictionParser

from . import fetch


class ParserError(RuntimeError):
    """Raised when a SG BCA record cannot be converted into a canonical form."""


@dataclass(slots=True)
class SGBCAPARSER:
    """Concrete parser for the SG BCA jurisdiction."""

    code: str = "sg_bca"
    _mapping_definition: dict | None = field(default=None, init=False, repr=False)

    def fetch_raw(self, since: date) -> Iterable[ProvenanceRecord]:
        return fetch.fetch(since)

    def parse(self, records: Iterable[ProvenanceRecord]) -> Iterable[CanonicalReg]:
        regulations: List[CanonicalReg] = []
        for record in records:
            payload = self._decode_record(record)
            regulations.append(self._build_regulation(record, payload))
        return regulations

    def map_overrides_path(self) -> Path | None:
        return Path(__file__).resolve().parent / "map_overrides.yaml"

    # ------------------------------------------------------------------
    def _decode_record(self, record: ProvenanceRecord) -> dict:
        try:
            payload = json.loads(record.raw_content)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ParserError(
                f"Record '{record.regulation_external_id}' contains invalid JSON: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise ParserError(
                f"Record '{record.regulation_external_id}' JSON payload is not an object"
            )
        return payload

    def _build_regulation(
        self, record: ProvenanceRecord, payload: dict
    ) -> CanonicalReg:
        title = self._extract_first(payload, "subject", "title", "circular_title")
        if not title:
            raise ParserError(
                f"SG BCA record '{record.regulation_external_id}' is missing a title"
            )

        text = self._extract_first(payload, "description", "content", "body")
        if not text:
            raise ParserError(
                f"SG BCA record '{record.regulation_external_id}' is missing body text"
            )

        issued_on = self._extract_date(
            payload,
            "circular_date",
            "issued_on",
            "issue_date",
            "published_date",
        )
        effective_on = self._extract_date(
            payload,
            "effective_date",
            "implementation_date",
            "wef_date",
            "effective_on",
        )

        version = self._extract_first(
            payload,
            "version",
            "circular_version",
            "revision",
            "revision_no",
        )

        metadata = self._build_metadata(record, payload)

        return CanonicalReg(
            jurisdiction_code=self.code,
            external_id=record.regulation_external_id,
            title=title,
            text=text,
            issued_on=issued_on,
            effective_on=effective_on,
            version=version,
            metadata=metadata,
            global_tags=self._map_upstream_tags(payload),
        )

    def _build_metadata(
        self, record: ProvenanceRecord, payload: dict
    ) -> dict[str, object]:
        metadata: dict[str, object] = {"source_uri": record.source_uri}
        for key in (
            "category",
            "categories",
            "keywords",
            "tags",
            "document_type",
            "agency",
            "subject",
            "weblink",
        ):
            value = payload.get(key)
            if value is not None and value != "":
                metadata[key] = value
        return metadata

    def _extract_first(self, payload: dict, *keys: str) -> str | None:
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                stripped = value.strip()
                if stripped:
                    return stripped
            else:
                return str(value)
        return None

    def _extract_date(self, payload: dict, *keys: str) -> date | None:
        for key in keys:
            value = payload.get(key)
            parsed = self._parse_date(value)
            if parsed:
                return parsed
        return None

    def _parse_date(self, value: object) -> date | None:
        if value is None or value == "":
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, (int, float)):
            # Some upstream feeds deliver Excel serial numbers.
            try:
                return datetime.utcfromtimestamp(float(value)).date()
            except (OverflowError, OSError, ValueError):
                return None
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            cleaned = cleaned.replace("T", " ").replace("Z", "")
            for fmt in (
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
            ):
                try:
                    return datetime.strptime(cleaned, fmt).date()
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(cleaned).date()
            except ValueError:
                return None
        return None

    def _map_upstream_tags(self, payload: dict) -> List[str]:
        definition = self._get_mapping_definition()
        categories = definition.get("categories", {})
        terms = self._extract_terms(payload)
        matched = set()
        for slug, meta in categories.items():
            candidates = self._keywords_for_category(slug, meta)
            if terms & candidates:
                matched.add(slug)
        return sorted(matched)

    def _extract_terms(self, payload: dict) -> set[str]:
        values: List[str] = []
        for key in ("category", "categories", "keywords", "tags", "topic", "topics"):
            raw = payload.get(key)
            if raw is None:
                continue
            if isinstance(raw, str):
                values.extend(re.split(r"[;,|]", raw))
            elif isinstance(raw, (list, tuple)):
                for item in raw:
                    if isinstance(item, str):
                        values.extend(re.split(r"[;,|]", item))
                    elif item is not None:
                        values.append(str(item))
            else:
                values.append(str(raw))

        normalised: set[str] = set()
        for value in values:
            cleaned = value.strip()
            if not cleaned:
                continue
            lower = cleaned.lower()
            normalised.add(lower)
            slug = self._slugify(cleaned)
            if slug:
                normalised.add(slug)
        return normalised

    def _keywords_for_category(self, slug: str, payload: dict) -> set[str]:
        keywords = set()
        keywords.add(slug)
        keywords.add(slug.replace("_", " "))
        title = payload.get("title")
        if isinstance(title, str):
            keywords.add(title.strip().lower())
            keywords.add(self._slugify(title))
        for keyword in payload.get("keywords", []) or []:
            if not isinstance(keyword, str):
                continue
            cleaned = keyword.strip()
            if not cleaned:
                continue
            keywords.add(cleaned.lower())
            slug = self._slugify(cleaned)
            if slug:
                keywords.add(slug)
        return keywords

    def _get_mapping_definition(self) -> dict:
        if self._mapping_definition is None:
            global_map = load_yaml(GLOBAL_MAPPING_FILE)
            override_map: dict = {}
            override_path = self.map_overrides_path()
            if override_path is not None:
                override_map = load_yaml(override_path)
            self._mapping_definition = merge_mappings(global_map, override_map)
        return self._mapping_definition

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
        return slug


PARSER: JurisdictionParser = SGBCAPARSER()
