"""Tests for the agent performance Prefect flows."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from app.flows.performance import (
    _parse_agent_ids,
    _parse_date,
    agent_performance_snapshots_flow,
    seed_performance_benchmarks_flow,
)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestParseAgentIds:
    """Tests for the _parse_agent_ids helper function."""

    def test_parse_agent_ids_with_valid_uuids(self) -> None:
        """Test parsing valid UUID strings."""
        id1 = str(uuid4())
        id2 = str(uuid4())
        result = _parse_agent_ids([id1, id2])

        assert result is not None
        assert len(result) == 2
        assert all(isinstance(uid, UUID) for uid in result)
        assert str(result[0]) == id1
        assert str(result[1]) == id2

    def test_parse_agent_ids_with_none(self) -> None:
        """Test that None input returns None."""
        result = _parse_agent_ids(None)
        assert result is None

    def test_parse_agent_ids_with_empty_list(self) -> None:
        """Test that empty list returns None."""
        result = _parse_agent_ids([])
        assert result is None

    def test_parse_agent_ids_skips_invalid_uuids(self) -> None:
        """Test that invalid UUIDs are skipped."""
        valid_id = str(uuid4())
        result = _parse_agent_ids([valid_id, "not-a-uuid", "12345"])

        assert result is not None
        assert len(result) == 1
        assert str(result[0]) == valid_id

    def test_parse_agent_ids_returns_none_if_all_invalid(self) -> None:
        """Test that None is returned if all IDs are invalid."""
        result = _parse_agent_ids(["invalid1", "invalid2"])
        assert result is None

    def test_parse_agent_ids_handles_mixed_types(self) -> None:
        """Test parsing with mixed valid/invalid types."""
        valid_id = str(uuid4())
        result = _parse_agent_ids([valid_id, None, "", 12345])  # type: ignore[list-item]

        assert result is not None
        assert len(result) == 1


class TestParseDate:
    """Tests for the _parse_date helper function."""

    def test_parse_date_with_valid_iso_format(self) -> None:
        """Test parsing a valid ISO date string."""
        result = _parse_date("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_parse_date_with_none(self) -> None:
        """Test that None input returns None."""
        result = _parse_date(None)
        assert result is None

    def test_parse_date_with_empty_string(self) -> None:
        """Test that empty string returns None."""
        result = _parse_date("")
        assert result is None

    def test_parse_date_with_whitespace(self) -> None:
        """Test that whitespace-only string returns None."""
        result = _parse_date("   ")
        assert result is None

    def test_parse_date_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from valid dates."""
        result = _parse_date("  2025-01-15  ")
        assert result == date(2025, 1, 15)

    def test_parse_date_with_invalid_format_raises(self) -> None:
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            _parse_date("01-15-2025")  # Wrong format

    def test_parse_date_with_invalid_date_raises(self) -> None:
        """Test that invalid date raises ValueError."""
        with pytest.raises(ValueError):
            _parse_date("2025-13-01")  # Invalid month


# ============================================================================
# FLOW TESTS (with mocking)
# ============================================================================


class TestAgentPerformanceSnapshotsFlow:
    """Tests for the agent_performance_snapshots_flow Prefect flow."""

    @pytest.mark.asyncio
    async def test_flow_returns_snapshot_count(
        self, mocker, async_session_factory
    ) -> None:
        """Test that the flow returns the count of generated snapshots."""
        mock_service = mocker.MagicMock()
        mock_service.generate_daily_snapshots = mocker.AsyncMock(
            return_value=[mocker.MagicMock(), mocker.MagicMock()]
        )

        mocker.patch(
            "app.flows.performance.AgentPerformanceService",
            return_value=mock_service,
        )
        mocker.patch(
            "app.flows.performance.AsyncSessionLocal",
            async_session_factory,
        )

        result = await agent_performance_snapshots_flow()

        assert result == {"snapshots": 2}

    @pytest.mark.asyncio
    async def test_flow_passes_parsed_agent_ids(
        self, mocker, async_session_factory
    ) -> None:
        """Test that the flow parses and passes agent IDs correctly."""
        mock_service = mocker.MagicMock()
        mock_service.generate_daily_snapshots = mocker.AsyncMock(return_value=[])

        mocker.patch(
            "app.flows.performance.AgentPerformanceService",
            return_value=mock_service,
        )
        mocker.patch(
            "app.flows.performance.AsyncSessionLocal",
            async_session_factory,
        )

        agent_id = str(uuid4())
        await agent_performance_snapshots_flow(agent_ids=[agent_id])

        call_kwargs = mock_service.generate_daily_snapshots.call_args.kwargs
        assert call_kwargs["agent_ids"] is not None
        assert len(call_kwargs["agent_ids"]) == 1
        assert str(call_kwargs["agent_ids"][0]) == agent_id

    @pytest.mark.asyncio
    async def test_flow_passes_parsed_date(
        self, mocker, async_session_factory
    ) -> None:
        """Test that the flow parses and passes the as_of date correctly."""
        mock_service = mocker.MagicMock()
        mock_service.generate_daily_snapshots = mocker.AsyncMock(return_value=[])

        mocker.patch(
            "app.flows.performance.AgentPerformanceService",
            return_value=mock_service,
        )
        mocker.patch(
            "app.flows.performance.AsyncSessionLocal",
            async_session_factory,
        )

        await agent_performance_snapshots_flow(as_of="2025-01-15")

        call_kwargs = mock_service.generate_daily_snapshots.call_args.kwargs
        assert call_kwargs["as_of"] == date(2025, 1, 15)

    @pytest.mark.asyncio
    async def test_flow_handles_no_agent_ids(
        self, mocker, async_session_factory
    ) -> None:
        """Test that the flow handles None agent_ids."""
        mock_service = mocker.MagicMock()
        mock_service.generate_daily_snapshots = mocker.AsyncMock(return_value=[])

        mocker.patch(
            "app.flows.performance.AgentPerformanceService",
            return_value=mock_service,
        )
        mocker.patch(
            "app.flows.performance.AsyncSessionLocal",
            async_session_factory,
        )

        await agent_performance_snapshots_flow(agent_ids=None, as_of=None)

        call_kwargs = mock_service.generate_daily_snapshots.call_args.kwargs
        assert call_kwargs["agent_ids"] is None
        assert call_kwargs["as_of"] is None


class TestSeedPerformanceBenchmarksFlow:
    """Tests for the seed_performance_benchmarks_flow Prefect flow."""

    @pytest.mark.asyncio
    async def test_flow_returns_benchmark_count(
        self, mocker, async_session_factory
    ) -> None:
        """Test that the flow returns the count of seeded benchmarks."""
        mock_service = mocker.MagicMock()
        mock_service.seed_default_benchmarks = mocker.AsyncMock(return_value=5)

        mocker.patch(
            "app.flows.performance.AgentPerformanceService",
            return_value=mock_service,
        )
        mocker.patch(
            "app.flows.performance.AsyncSessionLocal",
            async_session_factory,
        )

        result = await seed_performance_benchmarks_flow()

        assert result == {"benchmarks": 5}

    @pytest.mark.asyncio
    async def test_flow_calls_seed_default_benchmarks(
        self, mocker, async_session_factory
    ) -> None:
        """Test that the flow calls seed_default_benchmarks on the service."""
        mock_service = mocker.MagicMock()
        mock_service.seed_default_benchmarks = mocker.AsyncMock(return_value=0)

        mocker.patch(
            "app.flows.performance.AgentPerformanceService",
            return_value=mock_service,
        )
        mocker.patch(
            "app.flows.performance.AsyncSessionLocal",
            async_session_factory,
        )

        await seed_performance_benchmarks_flow()

        mock_service.seed_default_benchmarks.assert_called_once()
