"""Comprehensive tests for geocoding service.

Tests cover:
- Address model
- GeocodingService class
- Mock address generation
- Mock amenities generation
- District from postal code mapping
- Haversine distance calculation
"""

from __future__ import annotations

import pytest

from app.services.geocoding import Address, GeocodingService

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestAddressModel:
    """Tests for Address model."""

    def test_full_address_required(self) -> None:
        """Test full_address is required."""
        address = Address(full_address="123 Main Street")
        assert address.full_address == "123 Main Street"

    def test_optional_fields(self) -> None:
        """Test optional fields default to None."""
        address = Address(full_address="123 Main Street")
        assert address.street_name is None
        assert address.building_name is None
        assert address.block_number is None
        assert address.postal_code is None
        assert address.district is None

    def test_country_default_singapore(self) -> None:
        """Test country defaults to Singapore."""
        address = Address(full_address="123 Main Street")
        assert address.country == "Singapore"

    def test_all_fields(self) -> None:
        """Test all fields can be set."""
        address = Address(
            full_address="123 Main Street",
            street_name="Main Street",
            building_name="Main Building",
            block_number="123",
            postal_code="123456",
            district="D01 - Raffles Place",
            country="Singapore",
        )
        assert address.street_name == "Main Street"
        assert address.building_name == "Main Building"
        assert address.block_number == "123"
        assert address.postal_code == "123456"
        assert address.district == "D01 - Raffles Place"


class TestGeocodingServiceInit:
    """Tests for GeocodingService initialization."""

    def test_onemap_base_url(self) -> None:
        """Test OneMap base URL is set."""
        service = GeocodingService()
        assert service.onemap_base_url == "https://www.onemap.gov.sg/api"


class TestMockAddress:
    """Tests for mock address generation."""

    def test_build_mock_address(self) -> None:
        """Test mock address is generated correctly."""
        address = GeocodingService._build_mock_address(1.3, 103.85)
        assert "Mock" in address.full_address
        assert address.street_name == "Mock Street"
        assert address.building_name == "Mock Building"
        assert address.block_number == "000"
        assert address.postal_code == "000000"
        assert address.district == "D00 - Mock District"
        assert address.country == "Singapore"

    def test_mock_address_includes_coordinates(self) -> None:
        """Test mock address includes coordinates in full_address."""
        address = GeocodingService._build_mock_address(1.35, 103.9)
        assert "1.35" in address.full_address
        assert "103.9" in address.full_address


class TestMockAmenities:
    """Tests for mock amenities generation."""

    def test_mock_amenities_structure(self) -> None:
        """Test mock amenities has correct structure."""
        amenities = GeocodingService._mock_amenities()
        assert "mrt_stations" in amenities
        assert "bus_stops" in amenities
        assert "schools" in amenities
        assert "shopping_malls" in amenities
        assert "parks" in amenities

    def test_mock_amenities_have_coordinates(self) -> None:
        """Test mock amenities have latitude and longitude."""
        amenities = GeocodingService._mock_amenities(1.3, 103.85)
        for amenity in amenities["mrt_stations"]:
            assert "latitude" in amenity
            assert "longitude" in amenity
            assert "distance_m" in amenity
            assert "name" in amenity

    def test_mock_amenities_offset_from_location(self) -> None:
        """Test mock amenities are offset from provided location."""
        amenities = GeocodingService._mock_amenities(1.3, 103.85)
        mrt = amenities["mrt_stations"][0]
        assert mrt["latitude"] != 1.3  # Should be offset


class TestDistrictFromPostal:
    """Tests for _get_district_from_postal method."""

    def test_raffles_place_district(self) -> None:
        """Test postal code 01-06 maps to D01."""
        service = GeocodingService()
        district = service._get_district_from_postal("018956")
        assert district is not None
        assert "D01" in district

    def test_chinatown_district(self) -> None:
        """Test postal code 07-08 maps to D02."""
        service = GeocodingService()
        district = service._get_district_from_postal("078867")
        assert district is not None
        assert "D02" in district

    def test_orchard_district(self) -> None:
        """Test postal code 22-23 maps to D09."""
        service = GeocodingService()
        district = service._get_district_from_postal("228213")
        assert district is not None
        assert "D09" in district

    def test_invalid_postal_code(self) -> None:
        """Test invalid postal code returns None."""
        service = GeocodingService()
        assert service._get_district_from_postal("") is None
        assert service._get_district_from_postal("1") is None

    def test_unknown_postal_prefix(self) -> None:
        """Test unknown postal prefix returns None."""
        service = GeocodingService()
        assert service._get_district_from_postal("990000") is None


class TestDistanceCalculation:
    """Tests for _calculate_distance method."""

    def test_same_point_zero_distance(self) -> None:
        """Test same point returns zero distance."""
        service = GeocodingService()
        distance = service._calculate_distance(1.3, 103.85, 1.3, 103.85)
        assert distance == 0.0

    def test_known_distance(self) -> None:
        """Test calculation of known distance."""
        service = GeocodingService()
        # Roughly 1km apart
        distance = service._calculate_distance(1.3, 103.85, 1.309, 103.85)
        assert 900 < distance < 1100  # Should be roughly 1km

    def test_haversine_formula(self) -> None:
        """Test distance uses Haversine formula."""
        service = GeocodingService()
        # Singapore to Malaysia border area
        distance = service._calculate_distance(1.3, 103.85, 1.4, 103.85)
        # Should be roughly 11km
        assert 10000 < distance < 12000


class TestGeocodingScenarios:
    """Tests for geocoding use case scenarios."""

    def test_singapore_address_structure(self) -> None:
        """Test Singapore address structure."""
        address = Address(
            full_address="1 Raffles Place, Singapore 048616",
            street_name="Raffles Place",
            building_name="One Raffles Place",
            block_number="1",
            postal_code="048616",
            district="D01 - Raffles Place, Marina, Cecil",
        )
        assert address.postal_code == "048616"

    def test_hdb_address_structure(self) -> None:
        """Test HDB address structure."""
        address = Address(
            full_address="Block 123 Ang Mo Kio Avenue 3, Singapore 560123",
            street_name="Ang Mo Kio Avenue 3",
            block_number="123",
            postal_code="560123",
            district="D20 - Bishan, Ang Mo Kio",
        )
        assert address.block_number == "123"

    def test_condo_address_structure(self) -> None:
        """Test condo address structure."""
        address = Address(
            full_address="8 Marina View, Asia Square Tower 1, Singapore 018960",
            street_name="Marina View",
            building_name="Asia Square Tower 1",
            block_number="8",
            postal_code="018960",
            district="D01 - Raffles Place, Marina, Cecil",
        )
        assert address.building_name == "Asia Square Tower 1"
