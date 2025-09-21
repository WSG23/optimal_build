"""Pydantic schemas for rule endpoints."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RuleResponse(BaseModel):
    """Normalized rule representation."""

    id: Optional[int]
    jurisdiction: str
    authority: str
    topic: str
    clause_ref: Optional[str]
    parameter_key: str
    operator: str
    value: str
    unit: Optional[str]
    value_normalized: Optional[float] = Field(None, description="SI-normalized numeric value")
    applicability: Dict[str, object]
    exceptions: List[object]
    review_status: str
    provenance: Dict[str, object]


class RuleSearchResponse(BaseModel):
    count: int
    rules: List[RuleResponse]


class RulesByClauseResponse(BaseModel):
    clause_ref: str
    rules: Dict[str, List[RuleResponse]]


class RuleSnapshotResponse(BaseModel):
    generated_at: str
    total_rules: int
    by_authority: Dict[str, int]
    rules: List[RuleResponse]
