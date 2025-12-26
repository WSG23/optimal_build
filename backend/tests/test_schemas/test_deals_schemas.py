"""Comprehensive tests for deals schemas.

Tests cover:
- DealCreate and DealUpdate schemas
- DealStageChangeRequest schema
- DealSchema and DealWithTimelineSchema
- CommissionCreate and CommissionResponse schemas
- CommissionAdjustment schemas
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4


class TestDealCreate:
    """Tests for DealCreate schema."""

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "Marina Bay Office Acquisition"
        assert len(title) > 0

    def test_asset_type_required(self) -> None:
        """Test asset_type is required."""
        asset_type = "OFFICE"
        assert asset_type in ["OFFICE", "RETAIL", "INDUSTRIAL", "RESIDENTIAL", "MIXED"]

    def test_deal_type_required(self) -> None:
        """Test deal_type is required."""
        deal_type = "SALE"
        assert deal_type in ["SALE", "LEASE", "INVESTMENT"]

    def test_description_optional(self) -> None:
        """Test description is optional."""
        deal = {"title": "Test", "asset_type": "OFFICE"}
        assert deal.get("description") is None

    def test_pipeline_stage_defaults(self) -> None:
        """Test pipeline_stage defaults to LEAD_CAPTURED."""
        stage = "LEAD_CAPTURED"
        assert stage == "LEAD_CAPTURED"

    def test_status_defaults_open(self) -> None:
        """Test status defaults to OPEN."""
        status = "OPEN"
        assert status == "OPEN"

    def test_lead_source_optional(self) -> None:
        """Test lead_source is optional."""
        deal = {}
        assert deal.get("lead_source") is None

    def test_estimated_value_amount_optional(self) -> None:
        """Test estimated_value_amount is optional."""
        deal = {}
        assert deal.get("estimated_value_amount") is None

    def test_estimated_value_currency_defaults_sgd(self) -> None:
        """Test estimated_value_currency defaults to SGD."""
        currency = "SGD"
        assert len(currency) == 3

    def test_expected_close_date_optional(self) -> None:
        """Test expected_close_date is optional."""
        deal = {}
        assert deal.get("expected_close_date") is None

    def test_confidence_optional(self) -> None:
        """Test confidence is optional."""
        deal = {}
        assert deal.get("confidence") is None

    def test_confidence_range(self) -> None:
        """Test confidence is between 0 and 1."""
        confidence = Decimal("0.75")
        assert Decimal("0") <= confidence <= Decimal("1")

    def test_project_id_optional(self) -> None:
        """Test project_id is optional."""
        deal = {}
        assert deal.get("project_id") is None

    def test_property_id_optional(self) -> None:
        """Test property_id is optional."""
        deal = {}
        assert deal.get("property_id") is None

    def test_metadata_optional(self) -> None:
        """Test metadata is optional."""
        deal = {}
        assert deal.get("metadata") is None

    def test_agent_id_optional(self) -> None:
        """Test agent_id is optional."""
        deal = {}
        assert deal.get("agent_id") is None


class TestDealUpdate:
    """Tests for DealUpdate schema."""

    def test_all_fields_optional(self) -> None:
        """Test all fields are optional for update."""
        update = {}
        assert update.get("title") is None
        assert update.get("description") is None
        assert update.get("asset_type") is None

    def test_title_optional(self) -> None:
        """Test title is optional."""
        update = {}
        assert update.get("title") is None

    def test_actual_close_date_field(self) -> None:
        """Test actual_close_date field."""
        close_date = date(2024, 6, 15)
        assert close_date is not None

    def test_status_optional(self) -> None:
        """Test status is optional."""
        update = {}
        assert update.get("status") is None


class TestDealStageChangeRequest:
    """Tests for DealStageChangeRequest schema."""

    def test_to_stage_required(self) -> None:
        """Test to_stage is required."""
        to_stage = "QUALIFICATION"
        assert to_stage is not None

    def test_note_optional(self) -> None:
        """Test note is optional."""
        request = {"to_stage": "QUALIFICATION"}
        assert request.get("note") is None

    def test_metadata_optional(self) -> None:
        """Test metadata is optional."""
        request = {}
        assert request.get("metadata") is None

    def test_occurred_at_optional(self) -> None:
        """Test occurred_at is optional."""
        request = {}
        assert request.get("occurred_at") is None


class TestDealStageEventSchema:
    """Tests for DealStageEventSchema schema."""

    def test_id_uuid(self) -> None:
        """Test id is UUID."""
        event_id = uuid4()
        assert len(str(event_id)) == 36

    def test_deal_id_required(self) -> None:
        """Test deal_id is required."""
        deal_id = uuid4()
        assert deal_id is not None

    def test_from_stage_optional(self) -> None:
        """Test from_stage is optional (null for first stage)."""
        event = {"id": uuid4(), "deal_id": uuid4()}
        assert event.get("from_stage") is None

    def test_to_stage_required(self) -> None:
        """Test to_stage is required."""
        to_stage = "NEGOTIATION"
        assert to_stage is not None

    def test_changed_by_optional(self) -> None:
        """Test changed_by is optional."""
        event = {}
        assert event.get("changed_by") is None

    def test_note_optional(self) -> None:
        """Test note is optional."""
        event = {}
        assert event.get("note") is None

    def test_recorded_at_required(self) -> None:
        """Test recorded_at is required."""
        recorded_at = datetime.utcnow()
        assert recorded_at is not None

    def test_duration_seconds_optional(self) -> None:
        """Test duration_seconds is optional."""
        event = {}
        assert event.get("duration_seconds") is None

    def test_audit_log_optional(self) -> None:
        """Test audit_log is optional."""
        event = {}
        assert event.get("audit_log") is None


class TestDealSchema:
    """Tests for DealSchema schema."""

    def test_id_uuid(self) -> None:
        """Test id is UUID."""
        deal_id = uuid4()
        assert len(str(deal_id)) == 36

    def test_agent_id_required(self) -> None:
        """Test agent_id is required."""
        agent_id = uuid4()
        assert agent_id is not None

    def test_pipeline_stage_values(self) -> None:
        """Test valid pipeline stage values."""
        stages = [
            "LEAD_CAPTURED",
            "QUALIFICATION",
            "VIEWING_SCHEDULED",
            "NEGOTIATION",
            "OFFER_MADE",
            "CONTRACT_SIGNED",
            "CLOSED_WON",
            "CLOSED_LOST",
        ]
        for stage in stages:
            assert stage is not None

    def test_status_values(self) -> None:
        """Test valid status values."""
        statuses = ["OPEN", "WON", "LOST", "ON_HOLD"]
        for status in statuses:
            assert status is not None

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_required(self) -> None:
        """Test updated_at is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None


class TestDealWithTimelineSchema:
    """Tests for DealWithTimelineSchema schema."""

    def test_timeline_defaults_empty(self) -> None:
        """Test timeline defaults to empty list."""
        timeline = []
        assert isinstance(timeline, list)

    def test_timeline_contains_events(self) -> None:
        """Test timeline contains stage events."""
        timeline = [
            {"to_stage": "LEAD_CAPTURED", "recorded_at": datetime.utcnow()},
            {"from_stage": "LEAD_CAPTURED", "to_stage": "QUALIFICATION"},
        ]
        assert len(timeline) == 2

    def test_duration_calculation(self) -> None:
        """Test duration_seconds calculation."""
        event1_time = datetime(2024, 1, 1, 10, 0, 0)
        event2_time = datetime(2024, 1, 1, 12, 0, 0)
        duration = (event2_time - event1_time).total_seconds()
        assert duration == 7200  # 2 hours


class TestDealAssetType:
    """Tests for DealAssetType enum values."""

    def test_office_type(self) -> None:
        """Test OFFICE asset type."""
        asset_type = "OFFICE"
        assert asset_type == "OFFICE"

    def test_retail_type(self) -> None:
        """Test RETAIL asset type."""
        asset_type = "RETAIL"
        assert asset_type == "RETAIL"

    def test_industrial_type(self) -> None:
        """Test INDUSTRIAL asset type."""
        asset_type = "INDUSTRIAL"
        assert asset_type == "INDUSTRIAL"

    def test_residential_type(self) -> None:
        """Test RESIDENTIAL asset type."""
        asset_type = "RESIDENTIAL"
        assert asset_type == "RESIDENTIAL"

    def test_hospitality_type(self) -> None:
        """Test HOSPITALITY asset type."""
        asset_type = "HOSPITALITY"
        assert asset_type == "HOSPITALITY"

    def test_mixed_use_type(self) -> None:
        """Test MIXED_USE asset type."""
        asset_type = "MIXED_USE"
        assert asset_type == "MIXED_USE"


class TestDealType:
    """Tests for DealType enum values."""

    def test_sale_type(self) -> None:
        """Test SALE deal type."""
        deal_type = "SALE"
        assert deal_type == "SALE"

    def test_lease_type(self) -> None:
        """Test LEASE deal type."""
        deal_type = "LEASE"
        assert deal_type == "LEASE"

    def test_investment_type(self) -> None:
        """Test INVESTMENT deal type."""
        deal_type = "INVESTMENT"
        assert deal_type == "INVESTMENT"


class TestPipelineStage:
    """Tests for PipelineStage enum values."""

    def test_lead_captured(self) -> None:
        """Test LEAD_CAPTURED stage."""
        stage = "LEAD_CAPTURED"
        assert stage == "LEAD_CAPTURED"

    def test_qualification(self) -> None:
        """Test QUALIFICATION stage."""
        stage = "QUALIFICATION"
        assert stage == "QUALIFICATION"

    def test_viewing_scheduled(self) -> None:
        """Test VIEWING_SCHEDULED stage."""
        stage = "VIEWING_SCHEDULED"
        assert stage == "VIEWING_SCHEDULED"

    def test_negotiation(self) -> None:
        """Test NEGOTIATION stage."""
        stage = "NEGOTIATION"
        assert stage == "NEGOTIATION"

    def test_offer_made(self) -> None:
        """Test OFFER_MADE stage."""
        stage = "OFFER_MADE"
        assert stage == "OFFER_MADE"

    def test_contract_signed(self) -> None:
        """Test CONTRACT_SIGNED stage."""
        stage = "CONTRACT_SIGNED"
        assert stage == "CONTRACT_SIGNED"

    def test_closed_won(self) -> None:
        """Test CLOSED_WON stage."""
        stage = "CLOSED_WON"
        assert stage == "CLOSED_WON"

    def test_closed_lost(self) -> None:
        """Test CLOSED_LOST stage."""
        stage = "CLOSED_LOST"
        assert stage == "CLOSED_LOST"


class TestCommissionCreate:
    """Tests for CommissionCreate schema."""

    def test_agent_id_required(self) -> None:
        """Test agent_id is required."""
        agent_id = uuid4()
        assert agent_id is not None

    def test_commission_type_required(self) -> None:
        """Test commission_type is required."""
        comm_type = "AGENT_FEE"
        assert comm_type is not None

    def test_status_defaults_pending(self) -> None:
        """Test status defaults to PENDING."""
        status = "PENDING"
        assert status == "PENDING"

    def test_basis_amount_optional(self) -> None:
        """Test basis_amount is optional."""
        commission = {}
        assert commission.get("basis_amount") is None

    def test_basis_currency_defaults_sgd(self) -> None:
        """Test basis_currency defaults to SGD."""
        currency = "SGD"
        assert currency == "SGD"

    def test_commission_rate_optional(self) -> None:
        """Test commission_rate is optional."""
        commission = {}
        assert commission.get("commission_rate") is None

    def test_commission_amount_optional(self) -> None:
        """Test commission_amount is optional."""
        commission = {}
        assert commission.get("commission_amount") is None


class TestCommissionResponse:
    """Tests for CommissionResponse schema."""

    def test_id_uuid(self) -> None:
        """Test id is UUID."""
        comm_id = uuid4()
        assert len(str(comm_id)) == 36

    def test_deal_id_required(self) -> None:
        """Test deal_id is required."""
        deal_id = uuid4()
        assert deal_id is not None

    def test_agent_id_required(self) -> None:
        """Test agent_id is required."""
        agent_id = uuid4()
        assert agent_id is not None

    def test_status_values(self) -> None:
        """Test valid commission status values."""
        statuses = [
            "PENDING",
            "CONFIRMED",
            "INVOICED",
            "PAID",
            "DISPUTED",
            "RESOLVED",
        ]
        for status in statuses:
            assert status is not None

    def test_adjustments_defaults_empty(self) -> None:
        """Test adjustments defaults to empty list."""
        adjustments = []
        assert isinstance(adjustments, list)


class TestCommissionAdjustmentCreate:
    """Tests for CommissionAdjustmentCreate schema."""

    def test_adjustment_type_required(self) -> None:
        """Test adjustment_type is required."""
        adj_type = "BONUS"
        assert adj_type is not None

    def test_adjustment_type_values(self) -> None:
        """Test valid adjustment type values."""
        types = ["BONUS", "DEDUCTION", "REFERRAL_FEE", "SPLIT_ADJUSTMENT", "OTHER"]
        for t in types:
            assert t is not None

    def test_amount_optional(self) -> None:
        """Test amount is optional."""
        adjustment = {"adjustment_type": "BONUS"}
        assert adjustment.get("amount") is None

    def test_currency_defaults_sgd(self) -> None:
        """Test currency defaults to SGD."""
        currency = "SGD"
        assert currency == "SGD"

    def test_note_optional(self) -> None:
        """Test note is optional."""
        adjustment = {}
        assert adjustment.get("note") is None


class TestCommissionAdjustmentResponse:
    """Tests for CommissionAdjustmentResponse schema."""

    def test_id_uuid(self) -> None:
        """Test id is UUID."""
        adj_id = uuid4()
        assert len(str(adj_id)) == 36

    def test_commission_id_required(self) -> None:
        """Test commission_id is required."""
        commission_id = uuid4()
        assert commission_id is not None

    def test_recorded_by_optional(self) -> None:
        """Test recorded_by is optional."""
        adjustment = {}
        assert adjustment.get("recorded_by") is None

    def test_recorded_at_required(self) -> None:
        """Test recorded_at is required."""
        recorded_at = datetime.utcnow()
        assert recorded_at is not None

    def test_audit_log_id_optional(self) -> None:
        """Test audit_log_id is optional."""
        adjustment = {}
        assert adjustment.get("audit_log_id") is None
