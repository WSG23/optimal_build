"""Comprehensive tests for the AgentDealService pipeline operations."""

from __future__ import annotations

from datetime import date
from importlib import import_module
from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

import pytest_asyncio
from app.models.audit import AuditLog
from app.models.business_performance import (
    AgentDealContact,
    AgentDealDocument,
    DealAssetType,
    DealStatus,
    DealType,
    PipelineStage,
)
from app.models.users import User
from app.schemas.deals import DealWithTimelineSchema
from app.services.deals import AgentDealService
from app.services.deals.utils import audit_project_key
from sqlalchemy import select


@pytest_asyncio.fixture(autouse=True)
async def _override_async_session_factory(
    flow_session_factory, monkeypatch
):  # pragma: no cover - test scaffolding
    module = import_module("app.core.database")
    monkeypatch.setattr(
        module,
        "AsyncSessionLocal",
        flow_session_factory,
        raising=False,
    )
    yield


# ============================================================================
# DEAL CREATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_deal_seeds_stage_event(async_session_factory):
    """Test that creating a deal seeds the initial stage event."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="agent@example.com",
                username="pipeline_agent",
                full_name="Pipeline Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Jurong Logistics Hub",
            asset_type=DealAssetType.INDUSTRIAL,
            deal_type=DealType.SELL_SIDE,
            lead_source="referral",
            metadata={"priority": "high"},
            created_by=agent_id,
        )
        assert deal.pipeline_stage == PipelineStage.LEAD_CAPTURED
        assert deal.metadata["priority"] == "high"

        timeline, audit_map = await service.timeline_with_audit(
            session=session, deal=deal
        )
        assert len(timeline) == 1
        event = timeline[0]
        assert event.to_stage == PipelineStage.LEAD_CAPTURED
        assert event.note == "Deal created"
        assert str(event.changed_by) == str(agent_id)
        assert event.metadata.get("audit_log_id") is not None

        project_key = audit_project_key(deal)
        result = await session.execute(
            select(AuditLog).where(AuditLog.project_id == project_key)
        )
        logs = result.scalars().all()
        assert len(logs) == 1
        assert logs[0].context.get("deal_id") == str(deal.id)
        assert logs[0].context.get("to_stage") == PipelineStage.LEAD_CAPTURED.value
        audit_log = audit_map.get(str(logs[0].id))
        assert audit_log is not None


@pytest.mark.asyncio
async def test_create_deal_with_all_fields(async_session_factory):
    """Test creating a deal with all optional fields populated."""
    service = AgentDealService()
    agent_id = uuid4()
    project_id = uuid4()
    property_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="full_fields@example.com",
                username="full_agent",
                full_name="Full Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Orchard Retail Space",
            asset_type=DealAssetType.RETAIL,
            deal_type=DealType.BUY_SIDE,
            description="Prime retail opportunity in Orchard",
            pipeline_stage=PipelineStage.QUALIFIED,
            status=DealStatus.OPEN,
            lead_source="cold_call",
            estimated_value_amount=5_000_000.00,
            estimated_value_currency="SGD",
            expected_close_date=date(2025, 6, 30),
            confidence=0.75,
            project_id=project_id,
            property_id=property_id,
            metadata={"region": "central"},
            created_by=agent_id,
        )

        assert deal.title == "Orchard Retail Space"
        assert deal.asset_type == DealAssetType.RETAIL
        assert deal.deal_type == DealType.BUY_SIDE
        assert deal.description == "Prime retail opportunity in Orchard"
        assert deal.pipeline_stage == PipelineStage.QUALIFIED
        assert deal.estimated_value_amount == 5_000_000.00
        assert deal.estimated_value_currency == "SGD"
        assert deal.expected_close_date == date(2025, 6, 30)
        assert deal.confidence == 0.75
        assert deal.project_id == str(project_id)
        assert deal.property_id == str(property_id)


@pytest.mark.asyncio
async def test_create_deal_uses_agent_as_created_by_default(async_session_factory):
    """Test that created_by defaults to agent_id when not specified."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="default_creator@example.com",
                username="default_agent",
                full_name="Default Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Test Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            # created_by not specified
        )

        timeline = await service.timeline(session=session, deal=deal)
        assert len(timeline) == 1
        assert str(timeline[0].changed_by) == str(agent_id)


# ============================================================================
# STAGE CHANGE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_change_stage_updates_status(async_session_factory):
    """Test that changing stage to CLOSED_WON updates status."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="closer@example.com",
                username="closer_agent",
                full_name="Closer Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Marina View Portfolio",
            asset_type=DealAssetType.PORTFOLIO,
            deal_type=DealType.CAPITAL_RAISE,
            created_by=agent_id,
        )
        event = await service.change_stage(
            session=session,
            deal=deal,
            to_stage=PipelineStage.CLOSED_WON,
            changed_by=agent_id,
            note="Signed SPA",
        )
        assert event.to_stage == PipelineStage.CLOSED_WON
        assert deal.status.name == "CLOSED_WON"
        assert deal.actual_close_date is not None

        timeline, audit_map = await service.timeline_with_audit(
            session=session, deal=deal
        )
        assert len(timeline) == 2
        assert timeline[-1].note == "Signed SPA"
        assert timeline[-1].metadata.get("audit_log_id") is not None

        project_key = audit_project_key(deal)
        result = await session.execute(
            select(AuditLog)
            .where(AuditLog.project_id == project_key)
            .order_by(AuditLog.version)
        )
        logs = result.scalars().all()
        assert len(logs) == 2
        assert logs[-1].context.get("to_stage") == PipelineStage.CLOSED_WON.value

        timeline_schema = DealWithTimelineSchema.from_orm_deal(
            deal, timeline=timeline, audit_logs=audit_map
        )
        assert timeline_schema.timeline[0].duration_seconds is not None
        assert timeline_schema.timeline[0].audit_log is not None


@pytest.mark.asyncio
async def test_change_stage_to_closed_lost(async_session_factory):
    """Test that changing stage to CLOSED_LOST updates status correctly."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="lost_deal@example.com",
                username="lost_agent",
                full_name="Lost Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Lost Opportunity",
            asset_type=DealAssetType.RESIDENTIAL,
            deal_type=DealType.SELL_SIDE,
            created_by=agent_id,
        )

        event = await service.change_stage(
            session=session,
            deal=deal,
            to_stage=PipelineStage.CLOSED_LOST,
            changed_by=agent_id,
            note="Client chose competitor",
        )

        assert event.to_stage == PipelineStage.CLOSED_LOST
        assert deal.status == DealStatus.CLOSED_LOST
        assert deal.actual_close_date is not None


@pytest.mark.asyncio
async def test_reopen_closed_deal_resets_status(async_session_factory):
    """Test that reopening a closed deal resets status to OPEN."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="reopen@example.com",
                username="reopen_agent",
                full_name="Reopen Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Reopened Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            created_by=agent_id,
        )

        # Close the deal
        await service.change_stage(
            session=session,
            deal=deal,
            to_stage=PipelineStage.CLOSED_LOST,
            changed_by=agent_id,
        )
        assert deal.status == DealStatus.CLOSED_LOST

        # Reopen the deal
        await service.change_stage(
            session=session,
            deal=deal,
            to_stage=PipelineStage.NEGOTIATION,
            changed_by=agent_id,
            note="Client reconsidered",
        )

        assert deal.pipeline_stage == PipelineStage.NEGOTIATION
        assert deal.status == DealStatus.OPEN


@pytest.mark.asyncio
async def test_change_stage_with_metadata(async_session_factory):
    """Test that stage change with metadata persists correctly."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="metadata@example.com",
                username="metadata_agent",
                full_name="Metadata Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Metadata Test Deal",
            asset_type=DealAssetType.MIXED_USE,
            deal_type=DealType.BUY_SIDE,
            created_by=agent_id,
        )

        event = await service.change_stage(
            session=session,
            deal=deal,
            to_stage=PipelineStage.DUE_DILIGENCE,
            changed_by=agent_id,
            note="Entering DD phase",
            metadata={"dd_provider": "JLL", "scope": "technical"},
        )

        # Metadata should include both custom metadata and audit_log_id
        assert "dd_provider" in event.metadata
        assert event.metadata["dd_provider"] == "JLL"
        assert "audit_log_id" in event.metadata


# ============================================================================
# DEAL LISTING AND RETRIEVAL TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_list_deals_filters_by_agent(async_session_factory):
    """Test that list_deals filters by agent_ids correctly."""
    service = AgentDealService()
    agent_id_1 = uuid4()
    agent_id_2 = uuid4()

    async with async_session_factory() as session:
        # Create two agents
        session.add(
            User(
                id=str(agent_id_1),
                email="agent1@example.com",
                username="agent1",
                full_name="Agent One",
                hashed_password="secret",
            )
        )
        session.add(
            User(
                id=str(agent_id_2),
                email="agent2@example.com",
                username="agent2",
                full_name="Agent Two",
                hashed_password="secret",
            )
        )
        await session.commit()

        # Create deals for each agent
        await service.create_deal(
            session=session,
            agent_id=agent_id_1,
            title="Agent 1 Deal A",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            created_by=agent_id_1,
        )
        await service.create_deal(
            session=session,
            agent_id=agent_id_1,
            title="Agent 1 Deal B",
            asset_type=DealAssetType.RETAIL,
            deal_type=DealType.SELL_SIDE,
            created_by=agent_id_1,
        )
        await service.create_deal(
            session=session,
            agent_id=agent_id_2,
            title="Agent 2 Deal",
            asset_type=DealAssetType.INDUSTRIAL,
            deal_type=DealType.BUY_SIDE,
            created_by=agent_id_2,
        )

        # Filter by agent 1
        deals = await service.list_deals(
            session=session,
            agent_ids=[agent_id_1],
        )
        assert len(deals) == 2
        assert all(d.agent_id == str(agent_id_1) for d in deals)


@pytest.mark.asyncio
async def test_list_deals_filters_by_stage(async_session_factory):
    """Test that list_deals filters by pipeline stages."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="stage_filter@example.com",
                username="stage_agent",
                full_name="Stage Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        # Create deals at different stages
        deal1 = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Lead Stage Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            pipeline_stage=PipelineStage.LEAD_CAPTURED,
            created_by=agent_id,
        )
        deal2 = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Qualified Deal",
            asset_type=DealAssetType.RETAIL,
            deal_type=DealType.SELL_SIDE,
            pipeline_stage=PipelineStage.QUALIFIED,
            created_by=agent_id,
        )
        deal3 = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Negotiation Deal",
            asset_type=DealAssetType.INDUSTRIAL,
            deal_type=DealType.BUY_SIDE,
            pipeline_stage=PipelineStage.NEGOTIATION,
            created_by=agent_id,
        )

        # Filter by qualified stage only
        deals = await service.list_deals(
            session=session,
            stages=[PipelineStage.QUALIFIED],
        )
        assert len(deals) == 1
        assert deals[0].pipeline_stage == PipelineStage.QUALIFIED


@pytest.mark.asyncio
async def test_list_deals_filters_by_status(async_session_factory):
    """Test that list_deals filters by deal status."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="status_filter@example.com",
                username="status_agent",
                full_name="Status Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        # Create open deal
        deal1 = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Open Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            created_by=agent_id,
        )

        # Create and close a deal
        deal2 = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Closed Deal",
            asset_type=DealAssetType.RETAIL,
            deal_type=DealType.SELL_SIDE,
            created_by=agent_id,
        )
        await service.change_stage(
            session=session,
            deal=deal2,
            to_stage=PipelineStage.CLOSED_WON,
            changed_by=agent_id,
        )

        # Filter by open status
        open_deals = await service.list_deals(
            session=session,
            status=DealStatus.OPEN,
        )
        assert len(open_deals) == 1
        assert open_deals[0].status == DealStatus.OPEN


@pytest.mark.asyncio
async def test_list_deals_with_pagination(async_session_factory):
    """Test that list_deals supports pagination."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="pagination@example.com",
                username="pagination_agent",
                full_name="Pagination Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        # Create 5 deals
        for i in range(5):
            await service.create_deal(
                session=session,
                agent_id=agent_id,
                title=f"Deal {i}",
                asset_type=DealAssetType.OFFICE,
                deal_type=DealType.LEASE,
                created_by=agent_id,
            )

        # Get first page
        page1 = await service.list_deals(session=session, limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = await service.list_deals(session=session, limit=2, offset=2)
        assert len(page2) == 2

        # Verify no overlap
        page1_ids = {d.id for d in page1}
        page2_ids = {d.id for d in page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_get_deal_with_timeline(async_session_factory):
    """Test that get_deal with_timeline=True loads related data."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="timeline@example.com",
                username="timeline_agent",
                full_name="Timeline Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Timeline Test",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            created_by=agent_id,
        )

        # Add stage changes
        await service.change_stage(
            session=session,
            deal=deal,
            to_stage=PipelineStage.QUALIFIED,
            changed_by=agent_id,
        )

        # Fetch with timeline
        fetched = await service.get_deal(
            session=session,
            deal_id=deal.id,
            with_timeline=True,
        )

        assert fetched is not None
        assert fetched.id == deal.id
        assert len(fetched.stage_events) == 2


@pytest.mark.asyncio
async def test_get_deal_returns_none_for_missing(async_session_factory):
    """Test that get_deal returns None for non-existent deal."""
    service = AgentDealService()

    async with async_session_factory() as session:
        result = await service.get_deal(
            session=session,
            deal_id=uuid4(),
        )
        assert result is None


# ============================================================================
# DEAL UPDATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_update_deal_modifies_fields(async_session_factory):
    """Test that update_deal modifies deal fields correctly."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="update@example.com",
                username="update_agent",
                full_name="Update Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Original Title",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            created_by=agent_id,
        )

        updated = await service.update_deal(
            session=session,
            deal=deal,
            title="Updated Title",
            description="New description",
            estimated_value_amount=1_000_000.00,
            confidence=0.8,
        )

        assert updated.title == "Updated Title"
        assert updated.description == "New description"
        assert updated.estimated_value_amount == 1_000_000.00
        assert updated.confidence == 0.8


@pytest.mark.asyncio
async def test_update_deal_preserves_unchanged_fields(async_session_factory):
    """Test that update_deal preserves fields not being updated."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="preserve@example.com",
                username="preserve_agent",
                full_name="Preserve Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Original Title",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            description="Original description",
            lead_source="website",
            created_by=agent_id,
        )

        updated = await service.update_deal(
            session=session,
            deal=deal,
            title="New Title",
            # Not updating description or lead_source
        )

        assert updated.title == "New Title"
        assert updated.description == "Original description"
        assert updated.lead_source == "website"


# ============================================================================
# CONTACT AND DOCUMENT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_add_contact_to_deal(async_session_factory):
    """Test adding a contact to a deal."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="contact_test@example.com",
                username="contact_agent",
                full_name="Contact Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Contact Test Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            created_by=agent_id,
        )

        contact = AgentDealContact(
            deal_id=deal.id,
            name="John Doe",
            email="john@example.com",
            phone="+65 9123 4567",
            role="buyer",
            is_primary=True,
        )

        saved_contact = await service.add_contact(session=session, contact=contact)

        assert saved_contact.id is not None
        assert saved_contact.name == "John Doe"
        assert saved_contact.is_primary is True


@pytest.mark.asyncio
async def test_add_document_to_deal(async_session_factory):
    """Test adding a document reference to a deal."""
    service = AgentDealService()
    agent_id = uuid4()

    async with async_session_factory() as session:
        session.add(
            User(
                id=str(agent_id),
                email="document_test@example.com",
                username="document_agent",
                full_name="Document Agent",
                hashed_password="secret",
            )
        )
        await session.commit()

        deal = await service.create_deal(
            session=session,
            agent_id=agent_id,
            title="Document Test Deal",
            asset_type=DealAssetType.OFFICE,
            deal_type=DealType.LEASE,
            created_by=agent_id,
        )

        document = AgentDealDocument(
            deal_id=deal.id,
            title="Sales Agreement",
            document_type="contract",
            storage_url="s3://bucket/deals/123/agreement.pdf",
            uploaded_by=str(agent_id),
        )

        saved_doc = await service.add_document(session=session, document=document)

        assert saved_doc.id is not None
        assert saved_doc.title == "Sales Agreement"
        assert saved_doc.document_type == "contract"
