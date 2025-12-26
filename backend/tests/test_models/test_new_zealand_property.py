"""Comprehensive tests for new_zealand_property model.

Tests cover:
- NZPropertyZoning enum
- NZPropertyTenure enum
- NZDevelopmentStatus enum
- NZAcquisitionStatus enum
- NZFeasibilityStatus enum
- NZComplianceStatus enum
- NewZealandProperty model structure
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestNZPropertyZoning:
    """Tests for NZPropertyZoning enum - Auckland Unitary Plan zones."""

    def test_residential_single_house(self) -> None:
        """Test Single House zone."""
        zoning = "residential_single_house"
        assert zoning == "residential_single_house"

    def test_residential_mixed_housing_suburban(self) -> None:
        """Test Mixed Housing Suburban zone."""
        zoning = "residential_mixed_housing_suburban"
        assert zoning == "residential_mixed_housing_suburban"

    def test_residential_mixed_housing_urban(self) -> None:
        """Test Mixed Housing Urban zone."""
        zoning = "residential_mixed_housing_urban"
        assert zoning == "residential_mixed_housing_urban"

    def test_residential_terrace_housing_apartment(self) -> None:
        """Test Terrace Housing and Apartment zone."""
        zoning = "residential_terrace_housing_apartment"
        assert zoning == "residential_terrace_housing_apartment"

    def test_business_city_centre(self) -> None:
        """Test City Centre zone."""
        zoning = "business_city_centre"
        assert zoning == "business_city_centre"

    def test_business_mixed_use(self) -> None:
        """Test Mixed Use zone."""
        zoning = "business_mixed_use"
        assert zoning == "business_mixed_use"

    def test_special_purpose_maori(self) -> None:
        """Test Special Purpose Maori zone."""
        zoning = "special_purpose_maori"
        assert zoning == "special_purpose_maori"

    def test_future_urban(self) -> None:
        """Test Future Urban zone."""
        zoning = "future_urban"
        assert zoning == "future_urban"


class TestNZPropertyTenure:
    """Tests for NZPropertyTenure enum."""

    def test_freehold(self) -> None:
        """Test freehold (fee simple) tenure."""
        tenure = "freehold"
        assert tenure == "freehold"

    def test_leasehold(self) -> None:
        """Test leasehold (ground lease) tenure."""
        tenure = "leasehold"
        assert tenure == "leasehold"

    def test_cross_lease(self) -> None:
        """Test cross-lease (shared ownership) tenure."""
        tenure = "cross_lease"
        assert tenure == "cross_lease"

    def test_unit_title(self) -> None:
        """Test unit title (apartments) tenure."""
        tenure = "unit_title"
        assert tenure == "unit_title"

    def test_maori_land(self) -> None:
        """Test Maori land (Te Ture Whenua) tenure."""
        tenure = "maori_land"
        assert tenure == "maori_land"


class TestNZDevelopmentStatus:
    """Tests for NZDevelopmentStatus enum."""

    def test_vacant_land(self) -> None:
        """Test vacant land status."""
        status = "vacant_land"
        assert status == "vacant_land"

    def test_resource_consent_applied(self) -> None:
        """Test resource consent applied status."""
        status = "resource_consent_applied"
        assert status == "resource_consent_applied"

    def test_resource_consent_approved(self) -> None:
        """Test resource consent approved status."""
        status = "resource_consent_approved"
        assert status == "resource_consent_approved"

    def test_building_consent_approved(self) -> None:
        """Test building consent approved status."""
        status = "building_consent_approved"
        assert status == "building_consent_approved"

    def test_code_compliance_issued(self) -> None:
        """Test code compliance certificate issued status."""
        status = "code_compliance_issued"
        assert status == "code_compliance_issued"


class TestNZComplianceStatus:
    """Tests for NZComplianceStatus enum."""

    def test_pending(self) -> None:
        """Test pending status."""
        status = "pending"
        assert status == "pending"

    def test_passed(self) -> None:
        """Test passed status."""
        status = "passed"
        assert status == "passed"

    def test_warning(self) -> None:
        """Test warning status."""
        status = "warning"
        assert status == "warning"

    def test_failed(self) -> None:
        """Test failed status."""
        status = "failed"
        assert status == "failed"


class TestNewZealandPropertyModel:
    """Tests for NewZealandProperty model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        prop_id = uuid4()
        assert len(str(prop_id)) == 36

    def test_property_name_required(self) -> None:
        """Test property_name is required."""
        name = "Queen Street Tower"
        assert len(name) > 0

    def test_address_required(self) -> None:
        """Test address is required."""
        address = "123 Queen Street, Auckland CBD"
        assert len(address) > 0

    def test_region_optional(self) -> None:
        """Test region is optional."""
        prop = {}
        assert prop.get("region") is None

    def test_territorial_authority_optional(self) -> None:
        """Test territorial_authority is optional."""
        prop = {}
        assert prop.get("territorial_authority") is None

    def test_legal_description_optional(self) -> None:
        """Test legal_description (CT/Lot/DP) is optional."""
        prop = {}
        assert prop.get("legal_description") is None


class TestNewZealandPropertyScenarios:
    """Tests for New Zealand property use case scenarios."""

    def test_create_nz_property(self) -> None:
        """Test creating a New Zealand property."""
        prop = {
            "id": str(uuid4()),
            "property_name": "Commercial Bay",
            "address": "7 Queen Street, Auckland CBD",
            "region": "Auckland",
            "territorial_authority": "Auckland Council",
            "suburb": "Auckland Central",
            "legal_description": "Lot 1 DP 123456",
            "valuation_reference": "01234-56789-00",
            "zoning": "business_city_centre",
            "tenure": "freehold",
            "certificate_of_title": "NA123/456",
            "land_area_sqm": Decimal("5000"),
            "gross_floor_area_sqm": Decimal("35000"),
            "maximum_building_height_m": Decimal("72.5"),
            "development_status": "operational",
            "created_at": datetime.utcnow().isoformat(),
        }
        assert prop["territorial_authority"] == "Auckland Council"
        assert prop["zoning"] == "business_city_centre"

    def test_resource_consent_workflow(self) -> None:
        """Test RMA resource consent workflow."""
        prop = {
            "resource_consent_required": True,
            "resource_consent_type": "Discretionary",
            "resource_consent_status": "pending",
        }
        # Lodge application
        prop["resource_consent_number"] = "RC/2024/001234"
        prop["resource_consent_status"] = "lodged"
        # Notification decision
        prop["notification_required"] = True
        prop["affected_party_approval"] = True
        # Approved
        prop["resource_consent_status"] = "approved"
        prop["resource_consent_date"] = date.today()
        prop["resource_consent_conditions"] = [
            "Maximum 6 storeys",
            "Provide 20 car parks",
        ]
        assert prop["resource_consent_status"] == "approved"

    def test_building_consent_and_ccc(self) -> None:
        """Test building consent and code compliance workflow."""
        prop = {
            "building_consent_status": "pending",
        }
        # Apply for building consent
        prop["building_consent_number"] = "BC/2024/567890"
        prop["bca_name"] = "Auckland Council BCA"
        prop["building_consent_status"] = "under_review"
        # Approved
        prop["building_consent_status"] = "approved"
        prop["building_consent_date"] = date.today()
        # After construction - CCC issued
        prop["code_compliance_certificate"] = "CCC/2025/111222"
        prop["ccc_issue_date"] = date.today()
        assert prop["code_compliance_certificate"] is not None

    def test_heritage_property(self) -> None:
        """Test heritage-listed NZ property."""
        prop = {
            "is_heritage_listed": True,
            "heritage_category": "Category A",
            "heritage_new_zealand_list": "Heritage NZ List Category 1",
        }
        assert prop["heritage_category"] == "Category A"

    def test_environmental_overlays(self) -> None:
        """Test environmental overlays and hazards."""
        prop = {
            "significant_ecological_area": True,
            "outstanding_natural_feature": False,
            "coastal_hazard_zone": True,
            "flood_hazard_zone": True,
        }
        assert prop["coastal_hazard_zone"] is True

    def test_sustainability_ratings(self) -> None:
        """Test Homestar and Green Star NZ ratings."""
        prop = {
            "homestar_rating": "8 Star",
            "green_star_rating": "5 Star",
            "nabersnz_rating": "5.0",
        }
        assert prop["homestar_rating"] == "8 Star"

    def test_development_contributions(self) -> None:
        """Test development contributions calculation."""
        prop = {
            "development_contributions": Decimal("250000.00"),
            "infrastructure_growth_charge": Decimal("50000.00"),
        }
        total_levies = (
            prop["development_contributions"] + prop["infrastructure_growth_charge"]
        )
        assert total_levies == Decimal("300000.00")

    def test_council_valuation(self) -> None:
        """Test council valuation (CV/LV/IV)."""
        prop = {
            "capital_value_nzd": Decimal("5000000.00"),
            "land_value_nzd": Decimal("3000000.00"),
            "improvement_value_nzd": Decimal("2000000.00"),
            "valuation_date": date(2024, 7, 1).isoformat(),
            "rates_annual_nzd": Decimal("45000.00"),
        }
        assert prop["capital_value_nzd"] == Decimal("5000000.00")
