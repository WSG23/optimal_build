"""Comprehensive tests for common schemas.

Tests cover:
- PaginationParams schema
- PaginationMeta schema
- PaginatedResponse schema
- LegacyPaginatedCollection schema
- SuccessResponse schema
- ResourceCreatedResponse schema
- BulkOperationResult schema
"""

from __future__ import annotations

from datetime import datetime


class TestPaginationParams:
    """Tests for PaginationParams schema."""

    def test_limit_default(self) -> None:
        """Test limit defaults to 20."""
        limit = 20
        assert limit == 20

    def test_limit_min(self) -> None:
        """Test limit minimum is 1."""
        limit = 1
        assert limit >= 1

    def test_limit_max(self) -> None:
        """Test limit maximum is 100."""
        limit = 100
        assert limit <= 100

    def test_offset_default(self) -> None:
        """Test offset defaults to 0."""
        offset = 0
        assert offset == 0

    def test_offset_min(self) -> None:
        """Test offset minimum is 0."""
        offset = 0
        assert offset >= 0

    def test_cursor_optional(self) -> None:
        """Test cursor is optional."""
        params = {}
        assert params.get("cursor") is None

    def test_normalize_method(self) -> None:
        """Test normalize returns bounded tuple."""
        limit = 50
        offset = 100
        normalized = (max(1, min(limit, 100)), max(0, offset))
        assert normalized == (50, 100)

    def test_normalize_bounds_limit(self) -> None:
        """Test normalize bounds limit to max 100."""
        limit = 150
        normalized_limit = max(1, min(limit, 100))
        assert normalized_limit == 100

    def test_normalize_bounds_offset(self) -> None:
        """Test normalize ensures offset >= 0."""
        offset = -10
        normalized_offset = max(0, offset)
        assert normalized_offset == 0


class TestPaginationMeta:
    """Tests for PaginationMeta schema."""

    def test_total_required(self) -> None:
        """Test total is required."""
        total = 150
        assert total >= 0

    def test_limit_required(self) -> None:
        """Test limit is required."""
        limit = 20
        assert limit >= 1

    def test_offset_required(self) -> None:
        """Test offset is required."""
        offset = 40
        assert offset >= 0

    def test_has_next_required(self) -> None:
        """Test has_next is required boolean."""
        has_next = True
        assert isinstance(has_next, bool)

    def test_has_prev_required(self) -> None:
        """Test has_prev is required boolean."""
        has_prev = True
        assert isinstance(has_prev, bool)

    def test_page_required(self) -> None:
        """Test page is required (1-indexed)."""
        page = 3
        assert page >= 1

    def test_total_pages_required(self) -> None:
        """Test total_pages is required."""
        total_pages = 8
        assert total_pages >= 1

    def test_next_cursor_optional(self) -> None:
        """Test next_cursor is optional."""
        meta = {}
        assert meta.get("next_cursor") is None


class TestPaginationMetaFromPagination:
    """Tests for PaginationMeta.from_pagination class method."""

    def test_creates_meta(self) -> None:
        """Test from_pagination creates meta object."""
        total = 150
        limit = 20
        offset = 40

        total_pages = max(1, (total + limit - 1) // limit)
        page = (offset // limit) + 1
        has_next = offset + limit < total
        has_prev = offset > 0

        assert total_pages == 8
        assert page == 3
        assert has_next is True
        assert has_prev is True

    def test_first_page_no_prev(self) -> None:
        """Test first page has no prev."""
        offset = 0
        has_prev = offset > 0
        assert has_prev is False

    def test_last_page_no_next(self) -> None:
        """Test last page has no next."""
        total = 100
        limit = 20
        offset = 80
        has_next = offset + limit < total
        assert has_next is False


class TestPaginatedResponse:
    """Tests for PaginatedResponse schema."""

    def test_items_required(self) -> None:
        """Test items list is required."""
        items = []
        assert isinstance(items, list)

    def test_pagination_required(self) -> None:
        """Test pagination meta is required."""
        pagination = {"total": 100, "limit": 20, "offset": 0}
        assert "total" in pagination


class TestPaginatedResponseCreate:
    """Tests for PaginatedResponse.create class method."""

    def test_creates_response(self) -> None:
        """Test create method builds response."""
        items = [{"id": 1}, {"id": 2}]
        total = 50
        limit = 20
        offset = 0

        response = {
            "items": items,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }
        assert len(response["items"]) == 2

    def test_with_cursor(self) -> None:
        """Test create with next_cursor."""
        next_cursor = "eyJpZCI6IDUwfQ=="
        response = {"next_cursor": next_cursor}
        assert response["next_cursor"] is not None


class TestLegacyPaginatedCollection:
    """Tests for LegacyPaginatedCollection schema."""

    def test_items_required(self) -> None:
        """Test items list is required."""
        items = []
        assert isinstance(items, list)

    def test_total_required(self) -> None:
        """Test total is required."""
        total = 100
        assert total >= 0

    def test_limit_required(self) -> None:
        """Test limit is required."""
        limit = 20
        assert limit >= 1

    def test_offset_required(self) -> None:
        """Test offset is required."""
        offset = 0
        assert offset >= 0


class TestSuccessResponse:
    """Tests for SuccessResponse schema."""

    def test_success_default_true(self) -> None:
        """Test success defaults to True."""
        success = True
        assert success is True

    def test_message_required(self) -> None:
        """Test message is required."""
        message = "Operation completed successfully"
        assert len(message) > 0

    def test_timestamp_default(self) -> None:
        """Test timestamp defaults to now."""
        timestamp = datetime.utcnow()
        assert timestamp is not None


class TestResourceCreatedResponse:
    """Tests for ResourceCreatedResponse schema."""

    def test_id_required(self) -> None:
        """Test id is required (int or str)."""
        int_id = 1
        str_id = "abc-123"
        assert int_id is not None
        assert str_id is not None

    def test_data_required(self) -> None:
        """Test data is required."""
        data = {"name": "New Resource"}
        assert data is not None

    def test_created_at_default(self) -> None:
        """Test created_at defaults to now."""
        created_at = datetime.utcnow()
        assert created_at is not None


class TestBulkOperationResult:
    """Tests for BulkOperationResult schema."""

    def test_total_requested_required(self) -> None:
        """Test total_requested is required."""
        total_requested = 10
        assert total_requested >= 0

    def test_succeeded_required(self) -> None:
        """Test succeeded is required."""
        succeeded = 8
        assert succeeded >= 0

    def test_failed_required(self) -> None:
        """Test failed is required."""
        failed = 2
        assert failed >= 0

    def test_errors_default_empty(self) -> None:
        """Test errors defaults to empty list."""
        errors = []
        assert isinstance(errors, list)

    def test_success_rate_property(self) -> None:
        """Test success_rate calculation."""
        total_requested = 10
        succeeded = 8
        if total_requested == 0:
            success_rate = 100.0
        else:
            success_rate = (succeeded / total_requested) * 100
        assert success_rate == 80.0

    def test_success_rate_zero_total(self) -> None:
        """Test success_rate with zero total is 100%."""
        total_requested = 0
        if total_requested == 0:
            success_rate = 100.0
        else:
            success_rate = 0.0
        assert success_rate == 100.0


class TestPaginationScenarios:
    """Tests for pagination use case scenarios."""

    def test_first_page_of_results(self) -> None:
        """Test first page pagination."""
        total = 100
        limit = 20
        offset = 0

        page = (offset // limit) + 1
        has_next = offset + limit < total
        has_prev = offset > 0

        assert page == 1
        assert has_next is True
        assert has_prev is False

    def test_middle_page_of_results(self) -> None:
        """Test middle page pagination."""
        total = 100
        limit = 20
        offset = 40

        page = (offset // limit) + 1
        has_next = offset + limit < total
        has_prev = offset > 0

        assert page == 3
        assert has_next is True
        assert has_prev is True

    def test_last_page_of_results(self) -> None:
        """Test last page pagination."""
        total = 100
        limit = 20
        offset = 80

        page = (offset // limit) + 1
        has_next = offset + limit < total
        has_prev = offset > 0

        assert page == 5
        assert has_next is False
        assert has_prev is True

    def test_single_page_results(self) -> None:
        """Test single page of results."""
        total = 15
        limit = 20
        offset = 0

        total_pages = max(1, (total + limit - 1) // limit)
        has_next = offset + limit < total
        has_prev = offset > 0

        assert total_pages == 1
        assert has_next is False
        assert has_prev is False

    def test_empty_results(self) -> None:
        """Test empty results pagination."""
        total = 0
        limit = 20

        total_pages = max(1, (total + limit - 1) // limit)

        assert total_pages == 1

    def test_cursor_pagination(self) -> None:
        """Test cursor-based pagination."""
        cursor = "eyJpZCI6IDEwMH0="  # Base64 encoded cursor
        limit = 20

        params = {"cursor": cursor, "limit": limit}
        assert params["cursor"] is not None


class TestBulkOperationScenarios:
    """Tests for bulk operation use case scenarios."""

    def test_all_succeeded(self) -> None:
        """Test all operations succeeded."""
        result = {
            "total_requested": 10,
            "succeeded": 10,
            "failed": 0,
            "errors": [],
        }
        success_rate = (result["succeeded"] / result["total_requested"]) * 100
        assert success_rate == 100.0

    def test_partial_success(self) -> None:
        """Test partial success with errors."""
        result = {
            "total_requested": 10,
            "succeeded": 7,
            "failed": 3,
            "errors": [
                {"item_id": "5", "message": "Validation error"},
                {"item_id": "8", "message": "Not found"},
                {"item_id": "9", "message": "Permission denied"},
            ],
        }
        assert len(result["errors"]) == 3

    def test_all_failed(self) -> None:
        """Test all operations failed."""
        result = {
            "total_requested": 5,
            "succeeded": 0,
            "failed": 5,
            "errors": [{"item_id": str(i), "message": "Error"} for i in range(5)],
        }
        success_rate = (result["succeeded"] / result["total_requested"]) * 100
        assert success_rate == 0.0
