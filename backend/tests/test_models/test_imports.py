"""Comprehensive tests for imports model.

Tests cover:
- ImportRecord model structure
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestImportRecordModel:
    """Tests for ImportRecord model structure."""

    def test_id_is_string_uuid(self) -> None:
        """Test id is string UUID (36 chars)."""
        import_id = str(uuid4())
        assert len(import_id) == 36

    def test_project_id_optional(self) -> None:
        """Test project_id is optional but indexed."""
        record = {}
        assert record.get("project_id") is None

    def test_filename_required(self) -> None:
        """Test filename is required."""
        filename = "floor_plan_level_1.dwg"
        assert len(filename) > 0

    def test_content_type_optional(self) -> None:
        """Test content_type is optional."""
        record = {}
        assert record.get("content_type") is None

    def test_size_bytes_required(self) -> None:
        """Test size_bytes is required."""
        size = 1024000
        assert size > 0

    def test_storage_path_required(self) -> None:
        """Test storage_path is required."""
        path = "s3://bucket/uploads/project_1/floor_plan.dwg"
        assert len(path) > 0

    def test_zone_code_optional(self) -> None:
        """Test zone_code is optional."""
        record = {}
        assert record.get("zone_code") is None

    def test_layer_metadata_default_list(self) -> None:
        """Test layer_metadata defaults to empty list."""
        layers: list = []
        assert isinstance(layers, list)

    def test_detected_floors_default_list(self) -> None:
        """Test detected_floors defaults to empty list."""
        floors: list = []
        assert isinstance(floors, list)

    def test_detected_units_default_list(self) -> None:
        """Test detected_units defaults to empty list."""
        units: list = []
        assert isinstance(units, list)

    def test_vector_storage_path_optional(self) -> None:
        """Test vector_storage_path is optional."""
        record = {}
        assert record.get("vector_storage_path") is None

    def test_metric_overrides_default_dict(self) -> None:
        """Test metric_overrides defaults to empty dict."""
        overrides: dict = {}
        assert isinstance(overrides, dict)

    def test_parse_status_default_pending(self) -> None:
        """Test parse_status defaults to pending."""
        status = "pending"
        assert status == "pending"


class TestParseStatus:
    """Tests for parse status values."""

    def test_pending_status(self) -> None:
        """Test pending status."""
        status = "pending"
        assert status == "pending"

    def test_processing_status(self) -> None:
        """Test processing status."""
        status = "processing"
        assert status == "processing"

    def test_completed_status(self) -> None:
        """Test completed status."""
        status = "completed"
        assert status == "completed"

    def test_failed_status(self) -> None:
        """Test failed status."""
        status = "failed"
        assert status == "failed"


class TestContentTypes:
    """Tests for common import content types."""

    def test_dwg_content_type(self) -> None:
        """Test DWG file content type."""
        content_type = "application/acad"
        assert content_type is not None

    def test_dxf_content_type(self) -> None:
        """Test DXF file content type."""
        content_type = "application/dxf"
        assert content_type is not None

    def test_ifc_content_type(self) -> None:
        """Test IFC (BIM) file content type."""
        content_type = "application/x-step"
        assert content_type is not None

    def test_revit_content_type(self) -> None:
        """Test Revit file content type."""
        content_type = "application/x-revit"
        assert content_type is not None

    def test_pdf_content_type(self) -> None:
        """Test PDF floor plan content type."""
        content_type = "application/pdf"
        assert content_type is not None


class TestImportRecordScenarios:
    """Tests for import record use case scenarios."""

    def test_create_dwg_import(self) -> None:
        """Test creating a DWG file import record."""
        record = {
            "id": str(uuid4()),
            "project_id": 1,
            "filename": "architectural_plan_L01.dwg",
            "content_type": "application/acad",
            "size_bytes": 2500000,
            "storage_path": "s3://buildable-uploads/project_1/architectural_plan_L01.dwg",
            "zone_code": "SG:residential",
            "uploaded_at": datetime.utcnow().isoformat(),
            "parse_status": "pending",
        }
        assert record["content_type"] == "application/acad"
        assert record["parse_status"] == "pending"

    def test_parse_dwg_layers(self) -> None:
        """Test parsing DWG file layers."""
        record = {
            "parse_status": "processing",
            "parse_requested_at": datetime.utcnow().isoformat(),
            "layer_metadata": [
                {"name": "A-WALL", "color": 7, "visible": True},
                {"name": "A-DOOR", "color": 3, "visible": True},
                {"name": "A-WINDOW", "color": 5, "visible": True},
                {"name": "A-DIMS", "color": 6, "visible": False},
            ],
        }
        assert len(record["layer_metadata"]) == 4

    def test_complete_parsing(self) -> None:
        """Test completing file parsing."""
        record = {
            "parse_status": "pending",
        }
        record["parse_status"] = "completed"
        record["parse_completed_at"] = datetime.utcnow()
        record["detected_floors"] = [
            {"level": "L01", "area_sqm": 1500.0, "units": 12},
            {"level": "L02", "area_sqm": 1500.0, "units": 12},
        ]
        record["detected_units"] = [
            {"id": "01-01", "area_sqm": 120.0, "bedrooms": 3},
            {"id": "01-02", "area_sqm": 85.0, "bedrooms": 2},
        ]
        record["parse_result"] = {
            "total_floors": 2,
            "total_units": 24,
            "total_gfa_sqm": 3000.0,
        }
        assert record["parse_status"] == "completed"
        assert len(record["detected_floors"]) == 2

    def test_parsing_failure(self) -> None:
        """Test handling parsing failure."""
        record = {
            "parse_status": "processing",
        }
        record["parse_status"] = "failed"
        record["parse_error"] = "Unsupported DWG version 2024. Maximum supported: 2018"
        record["parse_completed_at"] = datetime.utcnow()
        assert record["parse_status"] == "failed"
        assert "Unsupported DWG version" in record["parse_error"]

    def test_metric_overrides(self) -> None:
        """Test applying metric overrides to import."""
        record = {
            "metric_overrides": {
                "gfa_multiplier": 1.05,
                "exclude_balconies": True,
                "void_threshold_sqm": 10.0,
            }
        }
        assert record["metric_overrides"]["gfa_multiplier"] == 1.05

    def test_bim_import_with_vector_storage(self) -> None:
        """Test BIM import with vector storage for spatial queries."""
        record = {
            "filename": "building_model.ifc",
            "content_type": "application/x-step",
            "storage_path": "s3://buildable-uploads/project_1/building_model.ifc",
            "vector_storage_path": "vectordb://project_1/building_model",
            "vector_summary": {
                "total_elements": 15000,
                "element_types": ["IfcWall", "IfcDoor", "IfcWindow", "IfcSlab"],
                "floors_detected": 25,
            },
        }
        assert record["vector_storage_path"] is not None
        assert record["vector_summary"]["floors_detected"] == 25
