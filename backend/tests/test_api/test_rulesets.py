"""API tests for rule pack listing and validation."""

from __future__ import annotations

import asyncio

import pytest

from app.api.v1.rulesets import list_rulesets, validate_ruleset
from app.models.rulesets import InMemoryRulePackRepository
from app.schemas.rulesets import RulesetValidationRequest


async def _seed_ruleset(repository: InMemoryRulePackRepository) -> int:
    stored = await repository.replace_all(
        [
            {
                "key": "sg-residential-envelope",
                "jurisdiction": "SG",
                "authority": "URA",
                "topic": "residential",
                "version": "2024",
                "revision": 1,
                "title": "Residential envelope controls",
                "description": "Example rule pack for integration testing",
                "metadata": {"document": "URA Envelope 2024"},
                "rules": [
                    {
                        "id": "height_limit",
                        "title": "Maximum tower height",
                        "applies_to": ["tower_a", "tower_b"],
                        "predicate": {"property": "height_m", "operator": "<=", "value": 24},
                        "citations": [
                            {
                                "text": "URA Envelope Control 4.2",
                                "url": "https://example.com/ura",
                            }
                        ],
                    },
                    {
                        "id": "site_coverage",
                        "title": "Maximum site coverage",
                        "applies_to": ["site"],
                        "predicate": {
                            "all": [
                                {"property": "coverage_ratio", "operator": "<=", "value": 0.4},
                                {"property": "zoning", "in": ["residential", "mixed"]},
                            ]
                        },
                        "citations": [
                            {
                                "text": "Coverage Schedule",
                                "clause": "Table 3",
                            }
                        ],
                    },
                ],
            }
        ]
    )
    return stored[0].id if stored else 0


@pytest.fixture
def ruleset_repository() -> InMemoryRulePackRepository:
    return InMemoryRulePackRepository()


def test_list_rulesets_returns_metadata(
    ruleset_repository: InMemoryRulePackRepository,
) -> None:
    async def _run() -> None:
        await _seed_ruleset(ruleset_repository)

        payload = await list_rulesets(repository=ruleset_repository)
        assert payload["count"] == 1
        item = payload["items"][0]
        assert item["key"] == "sg-residential-envelope"
        assert item["jurisdiction"] == "SG"
        assert len(item["rules"]) == 2
        citation = item["rules"][0]["citations"][0]
        assert citation["text"].startswith("URA Envelope Control")

    asyncio.run(_run())


def test_validate_ruleset_returns_offending_geometries(
    ruleset_repository: InMemoryRulePackRepository,
) -> None:
    async def _run() -> None:
        ruleset_id = await _seed_ruleset(ruleset_repository)

        request = RulesetValidationRequest(
            ruleset_id=ruleset_id,
            geometries={
                "tower_a": {"height_m": 22},
                "tower_b": {"height_m": 26},
                "site": {"coverage_ratio": 0.42, "zoning": "residential"},
            },
        )
        payload = await validate_ruleset(payload=request, repository=ruleset_repository)
        assert payload["ruleset"]["id"] == ruleset_id
        assert payload["valid"] is False

        height_rule = next(
            item for item in payload["results"] if item["rule_id"] == "height_limit"
        )
        assert height_rule["citations"][0]["text"] == "URA Envelope Control 4.2"
        assert height_rule["offending_geometry_ids"] == ["tower_b"]
        tower_b_eval = next(
            ev for ev in height_rule["evaluations"] if ev["geometry_id"] == "tower_b"
        )
        assert tower_b_eval["passed"] is False
        assert tower_b_eval["trace"]["type"] == "comparison"

        coverage_rule = next(
            item for item in payload["results"] if item["rule_id"] == "site_coverage"
        )
        assert coverage_rule["passed"] is False
        assert coverage_rule["offending_geometry_ids"] == ["site"]
        trace = coverage_rule["evaluations"][0]["trace"]
        assert trace["type"] == "all"
        first_child = trace["children"][0]
        assert first_child["details"]["operator"] == "<="

    asyncio.run(_run())

