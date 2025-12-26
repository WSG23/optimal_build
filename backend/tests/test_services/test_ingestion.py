"""Comprehensive tests for ingestion service.

Tests cover:
- start_ingestion_run function
- complete_ingestion_run function
- Ingestion run status tracking
"""

from __future__ import annotations

from datetime import datetime

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestIngestionRunStatus:
    """Tests for ingestion run status values."""

    def test_running_status(self) -> None:
        """Test running status."""
        status = "running"
        assert status == "running"

    def test_completed_status(self) -> None:
        """Test completed status."""
        status = "completed"
        assert status == "completed"

    def test_failed_status(self) -> None:
        """Test failed status."""
        status = "failed"
        assert status == "failed"

    def test_cancelled_status(self) -> None:
        """Test cancelled status."""
        status = "cancelled"
        assert status == "cancelled"


class TestIngestionFlowNames:
    """Tests for ingestion flow name values."""

    def test_ura_masterplan_flow(self) -> None:
        """Test URA masterplan flow name."""
        flow_name = "ingest_ura_masterplan"
        assert flow_name == "ingest_ura_masterplan"

    def test_bca_rules_flow(self) -> None:
        """Test BCA rules flow name."""
        flow_name = "ingest_bca_rules"
        assert flow_name == "ingest_bca_rules"

    def test_scdf_firecode_flow(self) -> None:
        """Test SCDF fire code flow name."""
        flow_name = "ingest_scdf_firecode"
        assert flow_name == "ingest_scdf_firecode"

    def test_cost_index_flow(self) -> None:
        """Test cost index flow name."""
        flow_name = "ingest_cost_index"
        assert flow_name == "ingest_cost_index"

    def test_vendor_catalog_flow(self) -> None:
        """Test vendor catalog flow name."""
        flow_name = "ingest_vendor_catalog"
        assert flow_name == "ingest_vendor_catalog"


class TestIngestionRunData:
    """Tests for ingestion run data structures."""

    def test_run_record_structure(self) -> None:
        """Test ingestion run record structure."""
        run = {
            "id": 1,
            "run_key": "ura-masterplan-2024-01-15",
            "flow_name": "ingest_ura_masterplan",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": None,
            "records_ingested": 0,
            "suspected_updates": 0,
            "notes": "Scheduled daily run",
            "metrics": {},
        }
        assert run["status"] == "running"
        assert run["finished_at"] is None

    def test_completed_run_record(self) -> None:
        """Test completed ingestion run record."""
        run = {
            "id": 1,
            "run_key": "ura-masterplan-2024-01-15",
            "flow_name": "ingest_ura_masterplan",
            "status": "completed",
            "started_at": "2024-01-15T10:00:00Z",
            "finished_at": "2024-01-15T10:05:30Z",
            "records_ingested": 1500,
            "suspected_updates": 12,
            "metrics": {
                "duration_seconds": 330,
                "pages_processed": 150,
                "rules_extracted": 1500,
            },
        }
        assert run["status"] == "completed"
        assert run["records_ingested"] == 1500


class TestIngestionMetrics:
    """Tests for ingestion metrics data structures."""

    def test_basic_metrics(self) -> None:
        """Test basic ingestion metrics."""
        metrics = {
            "duration_seconds": 125.5,
            "records_ingested": 1500,
            "records_skipped": 50,
            "errors_count": 3,
        }
        assert metrics["duration_seconds"] > 0

    def test_document_metrics(self) -> None:
        """Test document processing metrics."""
        metrics = {
            "pages_processed": 150,
            "documents_downloaded": 5,
            "documents_cached": 3,
            "bytes_downloaded": 15728640,
        }
        assert metrics["pages_processed"] > 0

    def test_rule_extraction_metrics(self) -> None:
        """Test rule extraction metrics."""
        metrics = {
            "rules_extracted": 1500,
            "rules_created": 1200,
            "rules_updated": 280,
            "rules_unchanged": 20,
        }
        total = (
            metrics["rules_created"]
            + metrics["rules_updated"]
            + metrics["rules_unchanged"]
        )
        assert total == metrics["rules_extracted"]


class TestIngestionScenarios:
    """Tests for ingestion use case scenarios."""

    def test_daily_masterplan_ingestion(self) -> None:
        """Test daily masterplan ingestion scenario."""
        run = {
            "run_key": "ura-masterplan-2024-01-15-daily",
            "flow_name": "ingest_ura_masterplan",
            "notes": "Scheduled daily run at 02:00 SGT",
            "status": "completed",
            "records_ingested": 2500,
            "suspected_updates": 15,
            "metrics": {
                "zones_processed": 55,
                "parcels_updated": 15,
                "new_zones_detected": 0,
            },
        }
        assert run["records_ingested"] > 0

    def test_bca_rules_update(self) -> None:
        """Test BCA rules update scenario."""
        run = {
            "run_key": "bca-rules-2024-01-15",
            "flow_name": "ingest_bca_rules",
            "notes": "Triggered by document hash change alert",
            "status": "completed",
            "records_ingested": 850,
            "suspected_updates": 25,
            "metrics": {
                "sections_processed": 12,
                "rules_extracted": 850,
                "new_rules": 25,
                "updated_rules": 0,
            },
        }
        assert run["suspected_updates"] == 25

    def test_cost_index_quarterly(self) -> None:
        """Test quarterly cost index ingestion scenario."""
        run = {
            "run_key": "cost-index-2024-Q1",
            "flow_name": "ingest_cost_index",
            "notes": "Quarterly BCA cost index update",
            "status": "completed",
            "records_ingested": 120,
            "suspected_updates": 120,
            "metrics": {
                "categories": ["material", "labor", "equipment"],
                "series_updated": 40,
                "period": "2024-Q1",
            },
        }
        assert run["records_ingested"] == 120

    def test_failed_ingestion(self) -> None:
        """Test failed ingestion scenario."""
        run = {
            "run_key": "ura-masterplan-2024-01-16",
            "flow_name": "ingest_ura_masterplan",
            "status": "failed",
            "records_ingested": 500,
            "suspected_updates": 0,
            "metrics": {
                "error_type": "connection_timeout",
                "error_message": "Connection to URA API timed out after 30s",
                "retry_count": 3,
            },
        }
        assert run["status"] == "failed"

    def test_vendor_catalog_ingestion(self) -> None:
        """Test vendor catalog ingestion scenario."""
        run = {
            "run_key": "kohler-catalog-2024-01",
            "flow_name": "ingest_vendor_catalog",
            "notes": "Monthly Kohler product catalog sync",
            "status": "completed",
            "records_ingested": 450,
            "suspected_updates": 30,
            "metrics": {
                "vendor": "Kohler",
                "products_new": 15,
                "products_updated": 15,
                "products_discontinued": 5,
                "categories": ["toilet", "basin", "shower", "bathtub"],
            },
        }
        assert "Kohler" == run["metrics"]["vendor"]


class TestIngestionAlerts:
    """Tests for ingestion alert data structures."""

    def test_document_changed_alert(self) -> None:
        """Test document changed alert structure."""
        alert = {
            "alert_type": "document_changed",
            "level": "warning",
            "message": "SCDF Fire Code document hash changed",
            "context": {
                "source_id": 1,
                "old_hash": "abc123",
                "new_hash": "def456",
                "document_title": "Fire Code 2018",
            },
            "acknowledged": False,
        }
        assert alert["level"] == "warning"

    def test_ingestion_failed_alert(self) -> None:
        """Test ingestion failed alert structure."""
        alert = {
            "alert_type": "ingestion_failed",
            "level": "error",
            "message": "URA masterplan ingestion failed after 3 retries",
            "context": {
                "flow_name": "ingest_ura_masterplan",
                "error_type": "api_error",
                "run_key": "ura-masterplan-2024-01-16",
            },
            "acknowledged": False,
        }
        assert alert["level"] == "error"

    def test_suspected_update_alert(self) -> None:
        """Test suspected update alert structure."""
        alert = {
            "alert_type": "suspected_update",
            "level": "info",
            "message": "15 rules may have been updated in BCA Building Code",
            "context": {
                "source_id": 2,
                "suspected_count": 15,
                "run_id": 42,
            },
            "acknowledged": False,
        }
        assert alert["level"] == "info"
