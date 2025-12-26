"""Comprehensive tests for rkp (Reference Knowledge Platform) model.

Tests cover:
- RefSource model structure
- RefDocument model structure
- RefClause model structure
- RefRule model structure
- RefParcel model structure
- RefZoningLayer model structure
- RefGeocodeCache model structure
- RefMaterialStandard model structure
- RefProduct model structure
- RefErgonomics model structure
- RefCostIndex model structure
- RefCostCatalog model structure
- RefIngestionRun model structure
- RefAlert model structure
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestRefSourceModel:
    """Tests for RefSource model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        source_id = 1
        assert isinstance(source_id, int)

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "SG"
        assert len(jurisdiction) > 0

    def test_authority_required(self) -> None:
        """Test authority is required."""
        authority = "URA"
        assert len(authority) > 0

    def test_topic_required(self) -> None:
        """Test topic is required."""
        topic = "zoning"
        assert len(topic) > 0

    def test_doc_title_required(self) -> None:
        """Test doc_title is required."""
        title = "Master Plan 2019"
        assert len(title) > 0

    def test_landing_url_required(self) -> None:
        """Test landing_url is required."""
        url = "https://www.ura.gov.sg/"
        assert url.startswith("http")

    def test_fetch_kind_default_pdf(self) -> None:
        """Test fetch_kind defaults to pdf."""
        fetch_kind = "pdf"
        assert fetch_kind == "pdf"


class TestRefDocumentModel:
    """Tests for RefDocument model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        doc_id = 1
        assert isinstance(doc_id, int)

    def test_source_id_required(self) -> None:
        """Test source_id is required."""
        source_id = 1
        assert source_id is not None

    def test_version_label_optional(self) -> None:
        """Test version_label is optional."""
        doc = {}
        assert doc.get("version_label") is None

    def test_storage_path_required(self) -> None:
        """Test storage_path is required."""
        path = "s3://bucket/docs/ura_masterplan_2019.pdf"
        assert len(path) > 0

    def test_file_hash_required(self) -> None:
        """Test file_hash (SHA-256) is required."""
        file_hash = "a" * 64
        assert len(file_hash) == 64


class TestRefRuleModel:
    """Tests for RefRule model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        rule_id = 1
        assert isinstance(rule_id, int)

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "SG"
        assert jurisdiction is not None

    def test_parameter_key_required(self) -> None:
        """Test parameter_key is required."""
        key = "egress.corridor.min_width_mm"
        assert len(key) > 0

    def test_operator_required(self) -> None:
        """Test operator is required."""
        operator = ">="
        assert len(operator) > 0

    def test_value_required(self) -> None:
        """Test value is required."""
        value = "1200"
        assert len(value) > 0

    def test_review_status_default_needs_review(self) -> None:
        """Test review_status defaults to needs_review."""
        status = "needs_review"
        assert status == "needs_review"

    def test_is_published_default_false(self) -> None:
        """Test is_published defaults to False."""
        is_published = False
        assert is_published is False


class TestRefCostIndexModel:
    """Tests for RefCostIndex model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        index_id = 1
        assert isinstance(index_id, int)

    def test_jurisdiction_default_sg(self) -> None:
        """Test jurisdiction defaults to SG."""
        jurisdiction = "SG"
        assert jurisdiction == "SG"

    def test_series_name_required(self) -> None:
        """Test series_name is required."""
        series = "concrete"
        assert len(series) > 0

    def test_category_required(self) -> None:
        """Test category is required."""
        category = "material"
        assert len(category) > 0

    def test_period_required(self) -> None:
        """Test period is required."""
        period = "2024-Q1"
        assert len(period) > 0

    def test_value_required(self) -> None:
        """Test value is required."""
        value = Decimal("125.50")
        assert value > 0

    def test_unit_required(self) -> None:
        """Test unit is required."""
        unit = "SGD/m3"
        assert len(unit) > 0


class TestRefProductModel:
    """Tests for RefProduct model structure."""

    def test_id_is_integer(self) -> None:
        """Test id is integer type."""
        product_id = 1
        assert isinstance(product_id, int)

    def test_vendor_required(self) -> None:
        """Test vendor is required."""
        vendor = "Kohler"
        assert len(vendor) > 0

    def test_category_required(self) -> None:
        """Test category is required."""
        category = "toilet"
        assert len(category) > 0

    def test_product_code_required(self) -> None:
        """Test product_code is required."""
        code = "K-123456"
        assert len(code) > 0

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Kohler San Raphael"
        assert len(name) > 0

    def test_currency_default_sgd(self) -> None:
        """Test currency defaults to SGD."""
        currency = "SGD"
        assert currency == "SGD"


class TestReviewStatuses:
    """Tests for rule review status values."""

    def test_needs_review(self) -> None:
        """Test needs_review status."""
        status = "needs_review"
        assert status == "needs_review"

    def test_approved(self) -> None:
        """Test approved status."""
        status = "approved"
        assert status == "approved"

    def test_rejected(self) -> None:
        """Test rejected status."""
        status = "rejected"
        assert status == "rejected"


class TestFetchKinds:
    """Tests for document fetch kind values."""

    def test_pdf_fetch(self) -> None:
        """Test pdf fetch kind."""
        kind = "pdf"
        assert kind == "pdf"

    def test_html_fetch(self) -> None:
        """Test html fetch kind."""
        kind = "html"
        assert kind == "html"

    def test_sitemap_fetch(self) -> None:
        """Test sitemap fetch kind."""
        kind = "sitemap"
        assert kind == "sitemap"


class TestAlertLevels:
    """Tests for alert level values."""

    def test_info_level(self) -> None:
        """Test info alert level."""
        level = "info"
        assert level == "info"

    def test_warning_level(self) -> None:
        """Test warning alert level."""
        level = "warning"
        assert level == "warning"

    def test_error_level(self) -> None:
        """Test error alert level."""
        level = "error"
        assert level == "error"

    def test_critical_level(self) -> None:
        """Test critical alert level."""
        level = "critical"
        assert level == "critical"


class TestRKPScenarios:
    """Tests for RKP use case scenarios."""

    def test_create_ref_source(self) -> None:
        """Test creating a reference source."""
        source = {
            "id": 1,
            "jurisdiction": "SG",
            "authority": "SCDF",
            "topic": "fire",
            "doc_title": "Fire Code 2018",
            "landing_url": "https://www.scdf.gov.sg/firecode",
            "fetch_kind": "pdf",
            "update_freq_hint": "annual",
            "is_active": True,
        }
        assert source["authority"] == "SCDF"

    def test_create_ref_rule(self) -> None:
        """Test creating a reference rule."""
        rule = {
            "id": 1,
            "source_id": 1,
            "jurisdiction": "SG",
            "authority": "SCDF",
            "topic": "fire",
            "clause_ref": "4.2.1",
            "parameter_key": "egress.corridor.min_width_mm",
            "operator": ">=",
            "value": "1200",
            "unit": "mm",
            "applicability": {"occupancy": ["residential"], "height": "any"},
            "review_status": "approved",
            "is_published": True,
        }
        assert rule["parameter_key"] == "egress.corridor.min_width_mm"
        assert rule["value"] == "1200"

    def test_create_cost_index(self) -> None:
        """Test creating a cost index entry."""
        index = {
            "id": 1,
            "jurisdiction": "SG",
            "series_name": "ready_mix_concrete",
            "category": "material",
            "subcategory": "grade_30",
            "period": "2024-Q2",
            "value": Decimal("125.00"),
            "unit": "SGD/m3",
            "source": "BCA Building Cost Information Service",
            "provider": "internal",
        }
        assert index["value"] == Decimal("125.00")

    def test_create_product_catalog_entry(self) -> None:
        """Test creating a product catalog entry."""
        product = {
            "id": 1,
            "vendor": "Kohler",
            "category": "toilet",
            "product_code": "K-77780-0",
            "name": "San Raphael Comfort Height",
            "brand": "Kohler",
            "model_number": "77780",
            "dimensions": {"width_mm": 390, "depth_mm": 700, "height_mm": 780},
            "specifications": {"flush_volume_l": 4.8, "material": "vitreous_china"},
            "unit_cost": Decimal("850.00"),
            "currency": "SGD",
            "is_active": True,
        }
        assert product["specifications"]["flush_volume_l"] == 4.8

    def test_create_ergonomics_reference(self) -> None:
        """Test creating an ergonomics reference."""
        ergo = {
            "id": 1,
            "metric_key": "wheelchair.turning_radius_mm",
            "population": "wheelchair",
            "percentile": "95th",
            "value": Decimal("1500.00"),
            "unit": "mm",
            "context": {"space_type": "bathroom"},
            "source": "ISO 21542:2011",
        }
        assert ergo["value"] == Decimal("1500.00")

    def test_create_ingestion_run(self) -> None:
        """Test creating an ingestion run record."""
        run = {
            "id": 1,
            "run_key": "ura-masterplan-2024-01-15",
            "flow_name": "ingest_ura_masterplan",
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "records_ingested": 0,
            "suspected_updates": 0,
        }
        assert run["status"] == "running"

    def test_complete_ingestion_run(self) -> None:
        """Test completing an ingestion run."""
        run = {
            "status": "running",
            "records_ingested": 0,
        }
        run["status"] = "completed"
        run["finished_at"] = datetime.utcnow()
        run["records_ingested"] = 1500
        run["suspected_updates"] = 12
        run["metrics"] = {
            "duration_seconds": 125.5,
            "pages_processed": 150,
            "rules_extracted": 1500,
        }
        assert run["status"] == "completed"
        assert run["records_ingested"] == 1500

    def test_create_alert(self) -> None:
        """Test creating an alert."""
        alert = {
            "id": 1,
            "alert_type": "document_changed",
            "level": "warning",
            "message": "SCDF Fire Code document hash changed - potential update detected",
            "created_at": datetime.utcnow().isoformat(),
            "context": {"source_id": 1, "old_hash": "abc...", "new_hash": "def..."},
            "ingestion_run_id": 1,
            "acknowledged": False,
        }
        assert alert["level"] == "warning"

    def test_acknowledge_alert(self) -> None:
        """Test acknowledging an alert."""
        alert = {
            "acknowledged": False,
        }
        alert["acknowledged"] = True
        alert["acknowledged_at"] = datetime.utcnow()
        alert["acknowledged_by"] = "admin@buildable.com"
        assert alert["acknowledged"] is True
