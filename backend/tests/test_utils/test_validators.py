from pathlib import Path
import sys

import pytest

BACKEND_ROOT = str(Path(__file__).resolve().parents[2])

if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

from app.utils.validators import validate_singapore_address


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
