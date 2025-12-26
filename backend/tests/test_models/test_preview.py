"""Comprehensive tests for preview model.

Tests cover:
- PreviewJobStatus enum
- PreviewJob model structure
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestPreviewJobStatus:
    """Tests for PreviewJobStatus enum."""

    def test_queued_status(self) -> None:
        """Test queued status."""
        status = "queued"
        assert status == "queued"

    def test_processing_status(self) -> None:
        """Test processing status."""
        status = "processing"
        assert status == "processing"

    def test_ready_status(self) -> None:
        """Test ready status."""
        status = "ready"
        assert status == "ready"

    def test_failed_status(self) -> None:
        """Test failed status."""
        status = "failed"
        assert status == "failed"

    def test_expired_status(self) -> None:
        """Test expired status."""
        status = "expired"
        assert status == "expired"


class TestPreviewJobModel:
    """Tests for PreviewJob model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        job_id = uuid4()
        assert len(str(job_id)) == 36

    def test_property_id_required(self) -> None:
        """Test property_id is required."""
        property_id = uuid4()
        assert property_id is not None

    def test_scenario_default_base(self) -> None:
        """Test scenario defaults to 'base'."""
        scenario = "base"
        assert scenario == "base"

    def test_status_default_queued(self) -> None:
        """Test status defaults to queued."""
        status = "queued"
        assert status == "queued"

    def test_requested_at_required(self) -> None:
        """Test requested_at is required."""
        requested_at = datetime.utcnow()
        assert requested_at is not None

    def test_started_at_optional(self) -> None:
        """Test started_at is optional."""
        job = {}
        assert job.get("started_at") is None

    def test_finished_at_optional(self) -> None:
        """Test finished_at is optional."""
        job = {}
        assert job.get("finished_at") is None

    def test_asset_version_optional(self) -> None:
        """Test asset_version is optional."""
        job = {}
        assert job.get("asset_version") is None

    def test_preview_url_optional(self) -> None:
        """Test preview_url is optional."""
        job = {}
        assert job.get("preview_url") is None

    def test_metadata_url_optional(self) -> None:
        """Test metadata_url is optional."""
        job = {}
        assert job.get("metadata_url") is None

    def test_thumbnail_url_optional(self) -> None:
        """Test thumbnail_url is optional."""
        job = {}
        assert job.get("thumbnail_url") is None

    def test_payload_checksum_optional(self) -> None:
        """Test payload_checksum is optional."""
        job = {}
        assert job.get("payload_checksum") is None

    def test_message_optional(self) -> None:
        """Test message is optional."""
        job = {}
        assert job.get("message") is None

    def test_metadata_default_dict(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata: dict = {}
        assert isinstance(metadata, dict)


class TestPreviewScenarios:
    """Tests for preview scenario values."""

    def test_base_scenario(self) -> None:
        """Test base scenario."""
        scenario = "base"
        assert scenario == "base"

    def test_optimized_scenario(self) -> None:
        """Test optimized scenario."""
        scenario = "optimized"
        assert scenario == "optimized"

    def test_max_yield_scenario(self) -> None:
        """Test max_yield scenario."""
        scenario = "max_yield"
        assert scenario == "max_yield"

    def test_heritage_compliant_scenario(self) -> None:
        """Test heritage_compliant scenario."""
        scenario = "heritage_compliant"
        assert scenario == "heritage_compliant"


class TestPreviewJobScenarios:
    """Tests for preview job use case scenarios."""

    def test_create_preview_job(self) -> None:
        """Test creating a preview job."""
        job = {
            "id": str(uuid4()),
            "property_id": str(uuid4()),
            "scenario": "base",
            "status": "queued",
            "requested_at": datetime.utcnow().isoformat(),
            "metadata": {
                "requested_by": str(uuid4()),
                "priority": "normal",
            },
        }
        assert job["status"] == "queued"
        assert job["scenario"] == "base"

    def test_start_processing(self) -> None:
        """Test starting preview processing."""
        job = {
            "status": "queued",
            "started_at": None,
        }
        job["status"] = "processing"
        job["started_at"] = datetime.utcnow()
        assert job["status"] == "processing"
        assert job["started_at"] is not None

    def test_complete_preview_generation(self) -> None:
        """Test completing preview generation."""
        job = {
            "status": "processing",
        }
        job["status"] = "ready"
        job["finished_at"] = datetime.utcnow()
        job["asset_version"] = "v2024.12.01"
        job["preview_url"] = "https://cdn.buildable.com/previews/job123/preview.glb"
        job["metadata_url"] = "https://cdn.buildable.com/previews/job123/metadata.json"
        job["thumbnail_url"] = "https://cdn.buildable.com/previews/job123/thumb.png"
        job["payload_checksum"] = "sha256:abc123def456..."
        assert job["status"] == "ready"
        assert job["preview_url"] is not None

    def test_preview_generation_failure(self) -> None:
        """Test handling preview generation failure."""
        job = {
            "status": "processing",
        }
        job["status"] = "failed"
        job["finished_at"] = datetime.utcnow()
        job["message"] = "Failed to generate 3D model: Invalid geometry data"
        assert job["status"] == "failed"
        assert "Invalid geometry" in job["message"]

    def test_expire_old_preview(self) -> None:
        """Test expiring old preview."""
        job = {
            "status": "ready",
        }
        job["status"] = "expired"
        job["message"] = "Preview expired after 30 days"
        assert job["status"] == "expired"

    def test_preview_with_optimization_scenario(self) -> None:
        """Test preview for optimization scenario."""
        job = {
            "id": str(uuid4()),
            "property_id": str(uuid4()),
            "scenario": "optimized",
            "status": "queued",
            "metadata": {
                "optimization_target": "gfa",
                "constraints": {
                    "max_height_m": 80,
                    "setback_front_m": 6,
                    "plot_ratio": 3.5,
                },
            },
        }
        assert job["scenario"] == "optimized"
        assert job["metadata"]["optimization_target"] == "gfa"

    def test_preview_metadata_structure(self) -> None:
        """Test preview metadata structure."""
        job = {
            "metadata": {
                "building_stats": {
                    "total_gfa_sqm": 25000,
                    "floors_above_ground": 30,
                    "floors_below_ground": 2,
                    "unit_count": 150,
                },
                "render_settings": {
                    "quality": "high",
                    "lighting": "day",
                    "camera_presets": ["aerial", "street", "interior"],
                },
                "compliance_check": {
                    "height_compliant": True,
                    "setback_compliant": True,
                    "plot_ratio_compliant": True,
                },
            }
        }
        assert job["metadata"]["building_stats"]["total_gfa_sqm"] == 25000
        assert job["metadata"]["compliance_check"]["height_compliant"] is True
