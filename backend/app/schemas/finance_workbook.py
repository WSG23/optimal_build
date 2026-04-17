"""Schemas for finance workbook import/export flows."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FinanceWorkbookSheetSummary(BaseModel):
    """Summary for a detected workbook sheet."""

    name: str
    row_count: int = Field(default=0, ge=0)
    column_count: int = Field(default=0, ge=0)
    recognised_as: str | None = None


class FinanceWorkbookValidationIssue(BaseModel):
    """Validation issue discovered while previewing a workbook import."""

    field: str
    message: str


class FinanceWorkbookPreviewResponse(BaseModel):
    """Preview payload returned before committing a workbook import."""

    filename: str
    workbook_format: str = "xlsx"
    detected_sheets: list[FinanceWorkbookSheetSummary] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    is_valid: bool = False
    validation_errors: list[FinanceWorkbookValidationIssue] = Field(
        default_factory=list
    )
    request_payload: dict[str, Any] = Field(default_factory=dict)
    scenario_name: str | None = None
    project_name: str | None = None
    asset_count: int = Field(default=0, ge=0)
