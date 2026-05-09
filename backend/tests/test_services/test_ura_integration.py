from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.schemas.external_sources import ExternalSourceState
from app.services.agents.ura_integration import URAIntegrationService


def _current_contract_month() -> str:
    today = date.today()
    return f"{today.month:02d}{str(today.year)[2:]}"


@pytest.mark.asyncio
async def test_source_metadata_reports_unavailable_without_access_key() -> None:
    service = URAIntegrationService()
    try:
        service.access_key = None

        source = service.source_metadata()

        assert source.state == ExternalSourceState.UNAVAILABLE
        assert source.configured is False
        assert source.synthetic is False
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_zoning_info_returns_none_when_real_zoning_source_is_unavailable() -> (
    None
):
    service = URAIntegrationService()
    try:
        address = "1 Fusionopolis Way, Singapore 138632"

        zoning = await service.get_zoning_info(address)

        assert zoning is None
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_ura_methods_return_unavailable_values_without_access_key() -> None:
    service = URAIntegrationService()
    try:
        service.access_key = None
        address = "10 Jln Besar, #11-06 Sim Lim Tower, Singapore 208787"

        assert await service.get_existing_use(address) is None
        assert await service.get_property_info(address) is None
        assert await service.get_development_plans(1.3, 103.8) == []
        assert await service.get_transaction_data("residential", "D08") == []
        assert await service.get_rental_data("residential", "D08") == []
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_existing_use_uses_approved_residential_use_service() -> None:
    service = URAIntegrationService()
    try:
        get_ura_data = AsyncMock(return_value={"status": "Success", "isResiUse": "Y"})
        service._get_ura_data = get_ura_data

        existing_use = await service.get_existing_use(
            "10 Jln Besar, #11-06 Sim Lim Tower, Singapore 208787"
        )

        assert existing_use == "Residential"
        get_ura_data.assert_awaited_once_with(
            "EAU_Appr_Resi_Use",
            {
                "blkHouseNo": "10",
                "street": "Jln Besar",
                "storeyNo": "11",
                "unitNo": "06",
            },
        )
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_existing_use_returns_none_for_non_residential_or_unavailable() -> None:
    service = URAIntegrationService()
    try:
        service._get_ura_data = AsyncMock(
            return_value={"status": "Success", "isResiUse": "NA"}
        )

        existing_use = await service.get_existing_use(
            "1 Fusionopolis Way, Singapore 138632"
        )

        assert existing_use is None
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_transaction_data_parses_real_residential_records() -> None:
    service = URAIntegrationService()
    try:
        contract_month = _current_contract_month()
        service._fetch_residential_transactions = AsyncMock(
            return_value=[
                {
                    "project": "TURQUOISE",
                    "street": "COVE DRIVE",
                    "contractDate": contract_month,
                    "area": "203",
                    "price": "2900000",
                    "propertyType": "Condominium",
                    "tenure": "99 yrs lease commencing from 2007",
                    "typeOfSale": "3",
                    "district": "04",
                },
                {
                    "project": "OTHER",
                    "street": "OTHER STREET",
                    "contractDate": contract_month,
                    "area": "100",
                    "price": "1000000",
                    "propertyType": "Apartment",
                    "district": "08",
                },
            ]
        )

        transactions = await service.get_transaction_data("residential", "D04")

        assert len(transactions) == 1
        assert transactions[0]["project_name"] == "TURQUOISE"
        assert transactions[0]["street"] == "COVE DRIVE"
        assert transactions[0]["district"] == "D04"
        assert transactions[0]["floor_area_sqm"] == 203.0
        assert transactions[0]["price"] == 2_900_000.0
        assert transactions[0]["buyer_type"] == "Resale"
        assert transactions[0]["source"] == "ura_data_service"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_property_info_uses_matching_transaction_without_fake_fields() -> None:
    service = URAIntegrationService()
    try:
        service._fetch_residential_transactions = AsyncMock(
            return_value=[
                {
                    "project": "TURQUOISE",
                    "street": "COVE DRIVE",
                    "contractDate": _current_contract_month(),
                    "area": "203",
                    "price": "2900000",
                    "propertyType": "Condominium",
                    "tenure": "99 yrs lease commencing from 2007",
                    "district": "04",
                }
            ]
        )

        property_info = await service.get_property_info(
            "Turquoise, Cove Drive, Singapore"
        )

        assert property_info is not None
        assert property_info.property_name == "TURQUOISE"
        assert property_info.tenure == "99 yrs lease commencing from 2007"
        assert property_info.last_transaction_price == 2_900_000.0
        assert property_info.site_area_sqm is None
        assert property_info.gfa_approved is None
        assert property_info.building_height is None
        assert property_info.completion_year is None
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_development_plans_parse_pipeline_service_records() -> None:
    service = URAIntegrationService()
    try:
        get_ura_data = AsyncMock(
            return_value={
                "Status": "Success",
                "Result": [
                    {
                        "project": "EXAMPLE RESIDENCES",
                        "street": "EXAMPLE ROAD",
                        "developer": "Example Developer Pte Ltd",
                        "district": "10",
                        "totalUnits": "120",
                        "noOfCondo": "120",
                        "expectedTOPYear": "2028",
                    }
                ],
            }
        )
        service._get_ura_data = get_ura_data

        plans = await service.get_development_plans(1.3, 103.8)

        assert plans == [
            {
                "project_name": "EXAMPLE RESIDENCES",
                "developer": "Example Developer Pte Ltd",
                "status": "Pipeline",
                "gfa": None,
                "use": "Condo",
                "expected_completion": "2028",
                "district": "10",
                "total_units": 120,
                "source": "ura_data_service",
            }
        ]
        get_ura_data.assert_awaited_once_with("PMI_Resi_Pipeline")
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_rental_data_parses_real_residential_rental_records() -> None:
    service = URAIntegrationService()
    try:
        get_ura_data = AsyncMock(
            return_value={
                "Status": "Success",
                "Result": [
                    {
                        "project": "EXAMPLE RESIDENCES",
                        "street": "EXAMPLE ROAD",
                        "rental": [
                            {
                                "district": "10",
                                "areaSqft": "1200-1300",
                                "rent": "6000",
                                "leaseDate": "26q1",
                                "noOfBedRoom": "3",
                            }
                        ],
                    }
                ],
            }
        )
        service._get_ura_data = get_ura_data

        rentals = await service.get_rental_data("residential", "D10")

        assert rentals == [
            {
                "property_name": "EXAMPLE RESIDENCES",
                "property_type": "residential",
                "district": "D10",
                "floor_area_sqm": None,
                "floor_area_sqft_range": "1200-1300",
                "monthly_rent": 6000.0,
                "psf_monthly": None,
                "lease_commencement": "26q1",
                "bedrooms": "3",
                "source": "ura_data_service",
            }
        ]
        assert get_ura_data.await_args.args[0] == "PMI_Resi_Rental"
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
async def test_western_industrial_addresses_do_not_return_mock_zoning(
    address: str,
) -> None:
    service = URAIntegrationService()
    try:
        zoning = await service.get_zoning_info(address)

        assert zoning is None
    finally:
        await service.close()
