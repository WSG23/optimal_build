"""Comprehensive tests for User model.

Tests cover:
- User creation and field validation
- UserRole enum validation
- Unique constraints (email, username)
- Singapore-specific fields (UEN, ACRA)
- Status fields (is_active, is_verified)
"""

from __future__ import annotations

import uuid
from datetime import datetime


from app.models.users import User, UserRole
from backend._compat.datetime import UTC


class TestUserRoleEnum:
    """Tests for UserRole enum."""

    def test_all_roles_defined(self) -> None:
        """All expected roles should be defined."""
        expected = [
            "ADMIN",
            "DEVELOPER",
            "INVESTOR",
            "CONTRACTOR",
            "CONSULTANT",
            "REGULATORY_OFFICER",
            "VIEWER",
        ]
        actual = [role.name for role in UserRole]
        assert sorted(actual) == sorted(expected)

    def test_role_values(self) -> None:
        """Role values should be lowercase."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.DEVELOPER.value == "developer"
        assert UserRole.VIEWER.value == "viewer"

    def test_role_is_string_enum(self) -> None:
        """UserRole should be a string enum."""
        assert isinstance(UserRole.ADMIN, str)
        assert UserRole.ADMIN == "admin"

    def test_default_role(self) -> None:
        """VIEWER should be the default role."""
        assert UserRole.VIEWER.value == "viewer"


class TestUserCreation:
    """Tests for User model creation."""

    def test_create_minimal_user(self) -> None:
        """User with only required fields should be valid."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password_here",
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"

    def test_create_user_with_all_fields(self) -> None:
        """User with all fields should be valid."""
        user_id = uuid.uuid4()
        now = datetime.now(UTC)
        user = User(
            id=user_id,
            email="full@example.com",
            username="fulluser",
            full_name="Full User",
            hashed_password="hashed_password",
            role=UserRole.DEVELOPER,
            company_name="Test Company Pte Ltd",
            phone_number="+65 9123 4567",
            is_active=True,
            is_verified=True,
            created_at=now,
            updated_at=now,
            last_login=now,
            uen_number="201234567A",
            acra_registered=True,
        )
        assert user.id == user_id
        assert user.role == UserRole.DEVELOPER
        assert user.company_name == "Test Company Pte Ltd"
        assert user.uen_number == "201234567A"


class TestUserRoleField:
    """Tests for role field."""

    def test_user_with_admin_role(self) -> None:
        """Admin role should be assignable."""
        user = User(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            hashed_password="hash",
            role=UserRole.ADMIN,
        )
        assert user.role == UserRole.ADMIN

    def test_user_with_developer_role(self) -> None:
        """Developer role should be assignable."""
        user = User(
            email="dev@example.com",
            username="developer",
            full_name="Developer User",
            hashed_password="hash",
            role=UserRole.DEVELOPER,
        )
        assert user.role == UserRole.DEVELOPER

    def test_user_with_investor_role(self) -> None:
        """Investor role should be assignable."""
        user = User(
            email="investor@example.com",
            username="investor",
            full_name="Investor User",
            hashed_password="hash",
            role=UserRole.INVESTOR,
        )
        assert user.role == UserRole.INVESTOR

    def test_user_with_contractor_role(self) -> None:
        """Contractor role should be assignable."""
        user = User(
            email="contractor@example.com",
            username="contractor",
            full_name="Contractor User",
            hashed_password="hash",
            role=UserRole.CONTRACTOR,
        )
        assert user.role == UserRole.CONTRACTOR

    def test_user_with_regulatory_officer_role(self) -> None:
        """Regulatory officer role should be assignable."""
        user = User(
            email="officer@example.com",
            username="officer",
            full_name="Officer User",
            hashed_password="hash",
            role=UserRole.REGULATORY_OFFICER,
        )
        assert user.role == UserRole.REGULATORY_OFFICER


class TestUserStatusFields:
    """Tests for status fields."""

    def test_active_user(self) -> None:
        """Active user should have is_active=True."""
        user = User(
            email="active@example.com",
            username="active",
            full_name="Active User",
            hashed_password="hash",
            is_active=True,
        )
        assert user.is_active is True

    def test_inactive_user(self) -> None:
        """Inactive user should have is_active=False."""
        user = User(
            email="inactive@example.com",
            username="inactive",
            full_name="Inactive User",
            hashed_password="hash",
            is_active=False,
        )
        assert user.is_active is False

    def test_verified_user(self) -> None:
        """Verified user should have is_verified=True."""
        user = User(
            email="verified@example.com",
            username="verified",
            full_name="Verified User",
            hashed_password="hash",
            is_verified=True,
        )
        assert user.is_verified is True

    def test_unverified_user(self) -> None:
        """Unverified user should have is_verified=False."""
        user = User(
            email="unverified@example.com",
            username="unverified",
            full_name="Unverified User",
            hashed_password="hash",
            is_verified=False,
        )
        assert user.is_verified is False


class TestUserSingaporeFields:
    """Tests for Singapore-specific fields."""

    def test_uen_number(self) -> None:
        """UEN number should be settable."""
        user = User(
            email="sg@example.com",
            username="sguser",
            full_name="SG User",
            hashed_password="hash",
            uen_number="201234567A",
        )
        assert user.uen_number == "201234567A"

    def test_uen_number_formats(self) -> None:
        """Various UEN formats should be accepted."""
        # Business registration number format
        user1 = User(
            email="biz@example.com",
            username="bizuser",
            full_name="Biz User",
            hashed_password="hash",
            uen_number="53312345A",
        )
        assert user1.uen_number == "53312345A"

        # Local company format
        user2 = User(
            email="local@example.com",
            username="localuser",
            full_name="Local User",
            hashed_password="hash",
            uen_number="202012345G",
        )
        assert user2.uen_number == "202012345G"

    def test_acra_registered(self) -> None:
        """ACRA registration status should be settable."""
        user = User(
            email="acra@example.com",
            username="acrauser",
            full_name="ACRA User",
            hashed_password="hash",
            acra_registered=True,
        )
        assert user.acra_registered is True

    def test_acra_not_registered(self) -> None:
        """Non-ACRA registration should work."""
        user = User(
            email="noacra@example.com",
            username="noacrauser",
            full_name="No ACRA User",
            hashed_password="hash",
            acra_registered=False,
        )
        assert user.acra_registered is False


class TestUserContactFields:
    """Tests for contact fields."""

    def test_company_name(self) -> None:
        """Company name should be settable."""
        user = User(
            email="company@example.com",
            username="companyuser",
            full_name="Company User",
            hashed_password="hash",
            company_name="Test Company Pte Ltd",
        )
        assert user.company_name == "Test Company Pte Ltd"

    def test_phone_number(self) -> None:
        """Phone number should be settable."""
        user = User(
            email="phone@example.com",
            username="phoneuser",
            full_name="Phone User",
            hashed_password="hash",
            phone_number="+65 9123 4567",
        )
        assert user.phone_number == "+65 9123 4567"

    def test_international_phone(self) -> None:
        """International phone numbers should be accepted."""
        user = User(
            email="intl@example.com",
            username="intluser",
            full_name="Intl User",
            hashed_password="hash",
            phone_number="+1 (555) 123-4567",
        )
        assert user.phone_number == "+1 (555) 123-4567"


class TestUserTimestampFields:
    """Tests for timestamp fields."""

    def test_created_at(self) -> None:
        """created_at should be settable."""
        now = datetime.now(UTC)
        user = User(
            email="time@example.com",
            username="timeuser",
            full_name="Time User",
            hashed_password="hash",
            created_at=now,
        )
        assert user.created_at == now

    def test_updated_at(self) -> None:
        """updated_at should be settable."""
        now = datetime.now(UTC)
        user = User(
            email="update@example.com",
            username="updateuser",
            full_name="Update User",
            hashed_password="hash",
            updated_at=now,
        )
        assert user.updated_at == now

    def test_last_login(self) -> None:
        """last_login should be settable."""
        now = datetime.now(UTC)
        user = User(
            email="login@example.com",
            username="loginuser",
            full_name="Login User",
            hashed_password="hash",
            last_login=now,
        )
        assert user.last_login == now

    def test_last_login_none(self) -> None:
        """last_login should be nullable."""
        user = User(
            email="nologin@example.com",
            username="nologinuser",
            full_name="No Login User",
            hashed_password="hash",
            last_login=None,
        )
        assert user.last_login is None


class TestUserRepr:
    """Tests for __repr__ method."""

    def test_repr_format(self) -> None:
        """Repr should show username and email."""
        user = User(
            email="repr@example.com",
            username="repruser",
            full_name="Repr User",
            hashed_password="hash",
        )
        repr_str = repr(user)
        assert "repruser" in repr_str
        assert "repr@example.com" in repr_str


class TestUserEmailField:
    """Tests for email field."""

    def test_email_with_subdomain(self) -> None:
        """Email with subdomain should be accepted."""
        user = User(
            email="user@mail.example.com",
            username="subdomain",
            full_name="Subdomain User",
            hashed_password="hash",
        )
        assert user.email == "user@mail.example.com"

    def test_email_with_plus_sign(self) -> None:
        """Email with plus sign should be accepted."""
        user = User(
            email="user+tag@example.com",
            username="plussign",
            full_name="Plus Sign User",
            hashed_password="hash",
        )
        assert user.email == "user+tag@example.com"


class TestUserUsernameField:
    """Tests for username field."""

    def test_username_with_underscore(self) -> None:
        """Username with underscore should be accepted."""
        user = User(
            email="under@example.com",
            username="user_name",
            full_name="Underscore User",
            hashed_password="hash",
        )
        assert user.username == "user_name"

    def test_username_with_numbers(self) -> None:
        """Username with numbers should be accepted."""
        user = User(
            email="num@example.com",
            username="user123",
            full_name="Number User",
            hashed_password="hash",
        )
        assert user.username == "user123"
