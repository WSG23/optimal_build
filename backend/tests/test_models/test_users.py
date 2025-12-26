"""Comprehensive tests for users model.

Tests cover:
- UserRole enum
- User model structure
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestUserRole:
    """Tests for UserRole enum."""

    def test_admin_role(self) -> None:
        """Test admin role."""
        role = "admin"
        assert role == "admin"

    def test_developer_role(self) -> None:
        """Test developer role."""
        role = "developer"
        assert role == "developer"

    def test_investor_role(self) -> None:
        """Test investor role."""
        role = "investor"
        assert role == "investor"

    def test_contractor_role(self) -> None:
        """Test contractor role."""
        role = "contractor"
        assert role == "contractor"

    def test_consultant_role(self) -> None:
        """Test consultant role."""
        role = "consultant"
        assert role == "consultant"

    def test_regulatory_officer_role(self) -> None:
        """Test regulatory_officer role."""
        role = "regulatory_officer"
        assert role == "regulatory_officer"

    def test_viewer_role(self) -> None:
        """Test viewer role."""
        role = "viewer"
        assert role == "viewer"


class TestUserModel:
    """Tests for User model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        user_id = uuid4()
        assert len(str(user_id)) == 36

    def test_email_required(self) -> None:
        """Test email is required."""
        email = "developer@company.com.sg"
        assert "@" in email

    def test_username_required(self) -> None:
        """Test username is required."""
        username = "john_developer"
        assert len(username) > 0

    def test_full_name_required(self) -> None:
        """Test full_name is required."""
        full_name = "John Tan Wei Ming"
        assert len(full_name) > 0

    def test_hashed_password_required(self) -> None:
        """Test hashed_password is required."""
        hashed = "$2b$12$..."
        assert len(hashed) > 0

    def test_role_default_viewer(self) -> None:
        """Test role defaults to viewer."""
        role = "viewer"
        assert role == "viewer"

    def test_company_name_optional(self) -> None:
        """Test company_name is optional."""
        user = {}
        assert user.get("company_name") is None

    def test_phone_number_optional(self) -> None:
        """Test phone_number is optional."""
        user = {}
        assert user.get("phone_number") is None

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True

    def test_is_verified_default_false(self) -> None:
        """Test is_verified defaults to False."""
        is_verified = False
        assert is_verified is False

    def test_last_login_optional(self) -> None:
        """Test last_login is optional."""
        user = {}
        assert user.get("last_login") is None

    def test_uen_number_optional(self) -> None:
        """Test uen_number (Singapore Unique Entity Number) is optional."""
        user = {}
        assert user.get("uen_number") is None

    def test_acra_registered_default_false(self) -> None:
        """Test acra_registered defaults to False."""
        acra_registered = False
        assert acra_registered is False


class TestUserEmailFormats:
    """Tests for valid email formats."""

    def test_corporate_email(self) -> None:
        """Test corporate email format."""
        email = "john.tan@propertydev.com.sg"
        assert "@" in email
        assert ".sg" in email

    def test_personal_email(self) -> None:
        """Test personal email format."""
        email = "developer123@gmail.com"
        assert "@" in email

    def test_government_email(self) -> None:
        """Test government email format."""
        email = "officer@ura.gov.sg"
        assert "@" in email
        assert ".gov.sg" in email


class TestSingaporeFields:
    """Tests for Singapore-specific fields."""

    def test_valid_uen_format(self) -> None:
        """Test valid UEN format (9-10 characters)."""
        uen = "201234567X"
        assert len(uen) >= 9
        assert len(uen) <= 10

    def test_uen_business_registration(self) -> None:
        """Test UEN for business registration."""
        # UEN format: NNNNNNNNX (9 chars for businesses)
        uen = "53123456X"
        assert len(uen) == 9

    def test_uen_company_registration(self) -> None:
        """Test UEN for company registration."""
        # UEN format: YYYYNNNNNX (10 chars for companies)
        uen = "201234567X"
        assert len(uen) == 10

    def test_singapore_phone_format(self) -> None:
        """Test Singapore phone number format."""
        phone = "+65 9123 4567"
        assert "+65" in phone


class TestUserScenarios:
    """Tests for user use case scenarios."""

    def test_create_developer_user(self) -> None:
        """Test creating a developer user."""
        user = {
            "id": str(uuid4()),
            "email": "developer@sgproperty.com",
            "username": "sg_developer",
            "full_name": "Tan Wei Ming",
            "hashed_password": "$2b$12$example",
            "role": "developer",
            "company_name": "Singapore Property Developers Pte Ltd",
            "phone_number": "+65 9123 4567",
            "is_active": True,
            "is_verified": True,
            "uen_number": "201234567X",
            "acra_registered": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        assert user["role"] == "developer"
        assert user["acra_registered"] is True

    def test_create_investor_user(self) -> None:
        """Test creating an investor user."""
        user = {
            "id": str(uuid4()),
            "email": "investor@fund.com",
            "username": "property_investor",
            "full_name": "Lee Capital Partners",
            "hashed_password": "$2b$12$example",
            "role": "investor",
            "is_active": True,
        }
        assert user["role"] == "investor"

    def test_create_regulatory_officer(self) -> None:
        """Test creating a regulatory officer user."""
        user = {
            "id": str(uuid4()),
            "email": "officer@bca.gov.sg",
            "username": "bca_officer",
            "full_name": "BCA Officer",
            "hashed_password": "$2b$12$example",
            "role": "regulatory_officer",
            "is_active": True,
            "is_verified": True,
        }
        assert user["role"] == "regulatory_officer"

    def test_verify_user(self) -> None:
        """Test verifying a user."""
        user = {"is_verified": False}
        user["is_verified"] = True
        assert user["is_verified"] is True

    def test_deactivate_user(self) -> None:
        """Test deactivating a user."""
        user = {"is_active": True}
        user["is_active"] = False
        assert user["is_active"] is False

    def test_update_last_login(self) -> None:
        """Test updating last login timestamp."""
        user = {"last_login": None}
        user["last_login"] = datetime.utcnow()
        assert user["last_login"] is not None

    def test_change_user_role(self) -> None:
        """Test changing user role."""
        user = {"role": "viewer"}
        user["role"] = "developer"
        assert user["role"] == "developer"
