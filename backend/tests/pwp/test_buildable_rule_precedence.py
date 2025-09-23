import pytest

from app.models.rkp import RefRule
from app.schemas.buildable import BuildableDefaults
from app.services.buildable import ResolvedZone, calculate_buildable

pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")


class _LayerStub:
    """Lightweight zoning layer stand-in for buildable tests."""

    def __init__(self, attributes: dict[str, float]) -> None:
        self.attributes = attributes
        self.layer_name = "TestLayer"
        self.jurisdiction = "SG"


@pytest.mark.asyncio
async def test_override_precedence_over_seeded_defaults(session) -> None:
    defaults = BuildableDefaults(
        plot_ratio=1.5,
        site_area_m2=1000.0,
        site_coverage=0.4,
        floor_height_m=3.5,
        efficiency_factor=0.75,
    )
    resolved = ResolvedZone(
        zone_code="R-PRIORITY",
        parcel=None,
        zone_layers=[
            _LayerStub(
                {
                    "plot_ratio": 1.2,
                    "front_setback_min_m": 4.0,
                }
            )
        ],
        input_kind="geometry",
    )

    seed_defaults = [
        RefRule(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            parameter_key="zoning.max_far",
            operator="<=",
            value="1.8",
            applicability={"zone_code": "R-PRIORITY"},
            source_provenance={"seed_tag": "zoning"},
            review_status="approved",
            is_published=True,
        ),
        RefRule(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            parameter_key="zoning.setback.front_min_m",
            operator=">=",
            value="5.0",
            unit="m",
            applicability={"zone_code": "R-PRIORITY"},
            source_provenance={"seed_tag": "zoning"},
            review_status="approved",
            is_published=True,
        ),
    ]

    ingested_overrides = [
        RefRule(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            parameter_key="zoning.max_far",
            operator="<=",
            value="3.2",
            applicability={"zone_code": "R-PRIORITY"},
            source_provenance={"seed_tag": "pwp_override"},
            review_status="approved",
            is_published=True,
        ),
        RefRule(
            jurisdiction="SG",
            authority="URA",
            topic="zoning",
            parameter_key="zoning.setback.front_min_m",
            operator=">=",
            value="7.5",
            unit="m",
            applicability={"zone_code": "R-PRIORITY"},
            source_provenance={"seed_tag": "pwp_override"},
            review_status="approved",
            is_published=True,
        ),
    ]

    session.add_all(seed_defaults + ingested_overrides)
    await session.flush()

    calculation = await calculate_buildable(session, resolved, defaults)

    assert calculation.metrics.gfa_cap_m2 == 3200

    rule_ids = {rule.id for rule in calculation.rules}
    override_ids = {rule.id for rule in ingested_overrides}
    assert override_ids.issubset(rule_ids)

    front_setback_rule = next(
        rule for rule in calculation.rules if rule.id == ingested_overrides[1].id
    )
    assert front_setback_rule.value == ingested_overrides[1].value
