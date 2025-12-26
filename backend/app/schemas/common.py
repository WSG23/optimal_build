"""Common schemas for standardized API responses.

This module provides:
- Unified pagination with cursor and offset support
- Standardized response envelopes for consistency
- Reusable base schemas for all endpoints
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Generic type for paginated items
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination.

    Supports both offset-based and cursor-based pagination patterns.
    Default limit is 20, max is 100 to prevent excessive data transfer.
    """

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of items to return (1-100)",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip for offset-based pagination",
    )
    cursor: str | None = Field(
        default=None,
        description="Opaque cursor for cursor-based pagination (overrides offset)",
    )

    def normalize(self) -> tuple[int, int]:
        """Return normalized (limit, offset) tuple with bounds checking."""
        limit_value = max(1, min(self.limit, 100))
        offset_value = max(0, self.offset)
        return limit_value, offset_value


class PaginationMeta(BaseModel):
    """Metadata about paginated results.

    Provides information for building pagination UI and links.
    """

    total: int = Field(..., description="Total number of items matching the query")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Current offset in the result set")
    has_next: bool = Field(..., description="Whether more items exist after this page")
    has_prev: bool = Field(..., description="Whether items exist before this page")
    page: int = Field(..., description="Current page number (1-indexed)")
    total_pages: int = Field(..., description="Total number of pages")
    next_cursor: str | None = Field(
        default=None, description="Cursor for next page (if using cursor pagination)"
    )

    @classmethod
    def from_pagination(
        cls,
        total: int,
        limit: int,
        offset: int,
        next_cursor: str | None = None,
    ) -> "PaginationMeta":
        """Create pagination metadata from query parameters."""
        total_pages = max(1, (total + limit - 1) // limit)
        page = (offset // limit) + 1

        return cls(
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total,
            has_prev=offset > 0,
            page=page,
            total_pages=total_pages,
            next_cursor=next_cursor,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope.

    All list endpoints should return this format for consistency.
    Provides rich pagination metadata for frontend integration.

    Example response:
    {
        "items": [...],
        "pagination": {
            "total": 150,
            "limit": 20,
            "offset": 40,
            "has_next": true,
            "has_prev": true,
            "page": 3,
            "total_pages": 8
        }
    }
    """

    items: list[T] = Field(..., description="List of items for the current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        limit: int,
        offset: int,
        next_cursor: str | None = None,
    ) -> "PaginatedResponse[T]":
        """Factory method to create a paginated response."""
        return cls(
            items=items,
            pagination=PaginationMeta.from_pagination(
                total=total,
                limit=limit,
                offset=offset,
                next_cursor=next_cursor,
            ),
        )


class LegacyPaginatedCollection(BaseModel, Generic[T]):
    """Legacy pagination format for backward compatibility.

    Matches the existing PaginatedCollection from entitlements.py.
    New endpoints should use PaginatedResponse instead.
    """

    items: list[T]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls, items: list[T], total: int, limit: int, offset: int
    ) -> "LegacyPaginatedCollection[T]":
        """Factory method to create a legacy paginated collection."""
        return cls(items=items, total=total, limit=limit, offset=offset)


class SuccessResponse(BaseModel):
    """Generic success response for operations without data return.

    Use for DELETE operations, status updates, etc.
    """

    success: bool = Field(default=True, description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable success message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the operation completed",
    )


class ResourceCreatedResponse(BaseModel, Generic[T]):
    """Response envelope for resource creation.

    Returns the created resource with its ID and creation timestamp.
    """

    id: int | str = Field(..., description="ID of the created resource")
    data: T = Field(..., description="The created resource")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the resource was created",
    )

    model_config = ConfigDict(from_attributes=True)


class BulkOperationResult(BaseModel):
    """Result of a bulk operation.

    Provides detailed success/failure counts and error details.
    """

    total_requested: int = Field(..., description="Number of items in the request")
    succeeded: int = Field(..., description="Number of successfully processed items")
    failed: int = Field(..., description="Number of failed items")
    errors: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of errors with item identifiers and messages",
    )

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_requested == 0:
            return 100.0
        return (self.succeeded / self.total_requested) * 100


__all__ = [
    "PaginationParams",
    "PaginationMeta",
    "PaginatedResponse",
    "LegacyPaginatedCollection",
    "SuccessResponse",
    "ResourceCreatedResponse",
    "BulkOperationResult",
]
