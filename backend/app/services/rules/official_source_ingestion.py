"""Live official-source ingestion for unresolved Capture rule fields.

This service fetches mapped official source pages and stages source-review
candidates. It can also publish narrow, pre-normalized values from the reviewed
source registry; broader live-source findings remain review-only until approved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Protocol

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefRule
from app.services.reference_sources import HTTPResponse, SimpleHTTPClient

logger = structlog.get_logger(__name__)


class OfficialSourceHTTPClient(Protocol):
    async def get(self, url: str) -> HTTPResponse: ...


FIELD_PARAMETER_KEYS = {
    "land_use": "zoning.source.land_use",
    "plot_ratio": "zoning.source.plot_ratio",
    "building_height_limit_m": "zoning.source.building_height_limit_m",
    "site_coverage_pct": "zoning.source.site_coverage_pct",
    "setbacks": "zoning.source.setbacks",
    "step_backs": "zoning.source.step_backs",
    "air_rights_note": "zoning.source.air_rights_note",
}

RESOLVED_PARAMETER_KEYS = {
    "building_height_limit_m": "zoning.max_building_height_m",
}

SETBACK_PARAMETER_KEYS = {
    "front": "zoning.setback.front_min_m",
    "rear": "zoning.setback.rear_min_m",
    "side": "zoning.setback.side_min_m",
}

ConfiguredRegistryValue = float | dict[str, float] | list[dict[str, float]]

HEIGHT_LIMIT_MARKER_RE = re.compile(
    r"capture-rule\s*:\s*building_height_limit_m\s*=\s*(?P<value>\d+(?:\.\d+)?)\s*m\b",
    re.IGNORECASE,
)
HEIGHT_LIMIT_JSON_RE = re.compile(
    r"<script[^>]+type=[\"']application/json[\"'][^>]*data-capture-rule[\"'][^>]*>"
    r"(?P<payload>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(slots=True)
class OfficialSourceIngestionCandidate:
    field: str
    authority: str
    title: str
    url: str
    status: str
    rule_id: int | None = None
    message: str | None = None


@dataclass(slots=True)
class OfficialSourceIngestionResult:
    jurisdiction: str
    zone_code: str | None
    candidates: list[OfficialSourceIngestionCandidate] = field(default_factory=list)

    @property
    def staged_count(self) -> int:
        return sum(1 for candidate in self.candidates if candidate.status == "staged")

    @property
    def resolved_count(self) -> int:
        return sum(1 for candidate in self.candidates if candidate.status == "resolved")

    @property
    def existing_count(self) -> int:
        return sum(1 for candidate in self.candidates if candidate.status == "existing")

    @property
    def failed_count(self) -> int:
        return sum(1 for candidate in self.candidates if candidate.status == "failed")

    def as_rule_corpus_payload(self) -> dict[str, Any]:
        return {
            "jurisdiction": self.jurisdiction,
            "zone_code": self.zone_code,
            "staged_count": self.staged_count,
            "resolved_count": self.resolved_count,
            "existing_count": self.existing_count,
            "failed_count": self.failed_count,
            "candidates": [
                {
                    "field": candidate.field,
                    "authority": candidate.authority,
                    "title": candidate.title,
                    "url": candidate.url,
                    "status": candidate.status,
                    "rule_id": candidate.rule_id,
                    "message": candidate.message,
                }
                for candidate in self.candidates
            ],
        }


class OfficialSourceIngestionService:
    """Fetch mapped official sources and resolve only reviewed registry values."""

    def __init__(self, http_client: OfficialSourceHTTPClient | None = None) -> None:
        self._http = http_client or SimpleHTTPClient(timeout=5.0, max_attempts=1)

    async def ingest_source_gaps(
        self,
        session: AsyncSession,
        *,
        jurisdiction: str,
        zone_code: str | None,
        source_gaps: list[dict[str, Any]],
    ) -> OfficialSourceIngestionResult:
        result = OfficialSourceIngestionResult(
            jurisdiction=jurisdiction,
            zone_code=zone_code,
        )
        if jurisdiction != "SG":
            return result

        for gap in source_gaps:
            field_name = str(gap.get("field") or "")
            parameter_key = FIELD_PARAMETER_KEYS.get(field_name)
            if not parameter_key:
                continue
            candidate_sources = gap.get("candidate_sources")
            if not isinstance(candidate_sources, list):
                continue

            for source in candidate_sources:
                if not isinstance(source, dict):
                    continue
                authority = str(source.get("authority") or "").strip()
                title = str(source.get("title") or "").strip()
                url = str(source.get("url") or "").strip()
                if not authority or not title or not url:
                    continue

                candidate = await self._stage_candidate(
                    session,
                    jurisdiction=jurisdiction,
                    zone_code=zone_code,
                    field_name=field_name,
                    parameter_key=parameter_key,
                    authority=authority,
                    title=title,
                    url=url,
                    source=source,
                )
                result.candidates.append(candidate)

        return result

    async def _stage_candidate(
        self,
        session: AsyncSession,
        *,
        jurisdiction: str,
        zone_code: str | None,
        field_name: str,
        parameter_key: str,
        authority: str,
        title: str,
        url: str,
        source: dict[str, Any],
    ) -> OfficialSourceIngestionCandidate:
        configured_value = _extract_configured_registry_value(
            field_name=field_name,
            source=source,
            zone_code=zone_code,
        )
        if configured_value is not None:
            resolved_rules = self._build_configured_resolved_rules(
                jurisdiction=jurisdiction,
                zone_code=zone_code,
                field_name=field_name,
                authority=authority,
                title=title,
                url=url,
                normalized_value=configured_value,
            )
            if resolved_rules:
                existing_rules: list[RefRule] = []
                new_rules: list[RefRule] = []
                for resolved_rule in resolved_rules:
                    existing_resolved = await self._find_existing_resolved_rule(
                        session,
                        jurisdiction=jurisdiction,
                        zone_code=zone_code,
                        parameter_key=resolved_rule.parameter_key,
                        value=resolved_rule.value,
                    )
                    if existing_resolved:
                        existing_rules.append(existing_resolved)
                    else:
                        new_rules.append(resolved_rule)

                if not new_rules:
                    return OfficialSourceIngestionCandidate(
                        field=field_name,
                        authority=authority,
                        title=title,
                        url=url,
                        status="existing",
                        rule_id=existing_rules[0].id if existing_rules else None,
                        message="configured normalized rule already approved",
                    )

                session.add_all(new_rules)
                await session.flush()
                return OfficialSourceIngestionCandidate(
                    field=field_name,
                    authority=authority,
                    title=title,
                    url=url,
                    status="resolved",
                    rule_id=new_rules[0].id,
                    message=(
                        f"normalized {field_name} rule approved from configured "
                        "official source registry"
                    ),
                )

        existing = await self._find_existing_candidate(
            session,
            jurisdiction=jurisdiction,
            zone_code=zone_code,
            parameter_key=parameter_key,
            url=url,
        )
        if existing:
            return OfficialSourceIngestionCandidate(
                field=field_name,
                authority=authority,
                title=title,
                url=url,
                status="existing",
                rule_id=existing.id,
            )

        try:
            response = await self._http.get(url)
            if response.status_code >= 400:
                return OfficialSourceIngestionCandidate(
                    field=field_name,
                    authority=authority,
                    title=title,
                    url=url,
                    status="failed",
                    message=f"official source returned HTTP {response.status_code}",
                )
        except Exception as exc:
            logger.warning(
                "Official source fetch failed",
                field=field_name,
                authority=authority,
                url=url,
                error=str(exc),
            )
            return OfficialSourceIngestionCandidate(
                field=field_name,
                authority=authority,
                title=title,
                url=url,
                status="failed",
                message=str(exc),
            )

        resolved_rule = self._build_resolved_rule(
            response=response,
            jurisdiction=jurisdiction,
            zone_code=zone_code,
            field_name=field_name,
            authority=authority,
            title=title,
            url=url,
        )
        if resolved_rule:
            existing_resolved = await self._find_existing_resolved_rule(
                session,
                jurisdiction=jurisdiction,
                zone_code=zone_code,
                parameter_key=resolved_rule.parameter_key,
                value=resolved_rule.value,
            )
            if existing_resolved:
                return OfficialSourceIngestionCandidate(
                    field=field_name,
                    authority=authority,
                    title=title,
                    url=url,
                    status="existing",
                    rule_id=existing_resolved.id,
                    message="normalized rule already approved",
                )

            session.add(resolved_rule)
            await session.flush()
            return OfficialSourceIngestionCandidate(
                field=field_name,
                authority=authority,
                title=title,
                url=url,
                status="resolved",
                rule_id=resolved_rule.id,
                message="normalized height-limit rule approved from machine-readable source",
            )

        rule = RefRule(
            jurisdiction=jurisdiction,
            authority=authority.split("/")[0],
            topic="zoning",
            parameter_key=parameter_key,
            operator="=",
            value="SOURCE_REVIEW_REQUIRED",
            applicability={"zone_code": zone_code} if zone_code else {},
            source_provenance=self._source_provenance(
                response=response,
                field_name=field_name,
                source_title=title,
                source_url=url,
            ),
            review_status="needs_review",
            is_published=False,
            notes=(
                "Live official source candidate. Extract and normalize the "
                "applicable rule before approval."
            ),
        )
        session.add(rule)
        await session.flush()

        return OfficialSourceIngestionCandidate(
            field=field_name,
            authority=authority,
            title=title,
            url=url,
            status="staged",
            rule_id=rule.id,
        )

    async def _find_existing_candidate(
        self,
        session: AsyncSession,
        *,
        jurisdiction: str,
        zone_code: str | None,
        parameter_key: str,
        url: str,
    ) -> RefRule | None:
        stmt = (
            select(RefRule)
            .where(RefRule.jurisdiction == jurisdiction)
            .where(RefRule.parameter_key == parameter_key)
            .where(RefRule.review_status == "needs_review")
            .where(RefRule.is_published.is_(False))
        )
        candidates = (await session.execute(stmt)).scalars().all()
        for candidate in candidates:
            provenance = (
                candidate.source_provenance
                if isinstance(candidate.source_provenance, dict)
                else {}
            )
            applicability = (
                candidate.applicability
                if isinstance(candidate.applicability, dict)
                else {}
            )
            if (
                provenance.get("official_source_url") == url
                and applicability.get("zone_code") == zone_code
            ):
                return candidate
        return None

    async def _find_existing_resolved_rule(
        self,
        session: AsyncSession,
        *,
        jurisdiction: str,
        zone_code: str | None,
        parameter_key: str,
        value: str,
    ) -> RefRule | None:
        stmt = (
            select(RefRule)
            .where(RefRule.jurisdiction == jurisdiction)
            .where(RefRule.parameter_key == parameter_key)
            .where(RefRule.value == value)
            .where(RefRule.review_status == "approved")
            .where(RefRule.is_published.is_(True))
        )
        candidates = (await session.execute(stmt)).scalars().all()
        for candidate in candidates:
            applicability = (
                candidate.applicability
                if isinstance(candidate.applicability, dict)
                else {}
            )
            if applicability.get("zone_code") == zone_code:
                return candidate
        return None

    def _build_resolved_rule(
        self,
        *,
        response: HTTPResponse,
        jurisdiction: str,
        zone_code: str | None,
        field_name: str,
        authority: str,
        title: str,
        url: str,
    ) -> RefRule | None:
        parameter_key = RESOLVED_PARAMETER_KEYS.get(field_name)
        if not parameter_key:
            return None

        normalized_value = _extract_machine_readable_value(
            field_name=field_name,
            content=response.content or b"",
        )
        if normalized_value is None:
            return None

        now = datetime.now(timezone.utc)
        return RefRule(
            jurisdiction=jurisdiction,
            authority=authority.split("/")[0],
            topic="zoning",
            parameter_key=parameter_key,
            operator="<=",
            value=f"{normalized_value:g}",
            unit="m",
            applicability={"zone_code": zone_code} if zone_code else {},
            source_provenance={
                **self._source_provenance(
                    response=response,
                    field_name=field_name,
                    source_title=title,
                    source_url=url,
                ),
                "ingestion_stage": "official_source_normalized",
                "normalization_method": "machine_readable_capture_rule",
            },
            review_status="approved",
            reviewer="capture-official-source-ingestion",
            reviewed_at=now,
            is_published=True,
            published_at=now,
            notes=(
                "Normalized from machine-readable official source marker. "
                "Review source provenance before production certification."
            ),
        )

    def _build_configured_resolved_rules(
        self,
        *,
        jurisdiction: str,
        zone_code: str | None,
        field_name: str,
        authority: str,
        title: str,
        url: str,
        normalized_value: ConfiguredRegistryValue,
    ) -> list[RefRule]:
        if field_name == "setbacks":
            if not isinstance(normalized_value, dict):
                return []
            rules = []
            for direction, parameter_key in SETBACK_PARAMETER_KEYS.items():
                value = normalized_value.get(direction)
                if value is None:
                    continue
                rules.append(
                    self._build_configured_resolved_rule(
                        jurisdiction=jurisdiction,
                        zone_code=zone_code,
                        field_name=field_name,
                        authority=authority,
                        title=title,
                        url=url,
                        parameter_key=parameter_key,
                        operator=">=",
                        normalized_value=value,
                        source_detail={"setback_direction": direction},
                    )
                )
            return rules

        if field_name == "step_backs":
            if not isinstance(normalized_value, list):
                return []
            rules = []
            for stepback in normalized_value:
                level = stepback.get("level")
                depth_m = stepback.get("depth_m")
                if level is None or depth_m is None:
                    continue
                level_number = _coerce_positive_int(level)
                if level_number is None:
                    continue
                rules.append(
                    self._build_configured_resolved_rule(
                        jurisdiction=jurisdiction,
                        zone_code=zone_code,
                        field_name=field_name,
                        authority=authority,
                        title=title,
                        url=url,
                        parameter_key=f"zoning.stepback.level_{level_number}_depth_m",
                        operator=">=",
                        normalized_value=depth_m,
                        source_detail={"stepback_level": level_number},
                        applicability_detail={"level": level_number},
                    )
                )
            return rules

        resolved_parameter_key = RESOLVED_PARAMETER_KEYS.get(field_name)
        if not resolved_parameter_key or not isinstance(normalized_value, float):
            return []

        return [
            self._build_configured_resolved_rule(
                jurisdiction=jurisdiction,
                zone_code=zone_code,
                field_name=field_name,
                authority=authority,
                title=title,
                url=url,
                parameter_key=resolved_parameter_key,
                operator="<=",
                normalized_value=normalized_value,
                source_detail={},
                applicability_detail=None,
            )
        ]

    def _build_configured_resolved_rule(
        self,
        *,
        jurisdiction: str,
        zone_code: str | None,
        field_name: str,
        authority: str,
        title: str,
        url: str,
        parameter_key: str,
        operator: str,
        normalized_value: float,
        source_detail: dict[str, Any],
        applicability_detail: dict[str, Any] | None = None,
    ) -> RefRule:
        now = datetime.now(timezone.utc)
        applicability = {"zone_code": zone_code} if zone_code else {}
        if applicability_detail:
            applicability.update(applicability_detail)
        return RefRule(
            jurisdiction=jurisdiction,
            authority=authority.split("/")[0],
            topic="zoning",
            parameter_key=parameter_key,
            operator=operator,
            value=f"{normalized_value:g}",
            unit="m",
            applicability=applicability,
            source_provenance={
                "ingestion_stage": "official_source_normalized",
                "field": field_name,
                "official_source_title": title,
                "official_source_url": url,
                "retrieved_at": now.isoformat(),
                "normalization_method": "configured_official_source_registry",
                **source_detail,
            },
            review_status="approved",
            reviewer="capture-official-source-ingestion",
            reviewed_at=now,
            is_published=True,
            published_at=now,
            notes=(
                "Normalized from configured official-source registry extract. "
                "Review source provenance before production certification."
            ),
        )

    def _source_provenance(
        self,
        *,
        response: HTTPResponse,
        field_name: str,
        source_title: str,
        source_url: str,
    ) -> dict[str, Any]:
        content = response.content or b""
        return {
            "ingestion_stage": "official_source_candidate",
            "field": field_name,
            "official_source_title": source_title,
            "official_source_url": source_url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "http_status": response.status_code,
            "content_type": _get_header(response.headers, "content-type"),
            "content_hash_sha256": sha256(content).hexdigest(),
            "excerpt": _excerpt(content),
        }


def _get_header(headers: Any, key: str) -> str | None:
    if not isinstance(headers, dict):
        return None
    key_lower = key.lower()
    for header, value in headers.items():
        if str(header).lower() == key_lower:
            return str(value)
    return None


def _excerpt(content: bytes, max_chars: int = 400) -> str:
    text = content.decode("utf-8", errors="ignore")
    return " ".join(text.split())[:max_chars]


def _extract_machine_readable_value(
    *,
    field_name: str,
    content: bytes,
) -> float | None:
    if field_name != "building_height_limit_m":
        return None

    text = content.decode("utf-8", errors="ignore")
    marker_match = HEIGHT_LIMIT_MARKER_RE.search(text)
    if marker_match:
        return _coerce_positive_float(marker_match.group("value"))

    for match in HEIGHT_LIMIT_JSON_RE.finditer(text):
        try:
            payload = json.loads(match.group("payload"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("field") != field_name:
            continue
        unit = str(payload.get("unit") or "").lower()
        if unit and unit not in {"m", "meter", "meters", "metre", "metres"}:
            continue
        value = _coerce_positive_float(payload.get("value"))
        if value is not None:
            return value

    return None


def _extract_configured_registry_value(
    *,
    field_name: str,
    source: dict[str, Any],
    zone_code: str | None,
) -> ConfiguredRegistryValue | None:
    if (
        field_name not in {"building_height_limit_m", "setbacks", "step_backs"}
        or not zone_code
    ):
        return None

    values_by_zone = source.get("configured_values_by_zone")
    if not isinstance(values_by_zone, dict):
        return None

    unit = str(source.get("unit") or "").lower()
    if unit and unit not in {"m", "meter", "meters", "metre", "metres"}:
        return None

    raw_value = None
    zone_key = zone_code.lower()
    for candidate_zone, candidate_value in values_by_zone.items():
        if str(candidate_zone).lower() == zone_key:
            raw_value = candidate_value
            break
    if raw_value is None:
        return None

    if field_name == "building_height_limit_m":
        return _coerce_positive_float(raw_value)

    if field_name == "setbacks":
        if not isinstance(raw_value, dict):
            return None
        setbacks = {
            direction: value
            for direction, value in (
                (direction, _coerce_positive_float(raw_value.get(direction)))
                for direction in SETBACK_PARAMETER_KEYS
            )
            if value is not None
        }
        return setbacks or None

    if field_name == "step_backs":
        if not isinstance(raw_value, list):
            return None
        step_backs = []
        for entry in raw_value:
            if not isinstance(entry, dict):
                continue
            level = _coerce_positive_float(entry.get("level") or entry.get("storey"))
            depth_m = _coerce_positive_float(entry.get("depth_m") or entry.get("depth"))
            if level is None or depth_m is None:
                continue
            step_backs.append({"level": level, "depth_m": depth_m})
        return step_backs or None

    return None


def _coerce_positive_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if number > 0 else None


def _coerce_positive_int(value: object) -> int | None:
    number = _coerce_positive_float(value)
    if number is None or not number.is_integer():
        return None
    return int(number)
