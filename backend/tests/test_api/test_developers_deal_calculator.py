from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.api.v1 import developers_deal_calculator as calculator_api
from app.schemas.buildable import (
    BuildableCalculation,
    BuildableMetrics,
    RuleCorpusCounts,
    RuleCorpusStatus,
    ZoneSource,
)
from app.schemas.external_sources import ExternalSourceMetadata, ExternalSourceState
from app.services.agents.ura_integration import URAPropertyInfo, URAZoningInfo


class _BuildableServiceStub:
    def __init__(self, _session):
        pass

    async def calculate_parameters(self, _buildable_input):
        return BuildableCalculation(
            metrics=BuildableMetrics(
                gfa_cap_m2=17500,
                floors_max=12,
                footprint_m2=1458,
                nsa_est_m2=14350,
            ),
            zone_source=ZoneSource(
                kind="unknown",
                jurisdiction="SG",
                note="stubbed buildable result",
            ),
            rule_corpus_status=RuleCorpusStatus(
                zone_code="SG:R",
                coverage_state="approved",
                confidence="high",
                counts=RuleCorpusCounts(
                    applicable=4,
                    approved=4,
                    published=4,
                    traceable=4,
                    needs_review=0,
                    rejected=0,
                ),
                applied_rule_ids=[1001, 1002],
            ),
            rules=[],
        )


@pytest.mark.asyncio
async def test_evaluate_deal_from_address_returns_one_screen_summary(
    client,
    monkeypatch,
):
    monkeypatch.setattr(calculator_api, "BuildableService", _BuildableServiceStub)
    monkeypatch.setattr(
        calculator_api.geocoding_service,
        "geocode_details",
        AsyncMock(return_value=(1.285, 103.851, "1 Marina Boulevard")),
    )
    monkeypatch.setattr(
        calculator_api.geocoding_service,
        "get_google_geocoding_metadata",
        lambda: ExternalSourceMetadata(
            provider="google_maps",
            state=ExternalSourceState.MOCK,
            configured=False,
            synthetic=True,
            reason="test",
        ),
    )
    monkeypatch.setattr(
        calculator_api.geocoding_service,
        "get_onemap_amenities_metadata",
        lambda: ExternalSourceMetadata(
            provider="onemap",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        ),
    )
    monkeypatch.setattr(
        calculator_api.ura_service,
        "source_metadata",
        lambda: ExternalSourceMetadata(
            provider="ura",
            state=ExternalSourceState.MOCK,
            configured=False,
            synthetic=True,
            reason="test",
        ),
    )
    monkeypatch.setattr(
        calculator_api.ura_service,
        "get_zoning_info",
        AsyncMock(
            return_value=URAZoningInfo(
                zone_code="R",
                zone_description="Residential",
                plot_ratio=3.5,
                building_height_limit=48.0,
                site_coverage=45.0,
                use_groups=["Residential"],
            )
        ),
    )
    monkeypatch.setattr(
        calculator_api.ura_service,
        "get_property_info",
        AsyncMock(
            return_value=URAPropertyInfo(
                property_name="Marina Residences",
                tenure="99-year leasehold",
                site_area_sqm=5000.0,
                gfa_approved=9000.0,
                building_height=38.0,
                completion_year=2012,
            )
        ),
    )
    monkeypatch.setattr(
        calculator_api.ura_service,
        "get_existing_use",
        AsyncMock(return_value="Residential Tower"),
    )

    response = await client.post(
        "/api/v1/developers/deal-calculator/evaluate",
        json={"address": "1 Marina Boulevard"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["site"]["inputMode"] == "address"
    assert body["site"]["formattedAddress"] == "1 Marina Boulevard"
    assert body["site"]["geocodingSource"]["provider"] == "google_maps"
    assert body["buildEnvelope"]["maxBuildableGfaSqm"] == 17500
    assert body["ruleCorpusStatus"]["coverage_state"] == "approved"
    assert body["feasibilitySummary"]["max_permissible_gfa_sqm"] == 17500
    assert body["recommendedRuleIds"]
    assert body["financeSummary"]["totalCapexSgd"] is not None
    assert body["financeSummary"]["dscr"] is not None
    assert body["financeSummary"]["irr"] is not None
    assert body["financeSummary"]["moic"] is not None
    assert body["financeSummary"]["moic"] < 100
    assert body["assetBreakdowns"]


@pytest.mark.asyncio
async def test_evaluate_deal_with_manual_inputs_skips_geocoding(
    client,
    monkeypatch,
):
    monkeypatch.setattr(calculator_api, "BuildableService", _BuildableServiceStub)
    monkeypatch.setattr(
        calculator_api.geocoding_service,
        "get_google_geocoding_metadata",
        lambda: ExternalSourceMetadata(
            provider="google_maps",
            state=ExternalSourceState.UNAVAILABLE,
            configured=True,
            synthetic=False,
            reason="not used",
        ),
    )
    monkeypatch.setattr(
        calculator_api.geocoding_service,
        "get_onemap_amenities_metadata",
        lambda: ExternalSourceMetadata(
            provider="onemap",
            state=ExternalSourceState.UNAVAILABLE,
            configured=True,
            synthetic=False,
            reason="not used",
        ),
    )
    monkeypatch.setattr(
        calculator_api.ura_service,
        "source_metadata",
        lambda: ExternalSourceMetadata(
            provider="ura",
            state=ExternalSourceState.UNAVAILABLE,
            configured=True,
            synthetic=False,
            reason="not used",
        ),
    )

    response = await client.post(
        "/api/v1/developers/deal-calculator/evaluate",
        json={
            "projectName": "Manual SG Screen",
            "landUse": "commercial",
            "zoneCode": "C",
            "siteAreaSqm": 2400,
            "allowablePlotRatio": 4.8,
            "currentGfaSqm": 3200,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["site"]["inputMode"] == "manual"
    assert body["site"]["formattedAddress"] == "Manual parameters"
    assert body["site"]["coordinates"] is None
    assert body["buildEnvelope"]["siteAreaSqm"] == 2400
    assert body["buildEnvelope"]["allowablePlotRatio"] == 4.8
    assert body["financeSummary"]["equityRequiredSgd"] is not None
