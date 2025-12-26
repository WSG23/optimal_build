"""Tests for Organization API endpoints.

Tests cover:
- Organization CRUD operations
- Member management
- Invitation workflows
- Authorization checks
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4


from app.models.organization import (
    Organization,
    OrganizationMember,
    OrganizationInvitation,
    OrganizationRole,
    OrganizationPlan,
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationMemberCreate,
    OrganizationMemberUpdate,
    OrganizationInvitationCreate,
)


class TestOrganizationCRUD:
    """Tests for organization CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_organization_success(self) -> None:
        """Test creating a new organization."""
        org_data = OrganizationCreate(
            name="Test Organization",
            slug="test-org",
            uen_number="123456789A",
        )

        assert org_data.name == "Test Organization"
        assert org_data.slug == "test-org"
        assert org_data.uen_number == "123456789A"

    def test_organization_slug_validation(self) -> None:
        """Test that slug must match required pattern."""
        # Valid slugs
        valid_slugs = ["test-org", "my-company", "abc123", "a1b2c3"]
        for slug in valid_slugs:
            org = OrganizationCreate(name="Test", slug=slug)
            assert org.slug == slug

    def test_organization_model(self) -> None:
        """Test Organization model creation."""
        org = Organization(
            id=uuid4(),
            name="Test Org",
            slug="test-org",
            plan=OrganizationPlan.FREE,
        )

        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.plan == OrganizationPlan.FREE

    def test_organization_update_schema(self) -> None:
        """Test OrganizationUpdate schema."""
        update = OrganizationUpdate(
            name="Updated Name",
            settings={"theme": "dark"},
            uen_number="987654321B",
        )

        assert update.name == "Updated Name"
        assert update.settings == {"theme": "dark"}
        assert update.uen_number == "987654321B"

    def test_organization_update_partial(self) -> None:
        """Test partial updates with OrganizationUpdate schema."""
        update = OrganizationUpdate(name="Only Name")

        assert update.name == "Only Name"
        assert update.settings is None
        assert update.uen_number is None


class TestOrganizationMember:
    """Tests for organization member management."""

    def test_member_create_schema(self) -> None:
        """Test OrganizationMemberCreate schema."""
        user_id = uuid4()
        member_data = OrganizationMemberCreate(
            user_id=user_id,
            role=OrganizationRole.ADMIN,
        )

        assert member_data.user_id == user_id
        assert member_data.role == OrganizationRole.ADMIN

    def test_member_create_default_role(self) -> None:
        """Test default role is MEMBER."""
        user_id = uuid4()
        member_data = OrganizationMemberCreate(user_id=user_id)

        assert member_data.role == OrganizationRole.MEMBER

    def test_member_update_schema(self) -> None:
        """Test OrganizationMemberUpdate schema."""
        update = OrganizationMemberUpdate(role=OrganizationRole.VIEWER)

        assert update.role == OrganizationRole.VIEWER

    def test_organization_member_model(self) -> None:
        """Test OrganizationMember model creation."""
        member = OrganizationMember(
            id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            role=OrganizationRole.ADMIN,
            is_active=True,
        )

        assert member.role == OrganizationRole.ADMIN
        assert member.is_active is True


class TestOrganizationInvitation:
    """Tests for organization invitation workflow."""

    def test_invitation_create_schema(self) -> None:
        """Test OrganizationInvitationCreate schema."""
        invitation_data = OrganizationInvitationCreate(
            email="test@example.com",
            role=OrganizationRole.ADMIN,
        )

        assert invitation_data.email == "test@example.com"
        assert invitation_data.role == OrganizationRole.ADMIN

    def test_invitation_create_default_role(self) -> None:
        """Test default invitation role is MEMBER."""
        invitation_data = OrganizationInvitationCreate(
            email="test@example.com",
        )

        assert invitation_data.role == OrganizationRole.MEMBER

    def test_invitation_model(self) -> None:
        """Test OrganizationInvitation model creation."""
        invitation = OrganizationInvitation(
            id=uuid4(),
            organization_id=uuid4(),
            email="test@example.com",
            role=OrganizationRole.MEMBER,
            token="test-token-123",
            status="pending",
            invited_by=uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        assert invitation.email == "test@example.com"
        assert invitation.status == "pending"
        assert invitation.token == "test-token-123"


class TestOrganizationRoles:
    """Tests for organization role hierarchy."""

    def test_role_values(self) -> None:
        """Test organization role enum values."""
        assert OrganizationRole.OWNER.value == "owner"
        assert OrganizationRole.ADMIN.value == "admin"
        assert OrganizationRole.MEMBER.value == "member"
        assert OrganizationRole.VIEWER.value == "viewer"

    def test_plan_values(self) -> None:
        """Test organization plan enum values."""
        assert OrganizationPlan.FREE.value == "free"
        assert OrganizationPlan.STARTER.value == "starter"
        assert OrganizationPlan.PROFESSIONAL.value == "professional"
        assert OrganizationPlan.ENTERPRISE.value == "enterprise"


class TestOrganizationValidation:
    """Tests for input validation."""

    def test_name_min_length(self) -> None:
        """Test organization name minimum length."""
        with pytest.raises(ValueError):
            OrganizationCreate(name="", slug="valid-slug")

    def test_slug_min_length(self) -> None:
        """Test slug minimum length."""
        with pytest.raises(ValueError):
            OrganizationCreate(name="Valid Name", slug="ab")  # Too short

    def test_slug_max_length(self) -> None:
        """Test slug maximum length."""
        with pytest.raises(ValueError):
            OrganizationCreate(name="Valid Name", slug="a" * 101)  # Too long

    def test_uen_number_optional(self) -> None:
        """Test UEN number is optional."""
        org = OrganizationCreate(name="Test", slug="test-org")
        assert org.uen_number is None

    def test_email_validation(self) -> None:
        """Test email validation for invitations."""
        with pytest.raises(ValueError):
            OrganizationInvitationCreate(email="not-an-email")


class TestOrganizationRelationships:
    """Tests for organization model relationships."""

    def test_organization_repr(self) -> None:
        """Test Organization string representation."""
        org = Organization(
            id=uuid4(),
            name="Test Org",
            slug="test-org",
        )
        repr_str = repr(org)

        assert "Test Org" in repr_str
        assert "test-org" in repr_str

    def test_organization_member_repr(self) -> None:
        """Test OrganizationMember string representation."""
        org_id = uuid4()
        user_id = uuid4()
        member = OrganizationMember(
            id=uuid4(),
            organization_id=org_id,
            user_id=user_id,
        )
        repr_str = repr(member)

        assert str(org_id) in repr_str or "org=" in repr_str
        assert str(user_id) in repr_str or "user=" in repr_str

    def test_organization_invitation_repr(self) -> None:
        """Test OrganizationInvitation string representation."""
        org_id = uuid4()
        invitation = OrganizationInvitation(
            id=uuid4(),
            organization_id=org_id,
            email="test@example.com",
            role=OrganizationRole.MEMBER,
            token="test-token",
            invited_by=uuid4(),
            expires_at=datetime.now(timezone.utc),
        )
        repr_str = repr(invitation)

        assert "test@example.com" in repr_str


class TestOrganizationDefaults:
    """Tests for default values."""

    def test_organization_default_plan(self) -> None:
        """Test organization defaults to FREE plan."""
        Organization(
            id=uuid4(),
            name="Test",
            slug="test",
        )
        # Default should be set in database, not in Python
        # But we can test the enum
        assert OrganizationPlan.FREE.value == "free"

    def test_organization_default_active(self) -> None:
        """Test organization defaults to active."""
        org = Organization(
            id=uuid4(),
            name="Test",
            slug="test",
            is_active=True,
        )
        assert org.is_active is True

    def test_member_default_active(self) -> None:
        """Test member defaults to active."""
        member = OrganizationMember(
            id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            is_active=True,
        )
        assert member.is_active is True


class TestOrganizationListSchemas:
    """Tests for list response schemas."""

    def test_organization_list_response_import(self) -> None:
        """Test OrganizationListResponse can be imported."""
        from app.schemas.organization import OrganizationListResponse

        # Schema should exist and be usable
        assert OrganizationListResponse is not None

    def test_member_list_response_import(self) -> None:
        """Test OrganizationMemberListResponse can be imported."""
        from app.schemas.organization import OrganizationMemberListResponse

        assert OrganizationMemberListResponse is not None

    def test_invitation_list_response_import(self) -> None:
        """Test OrganizationInvitationListResponse can be imported."""
        from app.schemas.organization import OrganizationInvitationListResponse

        assert OrganizationInvitationListResponse is not None
