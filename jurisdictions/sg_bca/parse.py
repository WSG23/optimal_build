"""Parser implementation for the Singapore BCA data.gov.sg circulars feed."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import json
import re
from pathlib import Path
from typing import Any, Iterable, List, Sequence

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
    display_name: str = "Singapore Building and Construction Authority"
    _mapping_definition: dict | None = field(default=None, init=False, repr=False)

    def fetch_raw(self, since: date) -> Iterable[ProvenanceRecord]:
        return fetch.fetch(since)

    def parse(self, records: Iterable[ProvenanceRecord]) -> Iterable[CanonicalReg]:
        regulations: List[CanonicalReg] = []
        for record in records:
            payload = self._decode_record(record)
            for regulation_payload, context, fallback_id in self._iter_regulations(
                record, payload
            ):
                regulations.append(
                    self._build_regulation(
                        record, regulation_payload, context, fallback_id
                    )
                )
        return regulations

    def map_overrides_path(self) -> Path | None:
        return Path(__file__).resolve().parent / "map_overrides.yaml"

    # ------------------------------------------------------------------
    def _decode_record(self, record: ProvenanceRecord) -> Any:
        try:
            payload = json.loads(record.raw_content)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ParserError(
                f"Record '{record.regulation_external_id}' contains invalid JSON: {exc}"
            ) from exc

        if not isinstance(payload, (dict, list)):
            raise ParserError(
                f"Record '{record.regulation_external_id}' JSON payload must be an object or array"
            )
        return payload

    def _iter_regulations(
        self, record: ProvenanceRecord, payload: Any
    ) -> List[tuple[dict, str, str | None]]:
        if isinstance(payload, list):
            container = payload
            container_label = "payload"
            fallback_id: str | None = None
        elif isinstance(payload, dict):
            container = self._locate_regulation_container(payload)
            if container is None:
                context = record.regulation_external_id or record.source_uri
                return [
                    (
                        payload,
                        context or "SG BCA record without identifier",
                        record.regulation_external_id,
                    )
                ]
            container_label = container[0]
            container = container[1]
            fallback_id = None
        else:  # pragma: no cover - defensive programming
            raise ParserError(
                f"Record '{record.regulation_external_id}' has unsupported payload type"
            )

        if not isinstance(container, Sequence) or isinstance(container, (str, bytes)):
            raise ParserError(
                f"Record '{record.regulation_external_id}' field '{container_label}' must be an array"
            )

        regulations: List[tuple[dict, str, str | None]] = []
        for index, entry in enumerate(container):
            if not isinstance(entry, dict):
                raise ParserError(
                    f"Record '{record.regulation_external_id}' entry {container_label}[{index}] is not a JSON object"
                )
            regulations.append(
                (
                    entry,
                    self._regulation_context(record, entry, container_label, index),
                    fallback_id,
                )
            )
        return regulations

    def _locate_regulation_container(
        self, payload: dict
    ) -> tuple[str, Sequence[Any]] | None:
        if "result" in payload and isinstance(payload["result"], dict):
            result = payload["result"]
            records = result.get("records")
            if isinstance(records, Sequence) and not isinstance(records, (str, bytes)):
                return "result.records", records
        for key in ("records", "regulations", "items", "data"):
            candidate = payload.get(key)
            if isinstance(candidate, Sequence) and not isinstance(
                candidate, (str, bytes)
            ):
                return key, candidate
        return None

    def _regulation_context(
        self,
        record: ProvenanceRecord,
        payload: dict,
        container_label: str,
        index: int,
    ) -> str:
        external_id = self._extract_external_id(payload, strict=False)
        if external_id:
            return str(external_id)
        base = record.regulation_external_id or record.source_uri or "unknown-record"
        return f"{base} {container_label}[{index}]"

    def _build_regulation(
        self,
        record: ProvenanceRecord,
        payload: dict,
        context: str,
        fallback_external_id: str | None,
    ) -> CanonicalReg:
        external_id = self._extract_external_id(payload) or fallback_external_id
        if not external_id:
            raise ParserError(
                f"SG BCA regulation '{context}' is missing a circular number or external identifier"
            )

        title = self._extract_first(payload, "subject", "title", "circular_title")
        if not title:
            raise ParserError(f"SG BCA regulation '{context}' is missing a title")

        text = self._extract_first(payload, "description", "content", "body")
        if not text:
            raise ParserError(f"SG BCA regulation '{context}' is missing body text")

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

        metadata = self._build_metadata(record, payload, context)

        return CanonicalReg(
            jurisdiction_code=self.code,
            external_id=external_id,
            title=title,
            text=text,
            issued_on=issued_on,
            effective_on=effective_on,
            version=version,
            metadata=metadata,
            global_tags=self._map_upstream_tags(payload),
        )

    def _build_metadata(
        self, record: ProvenanceRecord, payload: dict, context: str
    ) -> dict[str, object]:
        metadata: dict[str, object] = {}
        source_uri = self._extract_first(
            payload,
            "weblink",
            "url",
            "uri",
            "link",
            "source_uri",
        )
        if not source_uri:
            source_uri = record.source_uri
        if not source_uri:
            raise ParserError(f"SG BCA regulation '{context}' is missing a source URI")
        metadata["source_uri"] = source_uri
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

    def _extract_external_id(self, payload: dict, *, strict: bool = True) -> str | None:
        for key in (
            "circular_no",
            "circular_number",
            "external_id",
            "regulation_external_id",
            "document_number",
            "reference",
            "ref",
            "id",
            "identifier",
        ):
            if key not in payload:
                continue
            value = payload.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
                if value:
                    return value
            else:
                return str(value)
        if strict:
            return None
        return None

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
            values.extend(self._flatten_terms(payload.get(key)))

        normalised: set[str] = set()
        for value in values:
            for token in re.split(r"[;,|]", value):
                cleaned = token.strip()
                if not cleaned:
                    continue
                lower = cleaned.lower()
                normalised.add(lower)
                slug = self._slugify(cleaned)
                if slug:
                    normalised.add(slug)
        return normalised

    def _flatten_terms(self, raw: object) -> List[str]:
        if raw is None:
            return []
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, (list, tuple, set)):
            values: List[str] = []
            for item in raw:
                values.extend(self._flatten_terms(item))
            return values
        if isinstance(raw, dict):
            collected: List[str] = []
            for key in ("name", "title", "label", "value", "slug", "text"):
                value = raw.get(key)
                if isinstance(value, str):
                    collected.append(value)
            for nested in ("keywords", "tags", "values", "items"):
                if nested in raw:
                    collected.extend(self._flatten_terms(raw[nested]))
            if collected:
                return collected
            fallback = raw.get("id")
            if isinstance(fallback, str):
                return [fallback]
        return [str(raw)]

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
