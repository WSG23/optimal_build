"""Tests for validation utilities."""

from __future__ import annotations

import pytest

from app.utils import validators


def test_validate_username_allows_alphanumeric_and_underscore() -> None:
    assert validators.validate_username("user_name123") == "user_name123"


def test_validate_username_rejects_invalid_characters() -> None:
    with pytest.raises(ValueError):
        validators.validate_username("invalid-user!")


def test_validate_password_enforces_complexity() -> None:
    assert validators.validate_password("Str0ngPass") == "Str0ngPass"

    with pytest.raises(ValueError):
        validators.validate_password("nouppercase1")
    with pytest.raises(ValueError):
        validators.validate_password("NOLOWERCASE1")
    with pytest.raises(ValueError):
        validators.validate_password("NoDigits")


def test_validate_singapore_address_patterns() -> None:
    valid = "10 Anson Road #15-01 Singapore 079903"
    invalid = "123 Example Street"  # no postal code / Singapore mention

    assert validators.validate_singapore_address(valid) is True
    assert validators.validate_singapore_address(invalid) is False


def test_validate_postal_code_formats() -> None:
    assert validators.validate_postal_code("079903") is True
    assert validators.validate_postal_code("079 903") is True
    assert validators.validate_postal_code("79903") is False
    assert validators.validate_postal_code("ABC123") is False


@pytest.mark.parametrize(
    "lat, lon, expected",
    [
        (1.3, 103.8, True),
        (1.6, 103.8, False),
        (1.3, 104.5, False),
        (1.1, 103.6, True),  # Min bounds
        (1.5, 104.1, True),  # Max bounds
        (1.0, 103.8, False),  # Below min lat
        (1.3, 103.5, False),  # Below min lon
    ],
)
def test_validate_coordinates_bounds(lat: float, lon: float, expected: bool) -> None:
    assert validators.validate_coordinates(lat, lon) is expected


def test_validate_singapore_address_comprehensive() -> None:
    """Test comprehensive Singapore address patterns."""
    # Valid addresses with different patterns
    valid_addresses = [
        "123 Example Road Singapore 123456",
        "456 Test Street Singapore 654321",
        "789A Main Avenue Singapore 789012",
        "10 Innovation Drive Singapore 138632",
        "5 Garden Lane Singapore 238855",
        "20 Marina Crescent Singapore 018981",
        "100 ORCHARD ROAD SINGAPORE 238840",  # Uppercase
        "  50 Beach Road Singapore 189763  ",  # With spaces
    ]
    for addr in valid_addresses:
        assert (
            validators.validate_singapore_address(addr) is True
        ), f"Expected {addr} to be valid"

    # Invalid addresses
    invalid_addresses = [
        "",  # Empty
        "   ",  # Whitespace only
        "Short",  # Too short
        "123 Example Road",  # No postal code
        "Example Road Singapore",  # No street number
        "123 Example Road 12345",  # 5-digit postal
        "123 Example Road 1234567",  # 7-digit postal
    ]
    for addr in invalid_addresses:
        assert (
            validators.validate_singapore_address(addr) is False
        ), f"Expected {addr} to be invalid"


def test_validate_postal_code_edge_cases() -> None:
    """Test postal code validation edge cases."""
    assert validators.validate_postal_code("") is False
    assert validators.validate_postal_code("12345") is False  # 5 digits
    assert validators.validate_postal_code("1234567") is False  # 7 digits
    assert validators.validate_postal_code("  ") is False
    assert validators.validate_postal_code("07 99 03") is True  # Multiple spaces


def test_validate_username_edge_cases() -> None:
    """Test username validation edge cases."""
    # Valid usernames
    assert validators.validate_username("a") == "a"
    assert validators.validate_username("123") == "123"
    assert validators.validate_username("_") == "_"
    assert validators.validate_username("user123_test") == "user123_test"

    # Invalid usernames
    with pytest.raises(ValueError, match="only letters, numbers, and underscores"):
        validators.validate_username("user-name")
    with pytest.raises(ValueError):
        validators.validate_username("user name")
    with pytest.raises(ValueError):
        validators.validate_username("user@name")
    with pytest.raises(ValueError):
        validators.validate_username("user.name")


def test_validate_password_edge_cases() -> None:
    """Test password validation edge cases."""
    # Valid passwords
    assert validators.validate_password("Aa1") == "Aa1"
    assert validators.validate_password("P@ssw0rd") == "P@ssw0rd"
    assert validators.validate_password("C0mpl3x!Pass") == "C0mpl3x!Pass"

    # Missing uppercase
    with pytest.raises(ValueError, match="uppercase"):
        validators.validate_password("password1")

    # Missing lowercase
    with pytest.raises(ValueError, match="lowercase"):
        validators.validate_password("PASSWORD1")

    # Missing digit
    with pytest.raises(ValueError, match="number"):
        validators.validate_password("Password")
