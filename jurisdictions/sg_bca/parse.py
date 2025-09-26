"""Parser implementation for the Singapore BCA mock plug-in."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set

from core.canonical_models import CanonicalReg, ProvenanceRecord
from core.mapping import GLOBAL_MAPPING_FILE, load_yaml, merge_mappings
from core.registry import JurisdictionParser

from . import fetch


class ParserError(RuntimeError):
    """Raised when the upstream payload cannot be transformed."""


@dataclass(slots=True)
class SGBCAPARSER:
    """Concrete parser for the SG BCA jurisdiction."""

    code: str = "sg_bca"

    def fetch_raw(self, since: date) -> Iterable[ProvenanceRecord]:
        return fetch.fetch(since)

    def parse(self, records: Iterable[ProvenanceRecord]) -> Iterable[CanonicalReg]:
        keyword_index = self._build_keyword_index()
        regulations: List[CanonicalReg] = []
        for record in records:
            payload = self._load_payload(record)
            for index, upstream in enumerate(payload, start=1):
                regulation = self._convert_regulation(
                    record, upstream, index, keyword_index
                )
                regulations.append(regulation)
        return regulations

    def map_overrides_path(self) -> Path | None:
        return Path(__file__).resolve().parent / "map_overrides.yaml"

    # ------------------------------------------------------------------
    # Helpers
    def _load_payload(self, record: ProvenanceRecord) -> List[Dict]:
        """Deserialize a provenance payload into a list of regulations."""

        try:
            raw_payload = json.loads(record.raw_content)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ParserError(
                " | ".join(
                    [
                        f"Record {record.regulation_external_id} contains invalid JSON",
                        f"error: {exc.msg}",
                    ]
                )
            ) from exc

        if isinstance(raw_payload, dict):
            for key in ("regulations", "results", "items", "documents"):
                candidate = raw_payload.get(key)
                if isinstance(candidate, list):
                    raw_payload = candidate
                    break
            else:
                raise ParserError(
                    f"Record {record.regulation_external_id} is missing a 'regulations' list"
                )

        if not isinstance(raw_payload, list):
            raise ParserError(
                f"Record {record.regulation_external_id} payload must be a list of regulations"
            )

        typed_payload: List[Dict] = []
        for idx, item in enumerate(raw_payload, start=1):
            if not isinstance(item, dict):
                raise ParserError(
                    f"Record {record.regulation_external_id} regulation #{idx} must be a mapping"
                )
            typed_payload.append(item)
        return typed_payload

    def _convert_regulation(
        self,
        record: ProvenanceRecord,
        upstream: Dict,
        index: int,
        keyword_index: Dict[str, Set[str]],
    ) -> CanonicalReg:
        """Transform an upstream regulation payload into a canonical record."""

        external_id = self._require_str_field(
            upstream, "external_id", record, index
        )
        title = self._require_str_field(upstream, "title", record, index)
        text = upstream.get("body") or upstream.get("text") or upstream.get("content")
        if not isinstance(text, str) or not text.strip():
            raise ParserError(
                self._error_prefix(record, index, upstream)
                + "missing mandatory field 'body/text'"
            )

        issued_on = self._parse_date_field(
            upstream.get("issued_on") or upstream.get("issued"),
            "issued_on",
            record,
            upstream,
            index,
        )
        effective_on = self._parse_date_field(
            upstream.get("effective_on") or upstream.get("effective"),
            "effective_on",
            record,
            upstream,
            index,
        )

        version = upstream.get("version") or upstream.get("revision")
        if version is not None and not isinstance(version, str):
            raise ParserError(
                self._error_prefix(record, index, upstream)
                + "expected 'version' to be a string"
            )

        categories = self._coerce_list_of_str(
            upstream.get("categories"), "categories", record, upstream, index
        )
        keywords = self._coerce_list_of_str(
            upstream.get("keywords"), "keywords", record, upstream, index
        )

        metadata_payload = upstream.get("metadata") or {}
        if not isinstance(metadata_payload, dict):
            raise ParserError(
                self._error_prefix(record, index, upstream)
                + "expected 'metadata' to be an object"
            )

        metadata = dict(metadata_payload)
        if categories:
            metadata["upstream_categories"] = categories
        if keywords:
            metadata["upstream_keywords"] = keywords
        metadata.setdefault("source_uri", record.source_uri)
        metadata["provenance_record_id"] = record.regulation_external_id
        if record.fetch_parameters:
            metadata.setdefault("fetch_parameters", record.fetch_parameters)

        tags = self._map_tags(categories, keywords, keyword_index)

        return CanonicalReg(
            jurisdiction_code=self.code,
            external_id=external_id,
            title=title,
            text=text,
            issued_on=issued_on,
            effective_on=effective_on,
            version=version,
            metadata=metadata,
            global_tags=tags,
        )

    def _require_str_field(
        self,
        payload: Dict,
        field: str,
        record: ProvenanceRecord,
        index: int,
    ) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ParserError(
                self._error_prefix(record, index, payload)
                + f"missing mandatory field '{field}'"
            )
        return value.strip()

    def _parse_date_field(
        self,
        raw_value: object,
        field: str,
        record: ProvenanceRecord,
        payload: Dict,
        index: int,
    ) -> date | None:
        if raw_value in (None, ""):
            return None
        if not isinstance(raw_value, str):
            raise ParserError(
                self._error_prefix(record, index, payload)
                + f"expected '{field}' to be an ISO formatted string"
            )
        try:
            return date.fromisoformat(raw_value)
        except ValueError as exc:
            raise ParserError(
                self._error_prefix(record, index, payload)
                + f"invalid '{field}' value '{raw_value}': expected ISO date"
            ) from exc

    def _coerce_list_of_str(
        self,
        raw_values: object,
        field: str,
        record: ProvenanceRecord,
        payload: Dict,
        index: int,
    ) -> List[str]:
        if raw_values is None:
            return []
        if not isinstance(raw_values, Sequence) or isinstance(raw_values, (str, bytes)):
            raise ParserError(
                self._error_prefix(record, index, payload)
                + f"expected '{field}' to be an array of strings"
            )
        values: List[str] = []
        for position, value in enumerate(raw_values, start=1):
            if not isinstance(value, str) or not value.strip():
                raise ParserError(
                    self._error_prefix(record, index, payload)
                    + f"expected '{field}'[{position}] to be a non-empty string"
                )
            values.append(value.strip())
        return values

    def _build_keyword_index(self) -> Dict[str, Set[str]]:
        override_path = self.map_overrides_path()
        global_map = load_yaml(GLOBAL_MAPPING_FILE)
        override_map: Dict = {}
        if override_path is not None:
            override_map = load_yaml(override_path)
        merged = merge_mappings(global_map, override_map)

        categories = merged.get("categories", {})
        keyword_index: Dict[str, Set[str]] = {}
        for key, payload in categories.items():
            keywords = set()
            for keyword in payload.get("keywords", []) or []:
                if isinstance(keyword, str):
                    keywords.add(keyword.lower())
            keywords.add(key.lower())
            keywords.add(key.replace("_", " ").lower())
            keyword_index[key] = keywords
        return keyword_index

    def _map_tags(
        self,
        categories: Sequence[str],
        keywords: Sequence[str],
        keyword_index: Dict[str, Set[str]],
    ) -> List[str]:
        tags: Set[str] = set()
        normalized_terms = [value.lower() for value in (*categories, *keywords)]

        for category in categories:
            slug = category.lower().replace("-", "_").replace(" ", "_")
            if slug in keyword_index:
                tags.add(slug)

        for canonical, known_keywords in keyword_index.items():
            for term in normalized_terms:
                for keyword in known_keywords:
                    if keyword in term or term in keyword:
                        tags.add(canonical)
                        break
                if canonical in tags:
                    break

        return sorted(tags)

    def _error_prefix(
        self,
        record: ProvenanceRecord,
        index: int,
        payload: Dict,
    ) -> str:
        reference = payload.get("external_id")
        if isinstance(reference, str) and reference:
            return f"Record {record.regulation_external_id} ({reference}): "
        return f"Record {record.regulation_external_id} regulation #{index}: "


PARSER: JurisdictionParser = SGBCAPARSER()
