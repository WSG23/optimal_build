import sys
from pathlib import Path

import pytest

BACKEND_ROOT = str(Path(__file__).resolve().parents[2])

if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

from app.utils.validators import (
    validate_coordinates,
    validate_password,
    validate_postal_code,
    validate_singapore_address,
    validate_username,
)


# Username validation tests
def test_validate_username_accepts_alphanumeric():
    """Test that alphanumeric usernames are valid."""
    assert validate_username("user123") == "user123"


def test_validate_username_accepts_underscores():
    """Test that underscores are allowed in usernames."""
    assert validate_username("user_name_123") == "user_name_123"


def test_validate_username_rejects_spaces():
    """Test that spaces are not allowed."""
    with pytest.raises(ValueError, match="must contain only"):
        validate_username("user name")


def test_validate_username_rejects_special_characters():
    """Test that special characters are rejected."""
    with pytest.raises(ValueError, match="must contain only"):
        validate_username("user@name")


def test_validate_username_rejects_hyphens():
    """Test that hyphens are not allowed."""
    with pytest.raises(ValueError, match="must contain only"):
        validate_username("user-name")


# Password validation tests
def test_validate_password_accepts_valid_password():
    """Test that passwords meeting all requirements are valid."""
    assert validate_password("MyPass123") == "MyPass123"


def test_validate_password_rejects_no_uppercase():
    """Test that passwords without uppercase are rejected."""
    with pytest.raises(ValueError, match="uppercase"):
        validate_password("mypass123")


def test_validate_password_rejects_no_lowercase():
    """Test that passwords without lowercase are rejected."""
    with pytest.raises(ValueError, match="lowercase"):
        validate_password("MYPASS123")


def test_validate_password_rejects_no_digit():
    """Test that passwords without digits are rejected."""
    with pytest.raises(ValueError, match="number"):
        validate_password("MyPassword")


def test_validate_password_accepts_with_special_chars():
    """Test that passwords with special characters are accepted."""
    assert validate_password("MyPass123!@#") == "MyPass123!@#"


# Singapore address validation tests
@pytest.mark.parametrize(
    "address",
    [
        "Not an address",
        "123 Fake Street",
        "",  # Already handled by length check
        "     ",
    ],
)
def test_validate_singapore_address_rejects_invalid_inputs(address: str) -> None:
    assert validate_singapore_address(address) is False


def test_validate_singapore_address_accepts_valid_input() -> None:
    assert (
        validate_singapore_address(
            "10 ANSON ROAD #10-01 INTERNATIONAL PLAZA SINGAPORE 079903"
        )
        is True
    )


def test_validate_singapore_address_accepts_road_format():
    """Test various Singapore road address formats."""
    assert validate_singapore_address("123 Orchard Road Singapore 238858") is True


def test_validate_singapore_address_accepts_street_format():
    """Test Singapore street address format."""
    assert validate_singapore_address("45 Beach Street Singapore 189762") is True


def test_validate_singapore_address_accepts_avenue_format():
    """Test Singapore avenue address format."""
    assert (
        validate_singapore_address("10 Telok Blangah Avenue Singapore 109178") is True
    )


def test_validate_singapore_address_accepts_drive_format():
    """Test Singapore drive address format."""
    assert validate_singapore_address("5 Depot Drive Singapore 109681") is True


def test_validate_singapore_address_accepts_lane_format():
    """Test Singapore lane address format."""
    assert validate_singapore_address("12 Tech Lane Singapore 238801") is True


def test_validate_singapore_address_accepts_crescent_format():
    """Test Singapore crescent address format."""
    assert (
        validate_singapore_address("25 Hume Crescent Singapore 567890") is True
    )  # Using made-up postal for testing


def test_validate_singapore_address_rejects_short_address():
    """Test that very short addresses are rejected."""
    assert validate_singapore_address("Short") is False


def test_validate_singapore_address_rejects_missing_postal():
    """Test that addresses without postal codes are rejected."""
    assert validate_singapore_address("123 Orchard Road Singapore") is False


def test_validate_singapore_address_case_insensitive():
    """Test that validation is case insensitive."""
    assert (
        validate_singapore_address("10 orchard road singapore 238858") is True
    )  # lowercase


# Postal code validation tests
def test_validate_postal_code_accepts_valid_code():
    """Test that 6-digit postal codes are valid."""
    assert validate_postal_code("238858") is True


def test_validate_postal_code_accepts_with_spaces():
    """Test that postal codes with spaces are accepted."""
    assert validate_postal_code("238 858") is True


def test_validate_postal_code_rejects_too_short():
    """Test that codes shorter than 6 digits are rejected."""
    assert validate_postal_code("12345") is False


def test_validate_postal_code_rejects_too_long():
    """Test that codes longer than 6 digits are rejected."""
    assert validate_postal_code("1234567") is False


def test_validate_postal_code_rejects_non_numeric():
    """Test that non-numeric codes are rejected."""
    assert validate_postal_code("ABC123") is False


def test_validate_postal_code_rejects_empty():
    """Test that empty strings are rejected."""
    assert validate_postal_code("") is False


def test_validate_postal_code_rejects_none():
    """Test that None is rejected."""
    assert validate_postal_code(None) is False


# Coordinate validation tests
def test_validate_coordinates_accepts_valid_singapore_coords():
    """Test that coordinates within Singapore bounds are valid."""
    assert validate_coordinates(1.3521, 103.8198) is True  # Singapore city center


def test_validate_coordinates_accepts_northern_bounds():
    """Test northern boundary of Singapore."""
    assert validate_coordinates(1.47, 103.8) is True


def test_validate_coordinates_accepts_southern_bounds():
    """Test southern boundary of Singapore."""
    assert validate_coordinates(1.15, 103.8) is True


def test_validate_coordinates_accepts_eastern_bounds():
    """Test eastern boundary of Singapore."""
    assert validate_coordinates(1.3, 104.05) is True


def test_validate_coordinates_accepts_western_bounds():
    """Test western boundary of Singapore."""
    assert validate_coordinates(1.3, 103.65) is True


def test_validate_coordinates_rejects_too_far_north():
    """Test that coordinates too far north are rejected."""
    assert validate_coordinates(2.0, 103.8) is False


def test_validate_coordinates_rejects_too_far_south():
    """Test that coordinates too far south are rejected."""
    assert validate_coordinates(1.0, 103.8) is False


def test_validate_coordinates_rejects_too_far_east():
    """Test that coordinates too far east are rejected."""
    assert validate_coordinates(1.3, 105.0) is False


def test_validate_coordinates_rejects_too_far_west():
    """Test that coordinates too far west are rejected."""
    assert validate_coordinates(1.3, 103.0) is False


def test_validate_coordinates_rejects_outside_singapore():
    """Test that non-Singapore coordinates are rejected."""
    assert validate_coordinates(0.0, 0.0) is False  # Null Island
    assert validate_coordinates(40.7128, -74.0060) is False  # New York
