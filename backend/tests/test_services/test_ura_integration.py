from __future__ import annotations

import pytest

from app.services.agents.ura_integration import URAIntegrationService


@pytest.mark.asyncio
async def test_fusionopolis_mock_uses_business_research_profile() -> None:
    service = URAIntegrationService()
    try:
        address = "1 Fusionopolis Way, Singapore 138632"

        zoning = await service.get_zoning_info(address)
        existing_use = await service.get_existing_use(address)
        property_info = await service.get_property_info(address)

        assert zoning is not None
        assert zoning.zone_code == "B1"
        assert zoning.zone_description == "Business 1"
        assert existing_use == "Office / Research and Development"
        assert property_info is not None
        assert property_info.property_name == "Fusionopolis"
        assert property_info.site_area_sqm == 12000.0
        assert property_info.gfa_approved == 30000.0
    finally:
        await service.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "address",
    [
        "28 Soon Lee Rd, Singapore 628083",
        "10 Pioneer Road North, Singapore 628461",
        "8 Jurong Town Hall Road, Singapore 609434",
    ],
)
async def test_western_industrial_mock_addresses_use_business_profile(
    address: str,
) -> None:
    service = URAIntegrationService()
    try:
        zoning = await service.get_zoning_info(address)

        assert zoning is not None
        assert zoning.zone_code == "B1"
        assert zoning.zone_description == "Business 1"
        assert "Light Industrial" in zoning.use_groups
    finally:
        await service.close()
