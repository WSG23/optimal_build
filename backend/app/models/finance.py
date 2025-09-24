"""Financial modelling tables for pro forma scenarios."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel
from app.models.types import FlexibleJSONB


JSONType = FlexibleJSONB


class FinProject(BaseModel):
    """Finance workspace seeded for a project."""

    __tablename__ = "fin_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )
    discount_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    total_development_cost: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    total_gross_profit: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    scenarios: Mapped[List["FinScenario"]] = relationship(
        "FinScenario", back_populates="fin_project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_fin_projects_project_name", "project_id", "name"),
    )


class FinScenario(BaseModel):
    """Scenario-specific underwriting assumptions."""

    __tablename__ = "fin_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fin_project_id: Mapped[int] = mapped_column(
        ForeignKey("fin_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    fin_project: Mapped[FinProject] = relationship(
        "FinProject", back_populates="scenarios"
    )
    cost_items: Mapped[List["FinCostItem"]] = relationship(
        "FinCostItem", back_populates="scenario", cascade="all, delete-orphan"
    )
    schedules: Mapped[List["FinSchedule"]] = relationship(
        "FinSchedule", back_populates="scenario", cascade="all, delete-orphan"
    )
    capital_stack: Mapped[List["FinCapitalStack"]] = relationship(
        "FinCapitalStack", back_populates="scenario", cascade="all, delete-orphan"
    )
    results: Mapped[List["FinResult"]] = relationship(
        "FinResult", back_populates="scenario", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_fin_scenarios_project_name", "project_id", "name"),
    )


class FinCostItem(BaseModel):
    """Line item level detail for cost modelling."""

    __tablename__ = "fin_cost_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("fin_scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    cost_group: Mapped[str | None] = mapped_column(String(50))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict, nullable=False)

    scenario: Mapped[FinScenario] = relationship("FinScenario", back_populates="cost_items")

    __table_args__ = (
        Index("idx_fin_cost_items_project_name", "project_id", "name"),
    )


class FinSchedule(BaseModel):
    """Monthly cash flow view for a scenario."""

    __tablename__ = "fin_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("fin_scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month_index: Mapped[int] = mapped_column(Integer, nullable=False)
    hard_cost: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    soft_cost: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    cash_flow: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    cumulative_cash_flow: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict, nullable=False)

    scenario: Mapped[FinScenario] = relationship("FinScenario", back_populates="schedules")

    __table_args__ = (
        Index("idx_fin_schedules_project_month", "project_id", "month_index"),
    )


class FinCapitalStack(BaseModel):
    """Capital stack composition for financing mix."""

    __tablename__ = "fin_capital_stacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("fin_scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(50))
    tranche_order: Mapped[int | None] = mapped_column(Integer)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    equity_share: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict, nullable=False)

    scenario: Mapped[FinScenario] = relationship(
        "FinScenario", back_populates="capital_stack"
    )

    __table_args__ = (
        Index("idx_fin_capital_stacks_project_name", "project_id", "name"),
    )


class FinResult(BaseModel):
    """Key results emitted from financing calculations."""

    __tablename__ = "fin_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("fin_scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(16, 4))
    unit: Mapped[str | None] = mapped_column(String(20))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONType, default=dict, nullable=False)

    scenario: Mapped[FinScenario] = relationship(
        "FinScenario", back_populates="results", uselist=False
    )

    __table_args__ = (
        Index("idx_fin_results_project_name", "project_id", "name"),
    )


__all__ = [
    "FinProject",
    "FinScenario",
    "FinCostItem",
    "FinSchedule",
    "FinCapitalStack",
    "FinResult",
]
