"""Validation utilities."""

import re

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")
UPPERCASE_PATTERN = re.compile(r"[A-Z]")
LOWERCASE_PATTERN = re.compile(r"[a-z]")
DIGIT_PATTERN = re.compile(r"[0-9]")


def validate_username(value: str) -> str:
    """Ensure usernames stay alphanumeric with optional underscores."""
    if not USERNAME_PATTERN.match(value):
        raise ValueError("Username must contain only letters, numbers, and underscores")
    return value


def validate_password(value: str) -> str:
    """Enforce minimal password complexity requirements."""
    if not UPPERCASE_PATTERN.search(value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not LOWERCASE_PATTERN.search(value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not DIGIT_PATTERN.search(value):
        raise ValueError("Password must contain at least one number")
    return value


def validate_singapore_address(address: str) -> bool:
    """
    Validate Singapore address format.

    Args:
        address: Address string to validate

    Returns:
        True if valid Singapore address format
    """
    if not address or len(address.strip()) < 10:
        return False

    address = address.strip().upper()

    # Singapore postal code pattern (6 digits)
    postal_pattern = r"\b\d{6}\b"

    # Common Singapore address patterns
    patterns = [
        r"\b\d+[A-Z]?\s+.*\s+SINGAPORE\s+\d{6}\b",  # Standard format
        r"\b\d+.*ROAD\b",  # Road addresses
        r"\b\d+.*STREET\b",  # Street addresses
        r"\b\d+.*AVENUE\b",  # Avenue addresses
        r"\b\d+.*DRIVE\b",  # Drive addresses
        r"\b\d+.*LANE\b",  # Lane addresses
        r"\b\d+.*CRESCENT\b",  # Crescent addresses
        r"\b.*SINGAPORE\s+\d{6}\b",  # Any address with Singapore + postal
    ]

    # Check if postal code exists
    if not re.search(postal_pattern, address):
        return False

    # Check if any pattern matches
    for pattern in patterns:
        if re.search(pattern, address):
            return True

    return False


def validate_postal_code(postal_code: str) -> bool:
    """
    Validate Singapore postal code.

    Args:
        postal_code: 6-digit postal code

    Returns:
        True if valid postal code format
    """
    if not postal_code:
        return False

    # Remove spaces and check if 6 digits
    postal_clean = postal_code.replace(" ", "")
    return len(postal_clean) == 6 and postal_clean.isdigit()


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate coordinates are within Singapore bounds.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        True if coordinates are within Singapore
    """
    # Singapore bounding box (approximate)
    min_lat, max_lat = 1.1, 1.5
    min_lon, max_lon = 103.6, 104.1

    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
