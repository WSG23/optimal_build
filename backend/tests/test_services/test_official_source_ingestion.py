from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.rkp import RefRule
from app.services.reference_sources import HTTPResponse
from app.services.rules.official_source_ingestion import (
    OfficialSourceIngestionService,
)


class _FakeHTTPClient:
    def __init__(
        self,
        *,
        status_code: int = 200,
        content: bytes | None = None,
    ) -> None:
        self.calls: list[str] = []
        self.status_code = status_code
        self.content = (
            content
            if content is not None
            else b"<html><body>Official development control guidance</body></html>"
        )

    async def get(self, url: str) -> HTTPResponse:
        self.calls.append(url)
        return HTTPResponse(
            status_code=self.status_code,
            headers={"content-type": "text/html"},
            content=self.content,
        )


@pytest.mark.asyncio
async def test_official_source_ingestion_stages_review_candidate(
    async_session_factory,
) -> None:
    http = _FakeHTTPClient()
    service = OfficialSourceIngestionService(http_client=http)
    source_gaps = [
        {
            "field": "setbacks",
            "reason": "not_resolved_from_current_registry",
            "candidate_sources": [
                {
                    "authority": "URA",
                    "title": "Development Control Guidelines - setback controls",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                }
            ],
        }
    ]

    async with async_session_factory() as session:
        result = await service.ingest_source_gaps(
            session,
            jurisdiction="SG",
            zone_code="SG:commercial",
            source_gaps=source_gaps,
        )
        await session.commit()

    assert result.staged_count == 1
    assert result.failed_count == 0
    assert http.calls == [
        "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control"
    ]

    async with async_session_factory() as session:
        rules = (await session.execute(select(RefRule))).scalars().all()

    assert len(rules) == 1
    rule = rules[0]
    assert rule.parameter_key == "zoning.source.setbacks"
    assert rule.value == "SOURCE_REVIEW_REQUIRED"
    assert rule.review_status == "needs_review"
    assert rule.is_published is False
    assert rule.applicability == {"zone_code": "SG:commercial"}
    assert rule.source_provenance["field"] == "setbacks"
    assert rule.source_provenance["official_source_url"] == (
        "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control"
    )
    assert rule.source_provenance["ingestion_stage"] == "official_source_candidate"


@pytest.mark.asyncio
async def test_official_source_ingestion_resolves_machine_readable_height_limit(
    async_session_factory,
) -> None:
    http = _FakeHTTPClient(
        content=(b"<html><body>capture-rule: building_height_limit_m=80m</body></html>")
    )
    service = OfficialSourceIngestionService(http_client=http)
    source_gaps = [
        {
            "field": "building_height_limit_m",
            "reason": "not_resolved_from_current_registry",
            "candidate_sources": [
                {
                    "authority": "URA",
                    "title": "Development Control Guidelines and control plans",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                }
            ],
        }
    ]

    async with async_session_factory() as session:
        result = await service.ingest_source_gaps(
            session,
            jurisdiction="SG",
            zone_code="SG:business_park",
            source_gaps=source_gaps,
        )
        await session.commit()

    assert result.resolved_count == 1
    assert result.staged_count == 0
    payload = result.as_rule_corpus_payload()
    assert payload["resolved_count"] == 1
    assert payload["candidates"][0]["status"] == "resolved"

    async with async_session_factory() as session:
        rules = (await session.execute(select(RefRule))).scalars().all()

    assert len(rules) == 1
    rule = rules[0]
    assert rule.parameter_key == "zoning.max_building_height_m"
    assert rule.value == "80"
    assert rule.unit == "m"
    assert rule.review_status == "approved"
    assert rule.is_published is True
    assert rule.applicability == {"zone_code": "SG:business_park"}
    assert rule.source_provenance["field"] == "building_height_limit_m"
    assert rule.source_provenance["ingestion_stage"] == "official_source_normalized"


@pytest.mark.asyncio
async def test_official_source_ingestion_resolves_configured_registry_height_limit_without_fetch(
    async_session_factory,
) -> None:
    http = _FakeHTTPClient(status_code=503)
    service = OfficialSourceIngestionService(http_client=http)
    source_gaps = [
        {
            "field": "building_height_limit_m",
            "reason": "not_resolved_from_current_registry",
            "candidate_sources": [
                {
                    "authority": "URA",
                    "title": "Development Control Guidelines and control plans",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                    "configured_values_by_zone": {"SG:industrial": "80"},
                    "unit": "m",
                }
            ],
        }
    ]

    async with async_session_factory() as session:
        result = await service.ingest_source_gaps(
            session,
            jurisdiction="SG",
            zone_code="SG:industrial",
            source_gaps=source_gaps,
        )
        await session.commit()

    assert result.resolved_count == 1
    assert result.staged_count == 0
    assert result.failed_count == 0
    assert http.calls == []

    async with async_session_factory() as session:
        rules = (await session.execute(select(RefRule))).scalars().all()

    assert len(rules) == 1
    rule = rules[0]
    assert rule.parameter_key == "zoning.max_building_height_m"
    assert rule.value == "80"
    assert rule.unit == "m"
    assert rule.applicability == {"zone_code": "SG:industrial"}
    assert rule.review_status == "approved"
    assert rule.is_published is True
    assert rule.source_provenance["normalization_method"] == (
        "configured_official_source_registry"
    )


@pytest.mark.asyncio
async def test_official_source_ingestion_resolves_configured_registry_setbacks_without_fetch(
    async_session_factory,
) -> None:
    http = _FakeHTTPClient(status_code=503)
    service = OfficialSourceIngestionService(http_client=http)
    source_gaps = [
        {
            "field": "setbacks",
            "reason": "not_resolved_from_current_registry",
            "candidate_sources": [
                {
                    "authority": "URA",
                    "title": "Development Control Guidelines - setback controls",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                    "configured_values_by_zone": {
                        "SG:industrial": {
                            "front": "7.5",
                            "rear": "7.5",
                            "side": "3",
                        }
                    },
                    "unit": "m",
                }
            ],
        }
    ]

    async with async_session_factory() as session:
        result = await service.ingest_source_gaps(
            session,
            jurisdiction="SG",
            zone_code="SG:industrial",
            source_gaps=source_gaps,
        )
        await session.commit()

    assert result.resolved_count == 1
    assert result.staged_count == 0
    assert result.failed_count == 0
    assert http.calls == []

    async with async_session_factory() as session:
        rules = (await session.execute(select(RefRule))).scalars().all()

    rules_by_key = {rule.parameter_key: rule for rule in rules}
    assert set(rules_by_key) == {
        "zoning.setback.front_min_m",
        "zoning.setback.rear_min_m",
        "zoning.setback.side_min_m",
    }
    assert rules_by_key["zoning.setback.front_min_m"].value == "7.5"
    assert rules_by_key["zoning.setback.rear_min_m"].value == "7.5"
    assert rules_by_key["zoning.setback.side_min_m"].value == "3"
    for rule in rules:
        assert rule.unit == "m"
        assert rule.applicability == {"zone_code": "SG:industrial"}
        assert rule.review_status == "approved"
        assert rule.is_published is True
        assert rule.source_provenance["field"] == "setbacks"
        assert rule.source_provenance["normalization_method"] == (
            "configured_official_source_registry"
        )


@pytest.mark.asyncio
async def test_official_source_ingestion_reports_failed_fetch_without_rule(
    async_session_factory,
) -> None:
    http = _FakeHTTPClient(status_code=503)
    service = OfficialSourceIngestionService(http_client=http)
    source_gaps = [
        {
            "field": "air_rights_note",
            "candidate_sources": [
                {
                    "authority": "URA/CAAS",
                    "title": "Height control and aviation-related clearance sources",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                }
            ],
        }
    ]

    async with async_session_factory() as session:
        result = await service.ingest_source_gaps(
            session,
            jurisdiction="SG",
            zone_code="SG:commercial",
            source_gaps=source_gaps,
        )
        await session.commit()

    assert result.failed_count == 1
    assert result.staged_count == 0
    assert result.candidates[0].status == "failed"
    assert "HTTP 503" in (result.candidates[0].message or "")

    async with async_session_factory() as session:
        rules = (await session.execute(select(RefRule))).scalars().all()

    assert rules == []


@pytest.mark.asyncio
async def test_official_source_ingestion_deduplicates_existing_candidate(
    async_session_factory,
) -> None:
    http = _FakeHTTPClient()
    service = OfficialSourceIngestionService(http_client=http)
    source_gaps = [
        {
            "field": "step_backs",
            "candidate_sources": [
                {
                    "authority": "URA",
                    "title": "Development Control Guidelines",
                    "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
                }
            ],
        }
    ]

    async with async_session_factory() as session:
        first = await service.ingest_source_gaps(
            session,
            jurisdiction="SG",
            zone_code="SG:commercial",
            source_gaps=source_gaps,
        )
        second = await service.ingest_source_gaps(
            session,
            jurisdiction="SG",
            zone_code="SG:commercial",
            source_gaps=source_gaps,
        )
        await session.commit()

    assert first.staged_count == 1
    assert second.existing_count == 1
    assert len(http.calls) == 1

    async with async_session_factory() as session:
        rules = (await session.execute(select(RefRule))).scalars().all()

    assert len(rules) == 1
