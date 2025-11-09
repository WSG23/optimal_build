"""Tests for agent advisory models."""

from datetime import datetime

import pytest

from app.models.agent_advisory import AgentAdvisoryFeedback
from app.models.property import Property, PropertyType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


class TestAgentAdvisoryFeedback:
    """Tests for the AgentAdvisoryFeedback model."""

    async def test_create_agent_advisory_feedback(self, session: AsyncSession):
        """Test creating an AgentAdvisoryFeedback record."""
        # Create a test property first
        property_obj = Property(
            name="Test Property",
            address="123 Test Street",
            property_type=PropertyType.RESIDENTIAL,
            location="POINT(103.8535 1.2830)",
        )
        session.add(property_obj)
        await session.commit()
        await session.refresh(property_obj)

        feedback = AgentAdvisoryFeedback(
            property_id=property_obj.id,
            submitted_by="agent-123",
            channel="web",
            sentiment="positive",
            notes="Great property with good amenities",
            context={"source": "property_details_page", "rating": 5},
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        assert feedback.id is not None
        assert feedback.property_id == property_obj.id
        assert feedback.submitted_by == "agent-123"
        assert feedback.channel == "web"
        assert feedback.sentiment == "positive"
        assert feedback.notes == "Great property with good amenities"
        assert feedback.context == {"source": "property_details_page", "rating": 5}
        assert isinstance(feedback.created_at, datetime)

    async def test_feedback_optional_fields(self, session: AsyncSession):
        """Test that optional fields can be None."""
        property_obj = Property(
            name="Test Property",
            address="123 Test Street",
            property_type=PropertyType.RESIDENTIAL,
            location="POINT(103.8535 1.2830)",
        )
        session.add(property_obj)
        await session.commit()
        await session.refresh(property_obj)

        feedback = AgentAdvisoryFeedback(
            property_id=property_obj.id,
            submitted_by=None,
            channel=None,
            sentiment="neutral",
            notes="No specific feedback",
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        assert feedback.submitted_by is None
        assert feedback.channel is None
        assert feedback.sentiment == "neutral"
        assert feedback.notes == "No specific feedback"

    async def test_feedback_context_default_is_empty_dict(self, session: AsyncSession):
        """Test that context defaults to empty dict."""
        property_obj = Property(
            name="Test Property",
            address="123 Test Street",
            property_type=PropertyType.RESIDENTIAL,
            location="POINT(103.8535 1.2830)",
        )
        session.add(property_obj)
        await session.commit()
        await session.refresh(property_obj)

        feedback = AgentAdvisoryFeedback(
            property_id=property_obj.id,
            sentiment="negative",
            notes="Issue with pricing",
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        assert feedback.context == {}

    async def test_multiple_feedback_per_property(self, session: AsyncSession):
        """Test that a property can have multiple feedback records."""
        property_obj = Property(
            name="Test Property",
            address="123 Test Street",
            property_type=PropertyType.RESIDENTIAL,
            location="POINT(103.8535 1.2830)",
        )
        session.add(property_obj)
        await session.commit()
        await session.refresh(property_obj)

        feedback1 = AgentAdvisoryFeedback(
            property_id=property_obj.id,
            sentiment="positive",
            notes="First feedback",
        )
        feedback2 = AgentAdvisoryFeedback(
            property_id=property_obj.id,
            sentiment="neutral",
            notes="Second feedback",
        )

        session.add(feedback1)
        session.add(feedback2)
        await session.commit()

        # Query all feedback for the property
        result = await session.execute(
            select(AgentAdvisoryFeedback).where(
                AgentAdvisoryFeedback.property_id == property_obj.id
            )
        )
        feedbacks = result.scalars().all()

        assert len(feedbacks) == 2
        assert {f.notes for f in feedbacks} == {"First feedback", "Second feedback"}

    async def test_feedback_created_at_auto_generated(self, session: AsyncSession):
        """Test that created_at is automatically set."""
        property_obj = Property(
            name="Test Property",
            address="123 Test Street",
            property_type=PropertyType.RESIDENTIAL,
            location="POINT(103.8535 1.2830)",
        )
        session.add(property_obj)
        await session.commit()
        await session.refresh(property_obj)

        feedback = AgentAdvisoryFeedback(
            property_id=property_obj.id,
            sentiment="positive",
            notes="Test timestamp",
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        # created_at should be set automatically
        assert feedback.created_at is not None
        assert isinstance(feedback.created_at, datetime)

        # Should be recent (within the last minute)
        time_diff = datetime.now(feedback.created_at.tzinfo) - feedback.created_at
        assert time_diff.total_seconds() < 60

    async def test_feedback_complex_context_jsonb(self, session: AsyncSession):
        """Test storing complex data in the JSONB context field."""
        property_obj = Property(
            name="Test Property",
            address="123 Test Street",
            property_type=PropertyType.RESIDENTIAL,
            location="POINT(103.8535 1.2830)",
        )
        session.add(property_obj)
        await session.commit()
        await session.refresh(property_obj)

        complex_context = {
            "user_agent": "Mozilla/5.0",
            "screen_resolution": {"width": 1920, "height": 1080},
            "referrer": "https://example.com/search",
            "tags": ["premium", "high-demand"],
            "metadata": {
                "session_id": "abc123",
                "duration_seconds": 300,
            },
        }

        feedback = AgentAdvisoryFeedback(
            property_id=property_obj.id,
            sentiment="positive",
            notes="Complex context test",
            context=complex_context,
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)

        # Verify complex JSON structure is preserved
        assert feedback.context == complex_context
        assert feedback.context["screen_resolution"]["width"] == 1920
        assert feedback.context["tags"] == ["premium", "high-demand"]
        assert feedback.context["metadata"]["session_id"] == "abc123"
