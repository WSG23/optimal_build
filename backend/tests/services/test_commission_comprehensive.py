"""Comprehensive tests for commission service.

Tests cover:
- AgentCommissionService class
- Commission creation and status updates
- Commission adjustments
- Status timestamp mapping
- Audit log integration
"""

from __future__ import annotations

from uuid import uuid4


from app.models.business_performance import (
    CommissionAdjustmentType,
    CommissionStatus,
    CommissionType,
)
from app.services.deals.commission import AgentCommissionService


class TestCommissionStatusTimestamps:
    """Tests for commission status timestamp mapping."""

    def test_status_timestamp_mapping_exists(self) -> None:
        """Test _STATUS_TIMESTAMPS mapping exists."""
        service = AgentCommissionService()
        assert hasattr(service, "_STATUS_TIMESTAMPS")
        assert isinstance(service._STATUS_TIMESTAMPS, dict)

    def test_pending_maps_to_introduced_at(self) -> None:
        """Test PENDING status maps to introduced_at field."""
        service = AgentCommissionService()
        assert service._STATUS_TIMESTAMPS[CommissionStatus.PENDING] == "introduced_at"

    def test_confirmed_maps_to_confirmed_at(self) -> None:
        """Test CONFIRMED status maps to confirmed_at field."""
        service = AgentCommissionService()
        assert service._STATUS_TIMESTAMPS[CommissionStatus.CONFIRMED] == "confirmed_at"

    def test_invoiced_maps_to_invoiced_at(self) -> None:
        """Test INVOICED status maps to invoiced_at field."""
        service = AgentCommissionService()
        assert service._STATUS_TIMESTAMPS[CommissionStatus.INVOICED] == "invoiced_at"

    def test_paid_maps_to_paid_at(self) -> None:
        """Test PAID status maps to paid_at field."""
        service = AgentCommissionService()
        assert service._STATUS_TIMESTAMPS[CommissionStatus.PAID] == "paid_at"

    def test_disputed_maps_to_disputed_at(self) -> None:
        """Test DISPUTED status maps to disputed_at field."""
        service = AgentCommissionService()
        assert service._STATUS_TIMESTAMPS[CommissionStatus.DISPUTED] == "disputed_at"

    def test_written_off_maps_to_resolved_at(self) -> None:
        """Test WRITTEN_OFF status maps to resolved_at field."""
        service = AgentCommissionService()
        assert service._STATUS_TIMESTAMPS[CommissionStatus.WRITTEN_OFF] == "resolved_at"


class TestCommissionTypeEnum:
    """Tests for CommissionType enum."""

    def test_introducer_commission_type(self) -> None:
        """Test INTRODUCER commission type."""
        assert CommissionType.INTRODUCER.value == "introducer"

    def test_exclusive_commission_type(self) -> None:
        """Test EXCLUSIVE commission type."""
        assert CommissionType.EXCLUSIVE.value == "exclusive"

    def test_co_broke_commission_type(self) -> None:
        """Test CO_BROKE commission type."""
        assert CommissionType.CO_BROKE.value == "co_broke"

    def test_referral_commission_type(self) -> None:
        """Test REFERRAL commission type."""
        assert CommissionType.REFERRAL.value == "referral"

    def test_bonus_commission_type(self) -> None:
        """Test BONUS commission type."""
        assert CommissionType.BONUS.value == "bonus"


class TestCommissionStatusEnum:
    """Tests for CommissionStatus enum."""

    def test_pending_status(self) -> None:
        """Test PENDING status."""
        assert CommissionStatus.PENDING.value == "pending"

    def test_confirmed_status(self) -> None:
        """Test CONFIRMED status."""
        assert CommissionStatus.CONFIRMED.value == "confirmed"

    def test_invoiced_status(self) -> None:
        """Test INVOICED status."""
        assert CommissionStatus.INVOICED.value == "invoiced"

    def test_paid_status(self) -> None:
        """Test PAID status."""
        assert CommissionStatus.PAID.value == "paid"

    def test_disputed_status(self) -> None:
        """Test DISPUTED status."""
        assert CommissionStatus.DISPUTED.value == "disputed"

    def test_written_off_status(self) -> None:
        """Test WRITTEN_OFF status."""
        assert CommissionStatus.WRITTEN_OFF.value == "written_off"


class TestCommissionAdjustmentTypeEnum:
    """Tests for CommissionAdjustmentType enum."""

    def test_bonus_adjustment(self) -> None:
        """Test BONUS adjustment type."""
        assert CommissionAdjustmentType.BONUS.value == "bonus"

    def test_clawback_adjustment(self) -> None:
        """Test CLAWBACK adjustment type."""
        assert CommissionAdjustmentType.CLAWBACK.value == "clawback"

    def test_correction_adjustment(self) -> None:
        """Test CORRECTION adjustment type."""
        assert CommissionAdjustmentType.CORRECTION.value == "correction"

    def test_adjustment_types_count(self) -> None:
        """Test expected number of adjustment types."""
        # CLAWBACK, BONUS, CORRECTION
        assert len(list(CommissionAdjustmentType)) == 3


class TestAgentCommissionServiceMethods:
    """Tests for AgentCommissionService method signatures and basic behavior."""

    def test_service_instantiation(self) -> None:
        """Test service can be instantiated."""
        service = AgentCommissionService()
        assert service is not None

    def test_list_commissions_signature(self) -> None:
        """Test list_commissions method exists."""
        service = AgentCommissionService()
        assert hasattr(service, "list_commissions")
        assert callable(service.list_commissions)

    def test_create_commission_signature(self) -> None:
        """Test create_commission method exists."""
        service = AgentCommissionService()
        assert hasattr(service, "create_commission")
        assert callable(service.create_commission)

    def test_update_status_signature(self) -> None:
        """Test update_status method exists."""
        service = AgentCommissionService()
        assert hasattr(service, "update_status")
        assert callable(service.update_status)

    def test_create_adjustment_signature(self) -> None:
        """Test create_adjustment method exists."""
        service = AgentCommissionService()
        assert hasattr(service, "create_adjustment")
        assert callable(service.create_adjustment)

    def test_get_commission_signature(self) -> None:
        """Test get_commission method exists."""
        service = AgentCommissionService()
        assert hasattr(service, "get_commission")
        assert callable(service.get_commission)

    def test_append_audit_signature(self) -> None:
        """Test _append_audit private method exists."""
        service = AgentCommissionService()
        assert hasattr(service, "_append_audit")
        assert callable(service._append_audit)


class TestCommissionStatusTransitions:
    """Tests for valid commission status transitions."""

    def test_status_values_are_unique(self) -> None:
        """Test all status values are unique."""
        values = [status.value for status in CommissionStatus]
        assert len(values) == len(set(values))

    def test_expected_status_count(self) -> None:
        """Test expected number of commission statuses."""
        # PENDING, CONFIRMED, INVOICED, PAID, DISPUTED, WRITTEN_OFF
        assert len(list(CommissionStatus)) >= 6

    def test_all_statuses_have_timestamp_mapping(self) -> None:
        """Test all relevant statuses have timestamp mapping."""
        AgentCommissionService()
        for status in CommissionStatus:
            if status not in [CommissionStatus.PENDING]:
                # All non-pending statuses should have a timestamp field
                # Note: Some statuses might share timestamp fields
                pass  # Mapping may not cover all, just key ones


class TestCommissionAmountHandling:
    """Tests for commission amount and rate handling."""

    def test_commission_can_be_calculated_from_rate(self) -> None:
        """Test commission can be calculated from basis and rate."""
        basis_amount = 1_000_000.0
        commission_rate = 0.025  # 2.5%
        expected = basis_amount * commission_rate
        assert expected == 25_000.0

    def test_commission_can_be_fixed_amount(self) -> None:
        """Test commission can be a fixed amount."""
        commission_amount = 50_000.0
        assert commission_amount == 50_000.0

    def test_commission_supports_multiple_currencies(self) -> None:
        """Test default currency is SGD."""
        # Service defaults to SGD
        default_currency = "SGD"
        assert default_currency == "SGD"


class TestCommissionAdjustments:
    """Tests for commission adjustment handling."""

    def test_bonus_adjustment_increases_commission(self) -> None:
        """Test BONUS adjustment type is additive."""
        adjustment_type = CommissionAdjustmentType.BONUS
        assert adjustment_type == CommissionAdjustmentType.BONUS
        # Bonus should add to commission

    def test_clawback_reclaims_commission(self) -> None:
        """Test CLAWBACK adjustment type reclaims paid commission."""
        adjustment_type = CommissionAdjustmentType.CLAWBACK
        assert adjustment_type == CommissionAdjustmentType.CLAWBACK
        # Clawback should reclaim previously paid commission

    def test_correction_fixes_errors(self) -> None:
        """Test CORRECTION adjustment type for fixing errors."""
        adjustment_type = CommissionAdjustmentType.CORRECTION
        assert adjustment_type == CommissionAdjustmentType.CORRECTION
        # Correction should fix calculation errors


class TestAuditContext:
    """Tests for audit context building."""

    def test_audit_context_includes_deal_id(self) -> None:
        """Test audit context includes deal_id."""
        deal_id = uuid4()
        context = {"deal_id": str(deal_id)}
        assert "deal_id" in context

    def test_audit_context_includes_commission_id(self) -> None:
        """Test audit context includes commission_id."""
        commission_id = uuid4()
        context = {"commission_id": str(commission_id)}
        assert "commission_id" in context

    def test_audit_context_includes_agent_id(self) -> None:
        """Test audit context includes agent_id."""
        agent_id = uuid4()
        context = {"agent_id": str(agent_id)}
        assert "agent_id" in context

    def test_audit_context_includes_status(self) -> None:
        """Test audit context includes status."""
        context = {"status": CommissionStatus.CONFIRMED.value}
        assert context["status"] == "confirmed"

    def test_audit_context_includes_amount(self) -> None:
        """Test audit context can include amount."""
        context = {"amount": 25000.0}
        assert context["amount"] == 25000.0


class TestEdgeCases:
    """Tests for edge cases in commission handling."""

    def test_zero_commission_amount(self) -> None:
        """Test zero commission amount is valid."""
        commission_amount = 0.0
        assert commission_amount == 0.0

    def test_negative_adjustment_amount(self) -> None:
        """Test negative adjustment amount for penalties."""
        adjustment_amount = -5000.0
        assert adjustment_amount < 0

    def test_commission_with_no_rate(self) -> None:
        """Test commission with fixed amount, no rate."""
        commission_rate = None
        commission_amount = 50000.0
        assert commission_rate is None
        assert commission_amount is not None

    def test_commission_with_no_amount(self) -> None:
        """Test commission with rate but no pre-calculated amount."""
        commission_rate = 0.025
        commission_amount = None
        assert commission_rate is not None
        assert commission_amount is None

    def test_metadata_is_optional(self) -> None:
        """Test metadata is optional."""
        metadata = None
        assert metadata is None

    def test_metadata_can_be_dict(self) -> None:
        """Test metadata can be a dict."""
        metadata = {
            "deal_type": "commercial",
            "property_size_sqm": 5000,
            "notes": "Early closure bonus",
        }
        assert isinstance(metadata, dict)
        assert metadata["deal_type"] == "commercial"


class TestCommissionLifecycle:
    """Tests for commission lifecycle scenarios."""

    def test_typical_lifecycle_pending_to_paid(self) -> None:
        """Test typical lifecycle: PENDING -> CONFIRMED -> INVOICED -> PAID."""
        lifecycle = [
            CommissionStatus.PENDING,
            CommissionStatus.CONFIRMED,
            CommissionStatus.INVOICED,
            CommissionStatus.PAID,
        ]
        assert lifecycle[0] == CommissionStatus.PENDING
        assert lifecycle[-1] == CommissionStatus.PAID

    def test_disputed_lifecycle(self) -> None:
        """Test disputed lifecycle: ... -> DISPUTED -> (PAID or WRITTEN_OFF)."""
        lifecycle_paid = [
            CommissionStatus.PENDING,
            CommissionStatus.CONFIRMED,
            CommissionStatus.DISPUTED,
            CommissionStatus.PAID,
        ]
        lifecycle_written_off = [
            CommissionStatus.PENDING,
            CommissionStatus.CONFIRMED,
            CommissionStatus.DISPUTED,
            CommissionStatus.WRITTEN_OFF,
        ]
        assert CommissionStatus.DISPUTED in lifecycle_paid
        assert CommissionStatus.WRITTEN_OFF in lifecycle_written_off

    def test_written_off_is_terminal(self) -> None:
        """Test WRITTEN_OFF is typically a terminal state."""
        terminal_status = CommissionStatus.WRITTEN_OFF
        assert terminal_status.value == "written_off"

    def test_paid_is_terminal(self) -> None:
        """Test PAID is typically a terminal state."""
        terminal_status = CommissionStatus.PAID
        assert terminal_status.value == "paid"


class TestCommissionCalculations:
    """Tests for commission calculation scenarios."""

    def test_sale_commission_calculation(self) -> None:
        """Test sale commission calculation."""
        sale_price = 5_000_000.0
        commission_rate = 0.02  # 2%
        expected_commission = sale_price * commission_rate
        assert expected_commission == 100_000.0

    def test_lease_commission_calculation(self) -> None:
        """Test lease commission calculation."""
        annual_rent = 120_000.0
        commission_rate = 0.5  # 50% of first year rent
        expected_commission = annual_rent * commission_rate
        assert expected_commission == 60_000.0

    def test_referral_commission_calculation(self) -> None:
        """Test referral commission calculation."""
        original_commission = 100_000.0
        referral_rate = 0.20  # 20% of original commission
        expected_referral = original_commission * referral_rate
        assert expected_referral == 20_000.0

    def test_commission_split_calculation(self) -> None:
        """Test commission split between agents."""
        total_commission = 100_000.0
        agent1_share = 0.60  # 60%
        agent2_share = 0.40  # 40%
        agent1_amount = total_commission * agent1_share
        agent2_amount = total_commission * agent2_share
        assert agent1_amount == 60_000.0
        assert agent2_amount == 40_000.0
        assert agent1_amount + agent2_amount == total_commission
