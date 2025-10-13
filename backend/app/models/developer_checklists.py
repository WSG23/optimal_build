"""Developer due diligence checklist models."""

from __future__ import annotations

import enum
from typing import Dict
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import UUID, Base, MetadataProxy


class ChecklistCategory(str, enum.Enum):
    """Categories of due diligence checklist items."""

    TITLE_VERIFICATION = "title_verification"
    ZONING_COMPLIANCE = "zoning_compliance"
    ENVIRONMENTAL_ASSESSMENT = "environmental_assessment"
    STRUCTURAL_SURVEY = "structural_survey"
    HERITAGE_CONSTRAINTS = "heritage_constraints"
    UTILITY_CAPACITY = "utility_capacity"
    ACCESS_RIGHTS = "access_rights"


class ChecklistStatus(str, enum.Enum):
    """Status of checklist items."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"


class ChecklistPriority(str, enum.Enum):
    """Priority levels for checklist items."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DeveloperChecklistTemplate(Base):
    """Template for due diligence checklist items by development scenario."""

    __tablename__ = "developer_checklist_templates"

    id = Column(UUID(), primary_key=True, default=uuid4)
    development_scenario = Column(String(50), nullable=False, index=True)
    category = Column(Enum(ChecklistCategory), nullable=False, index=True)
    item_title = Column(String(255), nullable=False)
    item_description = Column(Text, nullable=True)
    priority = Column(Enum(ChecklistPriority), nullable=False)
    typical_duration_days = Column(Integer, nullable=True)
    requires_professional = Column(Boolean, nullable=False, default=False)
    professional_type = Column(String(100), nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    property_checklists = relationship(
        "DeveloperPropertyChecklist",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DeveloperChecklistTemplate("
            f"scenario={self.development_scenario}, "
            f"category={self.category}, "
            f"title={self.item_title})>"
        )


class DeveloperPropertyChecklist(Base):
    """Checklist items for a specific property's due diligence."""

    __tablename__ = "developer_property_checklists"

    id = Column(UUID(), primary_key=True, default=uuid4)
    property_id = Column(UUID(), nullable=False, index=True)
    template_id = Column(
        UUID(),
        ForeignKey("developer_checklist_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    development_scenario = Column(String(50), nullable=False, index=True)
    category = Column(Enum(ChecklistCategory), nullable=False)
    item_title = Column(String(255), nullable=False)
    item_description = Column(Text, nullable=True)
    priority = Column(Enum(ChecklistPriority), nullable=False)
    status = Column(
        Enum(ChecklistStatus),
        nullable=False,
        default=ChecklistStatus.PENDING,
        index=True,
    )
    assigned_to = Column(
        UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    completed_by = Column(
        UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    metadata = MetadataProxy()
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    template = relationship(
        "DeveloperChecklistTemplate", back_populates="property_checklists"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<DeveloperPropertyChecklist("
            f"property_id={self.property_id}, "
            f"scenario={self.development_scenario}, "
            f"status={self.status}, "
            f"title={self.item_title})>"
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "development_scenario": self.development_scenario,
            "category": self.category.value,
            "item_title": self.item_title,
            "item_description": self.item_description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_date": (
                self.completed_date.isoformat() if self.completed_date else None
            ),
            "completed_by": str(self.completed_by) if self.completed_by else None,
            "notes": self.notes,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
