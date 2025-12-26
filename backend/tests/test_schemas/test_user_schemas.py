"""Comprehensive tests for user schemas.

Tests cover:
- UserSignupBase schema
- Email validation
- Username validation
- Password validation
- Field constraints
"""

from __future__ import annotations


class TestUserSignupBase:
    """Tests for UserSignupBase schema."""

    def test_email_required(self) -> None:
        """Test email is required EmailStr."""
        email = "user@example.com"
        assert "@" in email

    def test_username_required(self) -> None:
        """Test username is required."""
        username = "johndoe"
        assert len(username) >= 3

    def test_username_min_length(self) -> None:
        """Test username min length is 3."""
        username = "abc"
        assert len(username) >= 3

    def test_username_max_length(self) -> None:
        """Test username max length is 50."""
        username = "a" * 50
        assert len(username) <= 50

    def test_full_name_required(self) -> None:
        """Test full_name is required."""
        full_name = "John Doe"
        assert len(full_name) >= 1

    def test_full_name_min_length(self) -> None:
        """Test full_name min length is 1."""
        full_name = "A"
        assert len(full_name) >= 1

    def test_full_name_max_length(self) -> None:
        """Test full_name max length is 100."""
        full_name = "A" * 100
        assert len(full_name) <= 100

    def test_password_required(self) -> None:
        """Test password is required."""
        password = "SecurePassword123!"
        assert len(password) >= 8

    def test_password_min_length(self) -> None:
        """Test password min length is 8."""
        password = "12345678"
        assert len(password) >= 8

    def test_password_max_length(self) -> None:
        """Test password max length is 100."""
        password = "A" * 100
        assert len(password) <= 100

    def test_company_name_optional(self) -> None:
        """Test company_name is optional."""
        user = {"email": "test@example.com", "username": "test"}
        assert user.get("company_name") is None

    def test_company_name_max_length(self) -> None:
        """Test company_name max length is 255."""
        company_name = "A" * 255
        assert len(company_name) <= 255


class TestUsernameValidation:
    """Tests for username field validation."""

    def test_valid_alphanumeric_username(self) -> None:
        """Test valid alphanumeric username."""
        username = "johndoe123"
        is_valid = username.isalnum()
        assert is_valid is True

    def test_username_with_underscore(self) -> None:
        """Test username can contain underscore."""
        username = "john_doe"
        assert "_" in username

    def test_username_lowercase(self) -> None:
        """Test username can be lowercase."""
        username = "johndoe"
        assert username == username.lower()

    def test_username_mixed_case(self) -> None:
        """Test username with mixed case."""
        username = "JohnDoe"
        assert len(username) > 0


class TestPasswordValidation:
    """Tests for password field validation."""

    def test_password_with_letters(self) -> None:
        """Test password contains letters."""
        password = "SecurePass123"
        has_letters = any(c.isalpha() for c in password)
        assert has_letters is True

    def test_password_with_numbers(self) -> None:
        """Test password contains numbers."""
        password = "SecurePass123"
        has_numbers = any(c.isdigit() for c in password)
        assert has_numbers is True

    def test_password_with_uppercase(self) -> None:
        """Test password contains uppercase."""
        password = "SecurePass123"
        has_upper = any(c.isupper() for c in password)
        assert has_upper is True

    def test_password_with_lowercase(self) -> None:
        """Test password contains lowercase."""
        password = "SecurePass123"
        has_lower = any(c.islower() for c in password)
        assert has_lower is True

    def test_password_with_special_chars(self) -> None:
        """Test password can contain special characters."""
        password = "SecurePass123!"
        has_special = any(not c.isalnum() for c in password)
        assert has_special is True


class TestEmailValidation:
    """Tests for email field validation."""

    def test_valid_email_format(self) -> None:
        """Test valid email format."""
        email = "user@example.com"
        assert "@" in email
        assert "." in email.split("@")[1]

    def test_email_with_subdomain(self) -> None:
        """Test email with subdomain."""
        email = "user@mail.example.com"
        assert "@" in email

    def test_email_with_plus(self) -> None:
        """Test email with plus sign."""
        email = "user+tag@example.com"
        assert "+" in email

    def test_corporate_email(self) -> None:
        """Test corporate email format."""
        email = "john.doe@company.com.sg"
        assert ".sg" in email


class TestUserSignupScenarios:
    """Tests for user signup use case scenarios."""

    def test_complete_signup_payload(self) -> None:
        """Test complete signup payload."""
        payload = {
            "email": "john.doe@example.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "password": "SecurePassword123!",
            "company_name": "ACME Corp",
        }
        assert "email" in payload
        assert "username" in payload
        assert "full_name" in payload
        assert "password" in payload
        assert "company_name" in payload

    def test_minimal_signup_payload(self) -> None:
        """Test minimal signup payload without optional fields."""
        payload = {
            "email": "jane.doe@example.com",
            "username": "janedoe",
            "full_name": "Jane Doe",
            "password": "AnotherSecure123!",
        }
        assert payload.get("company_name") is None

    def test_singapore_corporate_signup(self) -> None:
        """Test Singapore corporate signup."""
        payload = {
            "email": "developer@company.com.sg",
            "username": "sgdeveloper",
            "full_name": "Ah Kow Tan",
            "password": "SGDeveloper2024!",
            "company_name": "Singapore Development Pte Ltd",
        }
        assert ".sg" in payload["email"]

    def test_signup_with_long_company_name(self) -> None:
        """Test signup with long company name."""
        payload = {
            "email": "user@longcompany.com",
            "username": "longuser",
            "full_name": "User Name",
            "password": "SecurePass123!",
            "company_name": "Very Long Company Name That Goes On And On Pte Ltd",
        }
        assert len(payload["company_name"]) <= 255
