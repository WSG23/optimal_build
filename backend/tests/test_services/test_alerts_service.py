"""Tests for alerts service with mocked database.

Tests focus on create_alert, list_alerts, and acknowledge_alert functions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefAlert


class TestCreateAlert:
    """Test create_alert function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_alert_adds_record_to_session(self, mock_session):
        """Test create_alert adds alert record to session."""
        from app.services.alerts import create_alert

        with patch("app.services.alerts.metrics") as mock_metrics:
            mock_counter = MagicMock()
            mock_metrics.ALERT_COUNTER.labels.return_value = mock_counter

            await create_alert(
                mock_session,
                alert_type="validation_error",
                level="warning",
                message="Test alert message",
            )

            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()

            # Verify alert record attributes
            added_record = mock_session.add.call_args[0][0]
            assert added_record.alert_type == "validation_error"
            assert added_record.level == "warning"
            assert added_record.message == "Test alert message"

    @pytest.mark.asyncio
    async def test_create_alert_with_context(self, mock_session):
        """Test create_alert with context dict."""
        from app.services.alerts import create_alert

        with patch("app.services.alerts.metrics") as mock_metrics:
            mock_counter = MagicMock()
            mock_metrics.ALERT_COUNTER.labels.return_value = mock_counter

            context = {"document_id": "123", "field": "value"}

            await create_alert(
                mock_session,
                alert_type="parse_error",
                level="error",
                message="Parse failed",
                context=context,
            )

            added_record = mock_session.add.call_args[0][0]
            assert added_record.context == context

    @pytest.mark.asyncio
    async def test_create_alert_with_ingestion_run(self, mock_session):
        """Test create_alert with associated ingestion run."""
        from app.services.alerts import create_alert

        mock_ingestion_run = MagicMock()
        mock_ingestion_run.id = 42

        with patch("app.services.alerts.metrics") as mock_metrics:
            mock_counter = MagicMock()
            mock_metrics.ALERT_COUNTER.labels.return_value = mock_counter

            await create_alert(
                mock_session,
                alert_type="ingestion_warning",
                level="warning",
                message="Skipped duplicate",
                ingestion_run=mock_ingestion_run,
            )

            added_record = mock_session.add.call_args[0][0]
            assert added_record.ingestion_run == mock_ingestion_run
            assert added_record.ingestion_run_id == 42

    @pytest.mark.asyncio
    async def test_create_alert_increments_metric(self, mock_session):
        """Test create_alert increments the alert counter metric."""
        from app.services.alerts import create_alert

        with patch("app.services.alerts.metrics") as mock_metrics:
            mock_counter = MagicMock()
            mock_metrics.ALERT_COUNTER.labels.return_value = mock_counter

            await create_alert(
                mock_session,
                alert_type="system_error",
                level="critical",
                message="System failure",
            )

            mock_metrics.ALERT_COUNTER.labels.assert_called_with(level="critical")
            mock_counter.inc.assert_called_once()


class TestListAlerts:
    """Test list_alerts function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_list_alerts_returns_all_alerts(self, mock_session):
        """Test list_alerts returns all alerts when no filter provided."""
        from app.services.alerts import list_alerts

        mock_alerts = [
            MagicMock(spec=RefAlert, alert_type="error"),
            MagicMock(spec=RefAlert, alert_type="warning"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_alerts
        mock_session.execute.return_value = mock_result

        result = await list_alerts(mock_session)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_alerts_filters_by_type(self, mock_session):
        """Test list_alerts filters by alert_type when provided."""
        from app.services.alerts import list_alerts

        mock_alerts = [MagicMock(spec=RefAlert, alert_type="validation_error")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_alerts
        mock_session.execute.return_value = mock_result

        result = await list_alerts(mock_session, alert_type="validation_error")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_alerts_returns_empty_list(self, mock_session):
        """Test list_alerts returns empty list when no alerts found."""
        from app.services.alerts import list_alerts

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await list_alerts(mock_session)

        assert result == []


class TestAcknowledgeAlert:
    """Test acknowledge_alert function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_acknowledge_alert_updates_record(self, mock_session):
        """Test acknowledge_alert updates alert record."""
        from app.services.alerts import acknowledge_alert

        mock_alert = MagicMock(spec=RefAlert)
        mock_alert.id = 1
        mock_alert.acknowledged = False
        mock_alert.acknowledged_at = None
        mock_alert.acknowledged_by = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alert
        mock_session.execute.return_value = mock_result

        result = await acknowledge_alert(
            mock_session, alert_id=1, acknowledged_by="admin@example.com"
        )

        assert result is not None
        assert mock_alert.acknowledged is True
        assert mock_alert.acknowledged_at is not None
        assert mock_alert.acknowledged_by == "admin@example.com"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_acknowledge_alert_returns_none_when_not_found(self, mock_session):
        """Test acknowledge_alert returns None when alert not found."""
        from app.services.alerts import acknowledge_alert

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await acknowledge_alert(
            mock_session, alert_id=999, acknowledged_by="admin@example.com"
        )

        assert result is None
        mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_acknowledge_alert_sets_timestamp(self, mock_session):
        """Test acknowledge_alert sets acknowledged_at timestamp."""
        from app.services.alerts import acknowledge_alert

        mock_alert = MagicMock(spec=RefAlert)
        mock_alert.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alert
        mock_session.execute.return_value = mock_result

        await acknowledge_alert(
            mock_session, alert_id=1, acknowledged_by="user@example.com"
        )

        # Verify timestamp was set (not None)
        assert mock_alert.acknowledged_at is not None
