import importlib

import pytest

import app.utils.validators as validators


@pytest.fixture(autouse=True)
def reload_validators_module() -> None:
    importlib.reload(validators)


@pytest.mark.no_db
class TestValidators:
    def test_validate_username_accepts_alphanumeric_and_underscores(self) -> None:
        assert validators.validate_username("user_name123") == "user_name123"

    def test_validate_username_rejects_invalid_characters(self) -> None:
        with pytest.raises(ValueError):
            validators.validate_username("invalid name!")

    def test_validate_password_requires_all_character_classes(self) -> None:
        with pytest.raises(ValueError):
            validators.validate_password("lowercase1")
        with pytest.raises(ValueError):
            validators.validate_password("UPPERCASE1")
        with pytest.raises(ValueError):
            validators.validate_password("NoDigits")
        assert validators.validate_password("Valid123") == "Valid123"

    def test_validate_singapore_address_handles_edge_cases(self) -> None:
        assert not validators.validate_singapore_address("")
        assert not validators.validate_singapore_address("12 Road without postal")
        assert not validators.validate_singapore_address("No postal Singapore")
        assert validators.validate_singapore_address(
            "123 Example Road Singapore 654321"
        )

    def test_validate_postal_code_accepts_six_digits(self) -> None:
        assert validators.validate_postal_code("123456")
        assert validators.validate_postal_code("123 456")
        assert not validators.validate_postal_code("")
        assert not validators.validate_postal_code("12345A")

    def test_validate_coordinates_within_bounds(self) -> None:
        assert validators.validate_coordinates(1.3, 103.8)
        assert not validators.validate_coordinates(0.5, 103.8)
        assert not validators.validate_coordinates(1.3, 105.0)
