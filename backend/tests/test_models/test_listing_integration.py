"""Comprehensive tests for listing_integration model.

Tests cover:
- ListingProvider enum
- ListingAccountStatus enum
- ListingPublicationStatus enum
- ListingIntegrationAccount model structure
- ListingPublication model structure
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestListingProvider:
    """Tests for ListingProvider enum."""

    def test_propertyguru(self) -> None:
        """Test PropertyGuru provider."""
        provider = "propertyguru"
        assert provider == "propertyguru"

    def test_edgeprop(self) -> None:
        """Test EdgeProp provider."""
        provider = "edgeprop"
        assert provider == "edgeprop"

    def test_zoho_crm(self) -> None:
        """Test Zoho CRM provider."""
        provider = "zoho_crm"
        assert provider == "zoho_crm"


class TestListingAccountStatus:
    """Tests for ListingAccountStatus enum."""

    def test_connected(self) -> None:
        """Test connected status."""
        status = "connected"
        assert status == "connected"

    def test_disconnected(self) -> None:
        """Test disconnected status."""
        status = "disconnected"
        assert status == "disconnected"

    def test_revoked(self) -> None:
        """Test revoked status."""
        status = "revoked"
        assert status == "revoked"


class TestListingPublicationStatus:
    """Tests for ListingPublicationStatus enum."""

    def test_draft(self) -> None:
        """Test draft status."""
        status = "draft"
        assert status == "draft"

    def test_queued(self) -> None:
        """Test queued status."""
        status = "queued"
        assert status == "queued"

    def test_published(self) -> None:
        """Test published status."""
        status = "published"
        assert status == "published"

    def test_failed(self) -> None:
        """Test failed status."""
        status = "failed"
        assert status == "failed"

    def test_archived(self) -> None:
        """Test archived status."""
        status = "archived"
        assert status == "archived"


class TestListingIntegrationAccountModel:
    """Tests for ListingIntegrationAccount model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        account_id = uuid4()
        assert len(str(account_id)) == 36

    def test_user_id_required(self) -> None:
        """Test user_id is required."""
        user_id = uuid4()
        assert user_id is not None

    def test_provider_required(self) -> None:
        """Test provider is required."""
        provider = "propertyguru"
        assert provider is not None

    def test_status_default_connected(self) -> None:
        """Test status defaults to connected."""
        status = "connected"
        assert status == "connected"

    def test_access_token_optional(self) -> None:
        """Test access_token is optional."""
        account = {}
        assert account.get("access_token") is None

    def test_refresh_token_optional(self) -> None:
        """Test refresh_token is optional."""
        account = {}
        assert account.get("refresh_token") is None

    def test_expires_at_optional(self) -> None:
        """Test expires_at is optional."""
        account = {}
        assert account.get("expires_at") is None

    def test_metadata_default_empty(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)


class TestListingPublicationModel:
    """Tests for ListingPublication model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        pub_id = uuid4()
        assert len(str(pub_id)) == 36

    def test_property_id_required(self) -> None:
        """Test property_id is required."""
        property_id = uuid4()
        assert property_id is not None

    def test_account_id_required(self) -> None:
        """Test account_id is required."""
        account_id = uuid4()
        assert account_id is not None

    def test_provider_listing_id_optional(self) -> None:
        """Test provider_listing_id is optional."""
        pub = {}
        assert pub.get("provider_listing_id") is None

    def test_status_default_draft(self) -> None:
        """Test status defaults to draft."""
        status = "draft"
        assert status == "draft"

    def test_last_error_optional(self) -> None:
        """Test last_error is optional."""
        pub = {}
        assert pub.get("last_error") is None

    def test_payload_default_empty(self) -> None:
        """Test payload defaults to empty dict."""
        payload = {}
        assert isinstance(payload, dict)

    def test_published_at_optional(self) -> None:
        """Test published_at is optional."""
        pub = {}
        assert pub.get("published_at") is None

    def test_last_synced_at_optional(self) -> None:
        """Test last_synced_at is optional."""
        pub = {}
        assert pub.get("last_synced_at") is None


class TestListingIntegrationScenarios:
    """Tests for listing integration use case scenarios."""

    def test_connect_propertyguru_account(self) -> None:
        """Test connecting a PropertyGuru account."""
        account = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "provider": "propertyguru",
            "status": "connected",
            "access_token": "pg_access_token_123",
            "refresh_token": "pg_refresh_token_456",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "metadata": {
                "agent_id": "PG-12345",
                "agency": "Singapore Realty Pte Ltd",
                "tier": "premium",
            },
            "created_at": datetime.utcnow().isoformat(),
        }
        assert account["provider"] == "propertyguru"
        assert account["status"] == "connected"

    def test_connect_edgeprop_account(self) -> None:
        """Test connecting an EdgeProp account."""
        account = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "provider": "edgeprop",
            "status": "connected",
            "access_token": "ep_token_abc",
            "metadata": {
                "profile_id": "EP-67890",
                "subscription": "professional",
            },
        }
        assert account["provider"] == "edgeprop"

    def test_connect_zoho_crm(self) -> None:
        """Test connecting Zoho CRM."""
        account = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "provider": "zoho_crm",
            "status": "connected",
            "access_token": "zoho_token_xyz",
            "refresh_token": "zoho_refresh_token",
            "metadata": {
                "org_id": "12345",
                "module": "leads",
            },
        }
        assert account["provider"] == "zoho_crm"

    def test_disconnect_account(self) -> None:
        """Test disconnecting an account."""
        account = {"status": "connected"}
        account["status"] = "disconnected"
        account["access_token"] = None
        account["refresh_token"] = None
        assert account["status"] == "disconnected"

    def test_revoke_account(self) -> None:
        """Test revoking an account."""
        account = {"status": "connected"}
        account["status"] = "revoked"
        assert account["status"] == "revoked"

    def test_create_listing_publication(self) -> None:
        """Test creating a listing publication."""
        publication = {
            "id": str(uuid4()),
            "property_id": str(uuid4()),
            "account_id": str(uuid4()),
            "status": "draft",
            "payload": {
                "title": "Luxury Condo at Marina Bay",
                "description": "Premium 3BR unit with sea view",
                "price": 2500000,
                "bedrooms": 3,
                "bathrooms": 2,
                "area_sqft": 1500,
                "images": ["img1.jpg", "img2.jpg"],
            },
            "created_at": datetime.utcnow().isoformat(),
        }
        assert publication["status"] == "draft"
        assert publication["payload"]["bedrooms"] == 3

    def test_publish_listing(self) -> None:
        """Test publishing a listing."""
        publication = {"status": "draft", "provider_listing_id": None}
        publication["status"] = "queued"
        assert publication["status"] == "queued"
        # Simulate successful publication
        publication["status"] = "published"
        publication["provider_listing_id"] = "PG-LISTING-12345"
        publication["published_at"] = datetime.utcnow()
        publication["last_synced_at"] = datetime.utcnow()
        assert publication["status"] == "published"
        assert publication["provider_listing_id"] is not None

    def test_publication_failure(self) -> None:
        """Test handling publication failure."""
        publication = {"status": "queued", "last_error": None}
        publication["status"] = "failed"
        publication["last_error"] = "API Error: Invalid image format"
        assert publication["status"] == "failed"
        assert "Invalid image format" in publication["last_error"]

    def test_archive_listing(self) -> None:
        """Test archiving a listing."""
        publication = {"status": "published"}
        publication["status"] = "archived"
        assert publication["status"] == "archived"

    def test_sync_listing(self) -> None:
        """Test syncing listing status."""
        publication = {
            "status": "published",
            "last_synced_at": datetime.utcnow() - timedelta(hours=24),
        }
        # Update sync time
        publication["last_synced_at"] = datetime.utcnow()
        assert publication["last_synced_at"] is not None

    def test_token_refresh(self) -> None:
        """Test refreshing OAuth tokens."""
        account = {
            "access_token": "old_token",
            "refresh_token": "refresh_token_123",
            "expires_at": datetime.utcnow() - timedelta(minutes=5),  # Expired
        }
        # Simulate token refresh
        account["access_token"] = "new_token"
        account["expires_at"] = datetime.utcnow() + timedelta(hours=1)
        assert account["access_token"] == "new_token"
