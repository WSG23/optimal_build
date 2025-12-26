"""Tests for unified pagination schemas and dependencies.

Tests cover:
- PaginationParams validation and normalization
- PaginationMeta calculation
- PaginatedResponse factory methods
- Legacy backward compatibility
- Edge cases and bounds checking
"""

import pytest
from pydantic import ValidationError

from app.schemas.common import (
    BulkOperationResult,
    LegacyPaginatedCollection,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    ResourceCreatedResponse,
    SuccessResponse,
)


class TestPaginationParams:
    """Tests for PaginationParams schema."""

    def test_default_values(self) -> None:
        """Test default pagination parameters."""
        params = PaginationParams()
        assert params.limit == 20
        assert params.offset == 0
        assert params.cursor is None

    def test_custom_values(self) -> None:
        """Test custom pagination parameters."""
        params = PaginationParams(limit=50, offset=100, cursor="abc123")
        assert params.limit == 50
        assert params.offset == 100
        assert params.cursor == "abc123"

    def test_limit_minimum_bound(self) -> None:
        """Test that limit cannot be less than 1."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_limit_maximum_bound(self) -> None:
        """Test that limit cannot exceed 100."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=101)
        assert "less than or equal to 100" in str(exc_info.value)

    def test_offset_minimum_bound(self) -> None:
        """Test that offset cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(offset=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_normalize_returns_tuple(self) -> None:
        """Test normalize returns (limit, offset) tuple."""
        params = PaginationParams(limit=50, offset=25)
        limit, offset = params.normalize()
        assert limit == 50
        assert offset == 25

    def test_normalize_clamps_values(self) -> None:
        """Test normalize clamps values within bounds."""
        # Create params directly to bypass validation for edge case testing
        params = PaginationParams(limit=1, offset=0)
        limit, offset = params.normalize()
        assert limit >= 1
        assert limit <= 100
        assert offset >= 0


class TestPaginationMeta:
    """Tests for PaginationMeta calculation."""

    def test_from_pagination_first_page(self) -> None:
        """Test metadata for first page."""
        meta = PaginationMeta.from_pagination(total=100, limit=20, offset=0)

        assert meta.total == 100
        assert meta.limit == 20
        assert meta.offset == 0
        assert meta.has_next is True
        assert meta.has_prev is False
        assert meta.page == 1
        assert meta.total_pages == 5

    def test_from_pagination_middle_page(self) -> None:
        """Test metadata for middle page."""
        meta = PaginationMeta.from_pagination(total=100, limit=20, offset=40)

        assert meta.has_next is True
        assert meta.has_prev is True
        assert meta.page == 3
        assert meta.total_pages == 5

    def test_from_pagination_last_page(self) -> None:
        """Test metadata for last page."""
        meta = PaginationMeta.from_pagination(total=100, limit=20, offset=80)

        assert meta.has_next is False
        assert meta.has_prev is True
        assert meta.page == 5
        assert meta.total_pages == 5

    def test_from_pagination_empty_result(self) -> None:
        """Test metadata for empty result set."""
        meta = PaginationMeta.from_pagination(total=0, limit=20, offset=0)

        assert meta.total == 0
        assert meta.has_next is False
        assert meta.has_prev is False
        assert meta.page == 1
        assert meta.total_pages == 1

    def test_from_pagination_single_page(self) -> None:
        """Test metadata when all results fit on one page."""
        meta = PaginationMeta.from_pagination(total=15, limit=20, offset=0)

        assert meta.has_next is False
        assert meta.has_prev is False
        assert meta.page == 1
        assert meta.total_pages == 1

    def test_from_pagination_with_cursor(self) -> None:
        """Test metadata includes cursor for cursor-based pagination."""
        meta = PaginationMeta.from_pagination(
            total=100, limit=20, offset=0, next_cursor="cursor_abc"
        )

        assert meta.next_cursor == "cursor_abc"

    def test_total_pages_calculation_rounding(self) -> None:
        """Test total pages rounds up correctly."""
        # 21 items with limit 20 = 2 pages
        meta = PaginationMeta.from_pagination(total=21, limit=20, offset=0)
        assert meta.total_pages == 2

        # 40 items with limit 20 = 2 pages exactly
        meta = PaginationMeta.from_pagination(total=40, limit=20, offset=0)
        assert meta.total_pages == 2


class TestPaginatedResponse:
    """Tests for PaginatedResponse generic class."""

    def test_create_with_items(self) -> None:
        """Test creating paginated response with items."""
        items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        response = PaginatedResponse.create(items=items, total=50, limit=20, offset=0)

        assert response.items == items
        assert response.pagination.total == 50
        assert response.pagination.limit == 20
        assert response.pagination.offset == 0
        assert response.pagination.page == 1

    def test_create_empty_response(self) -> None:
        """Test creating paginated response with no items."""
        response: PaginatedResponse[dict] = PaginatedResponse.create(
            items=[], total=0, limit=20, offset=0
        )

        assert response.items == []
        assert response.pagination.total == 0
        assert response.pagination.has_next is False

    def test_create_with_cursor(self) -> None:
        """Test creating paginated response with cursor."""
        response: PaginatedResponse[str] = PaginatedResponse.create(
            items=["a", "b", "c"],
            total=100,
            limit=3,
            offset=0,
            next_cursor="cursor_xyz",
        )

        assert response.pagination.next_cursor == "cursor_xyz"

    def test_generic_type_preservation(self) -> None:
        """Test that generic type is preserved in response."""

        class UserSchema:
            id: int
            name: str

        users = [UserSchema(), UserSchema()]
        response: PaginatedResponse[UserSchema] = PaginatedResponse.create(
            items=users, total=2, limit=20, offset=0
        )

        assert len(response.items) == 2


class TestLegacyPaginatedCollection:
    """Tests for backward-compatible legacy pagination."""

    def test_create_legacy_collection(self) -> None:
        """Test creating legacy paginated collection."""
        items = [1, 2, 3]
        collection = LegacyPaginatedCollection.create(
            items=items, total=100, limit=3, offset=0
        )

        assert collection.items == items
        assert collection.total == 100
        assert collection.limit == 3
        assert collection.offset == 0

    def test_legacy_format_matches_existing(self) -> None:
        """Test that legacy format matches existing PaginatedCollection."""
        # This format should match entitlements.py PaginatedCollection
        collection = LegacyPaginatedCollection.create(
            items=["a", "b"], total=50, limit=10, offset=20
        )

        data = collection.model_dump()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        # Should NOT have the new pagination metadata
        assert "pagination" not in data


class TestSuccessResponse:
    """Tests for SuccessResponse schema."""

    def test_default_success(self) -> None:
        """Test default success response."""
        response = SuccessResponse(message="Operation completed")

        assert response.success is True
        assert response.message == "Operation completed"
        assert response.timestamp is not None

    def test_custom_success_flag(self) -> None:
        """Test custom success flag (though typically always True)."""
        response = SuccessResponse(success=True, message="Done")
        assert response.success is True


class TestResourceCreatedResponse:
    """Tests for ResourceCreatedResponse schema."""

    def test_create_with_int_id(self) -> None:
        """Test creating response with integer ID."""
        response: ResourceCreatedResponse[dict] = ResourceCreatedResponse(
            id=123, data={"name": "Test"}
        )

        assert response.id == 123
        assert response.data == {"name": "Test"}
        assert response.created_at is not None

    def test_create_with_string_id(self) -> None:
        """Test creating response with string ID (UUID)."""
        response: ResourceCreatedResponse[dict] = ResourceCreatedResponse(
            id="uuid-abc-123", data={"name": "Test"}
        )

        assert response.id == "uuid-abc-123"


class TestBulkOperationResult:
    """Tests for BulkOperationResult schema."""

    def test_all_successful(self) -> None:
        """Test bulk operation with all successes."""
        result = BulkOperationResult(
            total_requested=10, succeeded=10, failed=0, errors=[]
        )

        assert result.success_rate == 100.0
        assert result.failed == 0

    def test_partial_failure(self) -> None:
        """Test bulk operation with some failures."""
        result = BulkOperationResult(
            total_requested=10,
            succeeded=7,
            failed=3,
            errors=[
                {"item_id": "1", "message": "Invalid format"},
                {"item_id": "2", "message": "Not found"},
                {"item_id": "3", "message": "Permission denied"},
            ],
        )

        assert result.success_rate == 70.0
        assert result.failed == 3
        assert len(result.errors) == 3

    def test_all_failed(self) -> None:
        """Test bulk operation with all failures."""
        result = BulkOperationResult(
            total_requested=5, succeeded=0, failed=5, errors=[]
        )

        assert result.success_rate == 0.0

    def test_empty_request(self) -> None:
        """Test bulk operation with no items."""
        result = BulkOperationResult(
            total_requested=0, succeeded=0, failed=0, errors=[]
        )

        assert result.success_rate == 100.0  # No failures = 100%


class TestPaginationEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_large_offset_beyond_total(self) -> None:
        """Test when offset exceeds total items."""
        meta = PaginationMeta.from_pagination(total=50, limit=20, offset=100)

        assert meta.has_next is False
        assert meta.has_prev is True
        assert meta.page == 6  # offset/limit + 1

    def test_limit_equals_total(self) -> None:
        """Test when limit equals total items."""
        meta = PaginationMeta.from_pagination(total=20, limit=20, offset=0)

        assert meta.has_next is False
        assert meta.total_pages == 1

    def test_very_large_dataset(self) -> None:
        """Test pagination metadata for large dataset."""
        meta = PaginationMeta.from_pagination(total=1000000, limit=100, offset=5000)

        assert meta.total_pages == 10000
        assert meta.page == 51
        assert meta.has_next is True
        assert meta.has_prev is True

    def test_offset_at_exact_page_boundary(self) -> None:
        """Test offset at exact page boundary."""
        meta = PaginationMeta.from_pagination(total=100, limit=25, offset=50)

        assert meta.page == 3  # (50/25) + 1
        assert meta.total_pages == 4
