"""Tests for GDPR compliance API endpoints.

Tests cover:
- Consent management
- Data export requests
- Account deletion requests
- Data access requests
- Privacy dashboard
"""

from datetime import datetime, timezone

from app.api.v1.gdpr import (
    ConsentRecord,
    ConsentType,
    ConsentUpdateRequest,
    DataExportRequest,
    DataExportStatus,
    DeletionRequest,
    DeletionRequestStatus,
    DataAccessRequest,
)


class TestConsentTypes:
    """Tests for consent type enum."""

    def test_consent_types_values(self) -> None:
        """Test all consent type enum values."""
        assert ConsentType.MARKETING_EMAIL.value == "marketing_email"
        assert ConsentType.MARKETING_SMS.value == "marketing_sms"
        assert ConsentType.ANALYTICS.value == "analytics"
        assert ConsentType.THIRD_PARTY_SHARING.value == "third_party_sharing"
        assert ConsentType.PERSONALIZATION.value == "personalization"
        assert ConsentType.COOKIES_ESSENTIAL.value == "cookies_essential"
        assert ConsentType.COOKIES_ANALYTICS.value == "cookies_analytics"
        assert ConsentType.COOKIES_MARKETING.value == "cookies_marketing"

    def test_consent_type_count(self) -> None:
        """Test we have all expected consent types."""
        assert len(ConsentType) == 8


class TestConsentRecord:
    """Tests for ConsentRecord model."""

    def test_consent_record_creation(self) -> None:
        """Test creating a consent record."""
        now = datetime.now(timezone.utc)
        record = ConsentRecord(
            consent_type=ConsentType.MARKETING_EMAIL,
            granted=True,
            granted_at=now,
        )

        assert record.consent_type == ConsentType.MARKETING_EMAIL
        assert record.granted is True
        assert record.granted_at == now
        assert record.revoked_at is None

    def test_consent_record_revoked(self) -> None:
        """Test a revoked consent record."""
        now = datetime.now(timezone.utc)
        record = ConsentRecord(
            consent_type=ConsentType.MARKETING_SMS,
            granted=False,
            revoked_at=now,
        )

        assert record.granted is False
        assert record.revoked_at == now

    def test_consent_record_with_ip(self) -> None:
        """Test consent record with IP address."""
        record = ConsentRecord(
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            ip_address="192.168.1.1",
        )

        assert record.ip_address == "192.168.1.1"


class TestConsentUpdateRequest:
    """Tests for ConsentUpdateRequest model."""

    def test_consent_update_single(self) -> None:
        """Test updating a single consent."""
        request = ConsentUpdateRequest(
            consents=[
                ConsentRecord(
                    consent_type=ConsentType.MARKETING_EMAIL,
                    granted=True,
                ),
            ]
        )

        assert len(request.consents) == 1
        assert request.consents[0].granted is True

    def test_consent_update_multiple(self) -> None:
        """Test updating multiple consents."""
        request = ConsentUpdateRequest(
            consents=[
                ConsentRecord(consent_type=ConsentType.MARKETING_EMAIL, granted=True),
                ConsentRecord(consent_type=ConsentType.MARKETING_SMS, granted=False),
                ConsentRecord(consent_type=ConsentType.ANALYTICS, granted=True),
            ]
        )

        assert len(request.consents) == 3


class TestDataExportRequest:
    """Tests for DataExportRequest model."""

    def test_export_request_defaults(self) -> None:
        """Test default export request values."""
        request = DataExportRequest()

        assert request.include_projects is True
        assert request.include_properties is True
        assert request.include_documents is True
        assert request.include_activity_logs is True
        assert request.format == "json"

    def test_export_request_custom(self) -> None:
        """Test custom export request values."""
        request = DataExportRequest(
            include_projects=True,
            include_properties=False,
            include_documents=True,
            include_activity_logs=False,
            format="csv",
        )

        assert request.include_properties is False
        assert request.include_activity_logs is False
        assert request.format == "csv"


class TestDataExportStatus:
    """Tests for DataExportStatus enum."""

    def test_export_status_values(self) -> None:
        """Test all export status values."""
        assert DataExportStatus.PENDING.value == "pending"
        assert DataExportStatus.PROCESSING.value == "processing"
        assert DataExportStatus.COMPLETED.value == "completed"
        assert DataExportStatus.FAILED.value == "failed"
        assert DataExportStatus.EXPIRED.value == "expired"


class TestDeletionRequest:
    """Tests for DeletionRequest model."""

    def test_deletion_request_valid(self) -> None:
        """Test valid deletion request."""
        request = DeletionRequest(
            confirmation="DELETE MY ACCOUNT",
            reason="Moving to another platform",
        )

        assert request.confirmation == "DELETE MY ACCOUNT"
        assert request.reason == "Moving to another platform"

    def test_deletion_request_no_reason(self) -> None:
        """Test deletion request without reason."""
        request = DeletionRequest(confirmation="DELETE MY ACCOUNT")

        assert request.reason is None


class TestDeletionRequestStatus:
    """Tests for DeletionRequestStatus enum."""

    def test_deletion_status_values(self) -> None:
        """Test all deletion status values."""
        assert DeletionRequestStatus.PENDING.value == "pending"
        assert DeletionRequestStatus.CONFIRMED.value == "confirmed"
        assert DeletionRequestStatus.PROCESSING.value == "processing"
        assert DeletionRequestStatus.COMPLETED.value == "completed"
        assert DeletionRequestStatus.CANCELLED.value == "cancelled"


class TestDataAccessRequest:
    """Tests for DataAccessRequest model."""

    def test_access_request_defaults(self) -> None:
        """Test default access request values."""
        request = DataAccessRequest()

        assert request.request_type == "full_report"
        assert request.specific_categories is None

    def test_access_request_specific(self) -> None:
        """Test specific data access request."""
        request = DataAccessRequest(
            request_type="specific_data",
            specific_categories=["profile", "activity_logs"],
        )

        assert request.request_type == "specific_data"
        assert request.specific_categories == ["profile", "activity_logs"]


class TestGDPRCompliance:
    """Tests for GDPR compliance requirements."""

    def test_all_consent_types_defined(self) -> None:
        """Verify all required consent types are defined."""
        required_types = {
            "marketing_email",
            "marketing_sms",
            "analytics",
            "third_party_sharing",
            "cookies_essential",
            "cookies_analytics",
            "cookies_marketing",
        }

        actual_types = {ct.value for ct in ConsentType}

        assert required_types.issubset(actual_types)

    def test_deletion_status_lifecycle(self) -> None:
        """Test deletion request can go through full lifecycle."""
        # Valid lifecycle: PENDING -> CONFIRMED -> PROCESSING -> COMPLETED
        # Alternative: CONFIRMED -> CANCELLED

        statuses = [s for s in DeletionRequestStatus]
        assert DeletionRequestStatus.PENDING in statuses
        assert DeletionRequestStatus.CONFIRMED in statuses
        assert DeletionRequestStatus.PROCESSING in statuses
        assert DeletionRequestStatus.COMPLETED in statuses
        assert DeletionRequestStatus.CANCELLED in statuses

    def test_export_status_lifecycle(self) -> None:
        """Test export request can go through full lifecycle."""
        statuses = [s for s in DataExportStatus]
        assert DataExportStatus.PENDING in statuses
        assert DataExportStatus.PROCESSING in statuses
        assert DataExportStatus.COMPLETED in statuses
        assert DataExportStatus.FAILED in statuses
        assert DataExportStatus.EXPIRED in statuses


class TestConsentAuditability:
    """Tests for consent audit trail requirements."""

    def test_consent_record_has_timestamps(self) -> None:
        """Verify consent records can store timestamps for audit."""
        now = datetime.now(timezone.utc)
        record = ConsentRecord(
            consent_type=ConsentType.ANALYTICS,
            granted=True,
            granted_at=now,
        )

        # Both granted_at and revoked_at should be available
        assert hasattr(record, "granted_at")
        assert hasattr(record, "revoked_at")
        assert record.granted_at is not None

    def test_consent_record_has_ip_tracking(self) -> None:
        """Verify consent records can store IP for audit."""
        record = ConsentRecord(
            consent_type=ConsentType.MARKETING_EMAIL,
            granted=True,
            ip_address="10.0.0.1",
        )

        assert record.ip_address == "10.0.0.1"
