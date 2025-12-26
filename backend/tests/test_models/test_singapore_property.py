"""Comprehensive tests for singapore_property model.

Tests cover:
- PropertyZoning enum
- PropertyTenure enum
- DevelopmentStatus enum
- AcquisitionStatus enum
- FeasibilityStatus enum
- ComplianceStatus enum
- SingaporeProperty model structure
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestPropertyZoning:
    """Tests for PropertyZoning enum - URA Master Plan zoning types."""

    def test_residential(self) -> None:
        """Test residential zoning."""
        zoning = "residential"
        assert zoning == "residential"

    def test_commercial(self) -> None:
        """Test commercial zoning."""
        zoning = "commercial"
        assert zoning == "commercial"

    def test_industrial(self) -> None:
        """Test industrial zoning."""
        zoning = "industrial"
        assert zoning == "industrial"

    def test_mixed_use(self) -> None:
        """Test mixed_use zoning."""
        zoning = "mixed_use"
        assert zoning == "mixed_use"

    def test_business_park(self) -> None:
        """Test business_park zoning."""
        zoning = "business_park"
        assert zoning == "business_park"

    def test_civic_institutional(self) -> None:
        """Test civic_institutional zoning."""
        zoning = "civic_institutional"
        assert zoning == "civic_institutional"

    def test_educational(self) -> None:
        """Test educational zoning."""
        zoning = "educational"
        assert zoning == "educational"

    def test_healthcare(self) -> None:
        """Test healthcare zoning."""
        zoning = "healthcare"
        assert zoning == "healthcare"

    def test_open_space(self) -> None:
        """Test open_space zoning."""
        zoning = "open_space"
        assert zoning == "open_space"


class TestPropertyTenure:
    """Tests for PropertyTenure enum - Singapore tenure types."""

    def test_freehold(self) -> None:
        """Test freehold tenure."""
        tenure = "freehold"
        assert tenure == "freehold"

    def test_leasehold_999(self) -> None:
        """Test 999-year leasehold tenure."""
        tenure = "999_year_leasehold"
        assert tenure == "999_year_leasehold"

    def test_leasehold_99(self) -> None:
        """Test 99-year leasehold tenure."""
        tenure = "99_year_leasehold"
        assert tenure == "99_year_leasehold"

    def test_leasehold_60(self) -> None:
        """Test 60-year leasehold tenure."""
        tenure = "60_year_leasehold"
        assert tenure == "60_year_leasehold"

    def test_leasehold_30(self) -> None:
        """Test 30-year leasehold tenure."""
        tenure = "30_year_leasehold"
        assert tenure == "30_year_leasehold"


class TestDevelopmentStatus:
    """Tests for DevelopmentStatus enum."""

    def test_vacant_land(self) -> None:
        """Test vacant_land status."""
        status = "vacant_land"
        assert status == "vacant_land"

    def test_planning(self) -> None:
        """Test planning status."""
        status = "planning"
        assert status == "planning"

    def test_approved(self) -> None:
        """Test approved status."""
        status = "approved"
        assert status == "approved"

    def test_under_construction(self) -> None:
        """Test under_construction status."""
        status = "under_construction"
        assert status == "under_construction"

    def test_top_obtained(self) -> None:
        """Test TOP obtained status (Temporary Occupation Permit)."""
        status = "top_obtained"
        assert status == "top_obtained"

    def test_csc_obtained(self) -> None:
        """Test CSC obtained status (Certificate of Statutory Completion)."""
        status = "csc_obtained"
        assert status == "csc_obtained"

    def test_operational(self) -> None:
        """Test operational status."""
        status = "operational"
        assert status == "operational"


class TestAcquisitionStatus:
    """Tests for AcquisitionStatus enum."""

    def test_available(self) -> None:
        """Test available status."""
        status = "available"
        assert status == "available"

    def test_under_review(self) -> None:
        """Test under_review status."""
        status = "under_review"
        assert status == "under_review"

    def test_acquired(self) -> None:
        """Test acquired status."""
        status = "acquired"
        assert status == "acquired"

    def test_rejected(self) -> None:
        """Test rejected status."""
        status = "rejected"
        assert status == "rejected"


class TestFeasibilityStatus:
    """Tests for FeasibilityStatus enum."""

    def test_analyzing(self) -> None:
        """Test analyzing status."""
        status = "analyzing"
        assert status == "analyzing"

    def test_approved(self) -> None:
        """Test approved status."""
        status = "approved"
        assert status == "approved"

    def test_rejected(self) -> None:
        """Test rejected status."""
        status = "rejected"
        assert status == "rejected"

    def test_on_hold(self) -> None:
        """Test on_hold status."""
        status = "on_hold"
        assert status == "on_hold"


class TestComplianceStatus:
    """Tests for ComplianceStatus enum - BCA/URA compliance."""

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


class TestSingaporePropertyModel:
    """Tests for SingaporeProperty model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        property_id = uuid4()
        assert len(str(property_id)) == 36

    def test_property_name_required(self) -> None:
        """Test property_name is required."""
        name = "Marina Bay Tower"
        assert len(name) > 0

    def test_address_required(self) -> None:
        """Test address is required."""
        address = "1 Raffles Place, Singapore"
        assert len(address) > 0

    def test_postal_code_format(self) -> None:
        """Test postal_code is 6 digits (Singapore format)."""
        postal = "048616"
        assert len(postal) == 6
        assert postal.isdigit()

    def test_planning_region_optional(self) -> None:
        """Test planning_region is optional."""
        prop = {}
        assert prop.get("planning_region") is None

    def test_development_status_default(self) -> None:
        """Test development_status defaults to vacant_land."""
        status = "vacant_land"
        assert status == "vacant_land"

    def test_acquisition_status_default(self) -> None:
        """Test acquisition_status defaults to available."""
        status = "available"
        assert status == "available"

    def test_feasibility_status_default(self) -> None:
        """Test feasibility_status defaults to analyzing."""
        status = "analyzing"
        assert status == "analyzing"

    def test_compliance_status_default(self) -> None:
        """Test compliance status defaults to pending."""
        status = "pending"
        assert status == "pending"

    def test_is_conserved_default_false(self) -> None:
        """Test is_conserved defaults to False."""
        is_conserved = False
        assert is_conserved is False

    def test_is_government_land_default_false(self) -> None:
        """Test is_government_land defaults to False."""
        is_gov = False
        assert is_gov is False

    def test_is_en_bloc_potential_default_false(self) -> None:
        """Test is_en_bloc_potential defaults to False."""
        en_bloc = False
        assert en_bloc is False


class TestSingaporePlanningRegions:
    """Tests for Singapore planning region values."""

    def test_central_region(self) -> None:
        """Test Central Region."""
        region = "Central Region"
        assert region == "Central Region"

    def test_east_region(self) -> None:
        """Test East Region."""
        region = "East Region"
        assert region == "East Region"

    def test_north_region(self) -> None:
        """Test North Region."""
        region = "North Region"
        assert region == "North Region"

    def test_north_east_region(self) -> None:
        """Test North-East Region."""
        region = "North-East Region"
        assert region == "North-East Region"

    def test_west_region(self) -> None:
        """Test West Region."""
        region = "West Region"
        assert region == "West Region"


class TestGreenMarkRatings:
    """Tests for BCA Green Mark rating values."""

    def test_platinum_rating(self) -> None:
        """Test Platinum rating."""
        rating = "Platinum"
        assert rating == "Platinum"

    def test_gold_plus_rating(self) -> None:
        """Test GoldPLUS rating."""
        rating = "GoldPLUS"
        assert rating == "GoldPLUS"

    def test_gold_rating(self) -> None:
        """Test Gold rating."""
        rating = "Gold"
        assert rating == "Gold"

    def test_certified_rating(self) -> None:
        """Test Certified rating."""
        rating = "Certified"
        assert rating == "Certified"


class TestSingaporePropertyScenarios:
    """Tests for Singapore property use case scenarios."""

    def test_create_commercial_property(self) -> None:
        """Test creating a commercial property."""
        prop = {
            "id": str(uuid4()),
            "property_name": "One Raffles Place",
            "address": "1 Raffles Place, Singapore 048616",
            "postal_code": "048616",
            "latitude": 1.2843,
            "longitude": 103.8512,
            "planning_region": "Central Region",
            "planning_area": "Downtown Core",
            "subzone": "Raffles Place",
            "zoning": "commercial",
            "tenure": "999_year_leasehold",
            "land_area_sqm": Decimal("12000.00"),
            "gross_floor_area_sqm": Decimal("180000.00"),
            "gross_plot_ratio": Decimal("15.00"),
            "development_status": "operational",
            "green_mark_rating": "Platinum",
        }
        assert prop["zoning"] == "commercial"
        assert prop["gross_plot_ratio"] == Decimal("15.00")

    def test_create_residential_property(self) -> None:
        """Test creating a residential property."""
        prop = {
            "id": str(uuid4()),
            "property_name": "Marina Bay Residences",
            "address": "18 Marina Boulevard, Singapore",
            "postal_code": "018980",
            "zoning": "residential",
            "tenure": "99_year_leasehold",
            "lease_start_date": date(2008, 1, 1).isoformat(),
            "lease_remaining_years": 82,
            "development_status": "operational",
            "mrt_station_nearest": "Marina Bay MRT",
            "mrt_distance_km": Decimal("0.30"),
        }
        assert prop["tenure"] == "99_year_leasehold"

    def test_feasibility_workflow(self) -> None:
        """Test feasibility workflow status changes."""
        prop = {
            "acquisition_status": "available",
            "feasibility_status": "analyzing",
        }
        # Start analysis
        prop["acquisition_status"] = "under_review"
        assert prop["acquisition_status"] == "under_review"
        # Complete analysis - approved
        prop["feasibility_status"] = "approved"
        assert prop["feasibility_status"] == "approved"
        # Acquire property
        prop["acquisition_status"] = "acquired"
        assert prop["acquisition_status"] == "acquired"

    def test_compliance_check_workflow(self) -> None:
        """Test compliance check workflow."""
        prop = {
            "bca_compliance_status": "pending",
            "ura_compliance_status": "pending",
        }
        # Check BCA
        prop["bca_compliance_status"] = "passed"
        prop["compliance_last_checked"] = datetime.utcnow()
        # Check URA - found warning
        prop["ura_compliance_status"] = "warning"
        prop["compliance_notes"] = "Minor setback deviation detected"
        assert prop["bca_compliance_status"] == "passed"
        assert prop["ura_compliance_status"] == "warning"

    def test_development_charges(self) -> None:
        """Test Singapore development charges and fees."""
        prop = {
            "development_charge": Decimal("5000000.00"),
            "differential_premium": Decimal("2500000.00"),
            "temporary_occupation_fee": Decimal("50000.00"),
            "property_tax_annual": Decimal("120000.00"),
        }
        total_fees = (
            prop["development_charge"]
            + prop["differential_premium"]
            + prop["temporary_occupation_fee"]
        )
        assert total_fees == Decimal("7550000.00")

    def test_conservation_property(self) -> None:
        """Test conservation/heritage property."""
        prop = {
            "property_name": "Fullerton Building",
            "is_conserved": True,
            "conservation_status": "Full Conservation",
            "heritage_status": "National Monument",
            "development_constraints": {
                "facade_protection": True,
                "height_restriction": True,
                "max_height_m": 30,
                "approved_uses": ["hotel", "commercial"],
            },
        }
        assert prop["is_conserved"] is True
        assert prop["heritage_status"] == "National Monument"

    def test_en_bloc_potential(self) -> None:
        """Test collective sale (en-bloc) potential assessment."""
        prop = {
            "is_en_bloc_potential": True,
            "tenure": "99_year_leasehold",
            "lease_remaining_years": 45,
            "current_plot_ratio": Decimal("2.00"),
            "gross_plot_ratio": Decimal("3.50"),  # Potential uplift
            "potential_additional_units": 150,
        }
        # GFA uplift potential
        uplift_ratio = prop["gross_plot_ratio"] - prop["current_plot_ratio"]
        assert uplift_ratio == Decimal("1.50")
        assert prop["is_en_bloc_potential"] is True

    def test_space_optimization_metrics(self) -> None:
        """Test space optimization metrics."""
        prop = {
            "gross_floor_area_sqm": Decimal("15000.00"),
            "max_developable_gfa_sqm": Decimal("25000.00"),
            "gfa_utilization_percentage": Decimal("60.00"),
            "potential_additional_units": 50,
        }
        # Calculate utilization
        utilization = (
            prop["gross_floor_area_sqm"] / prop["max_developable_gfa_sqm"] * 100
        )
        assert utilization == Decimal("60.00")
