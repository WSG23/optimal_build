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
    ],
)
def test_validate_coordinates_bounds(lat: float, lon: float, expected: bool) -> None:
    assert validators.validate_coordinates(lat, lon) is expected
