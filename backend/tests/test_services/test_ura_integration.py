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
