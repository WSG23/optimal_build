"""Approval workflow models for project governance."""

import uuid
from enum import Enum

from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from app.models.users import UserRole
from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class WorkflowStatus(str, Enum):
    """Status of an overall workflow."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Status of an individual approval step."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class ApprovalWorkflow(BaseModel):
    """A collection of approval steps required for a milestone."""

    __tablename__ = "approval_workflows"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Type of workflow (e.g., 'feasibility_signoff', 'design_review')
    workflow_type = Column(String(50), nullable=False, index=True)

    status = Column(
        SQLEnum(WorkflowStatus, values_callable=lambda x: [e.value for e in x]),
        default=WorkflowStatus.DRAFT,
        nullable=False,
        index=True,
    )

    created_by_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    completed_at = Column(DateTime)

    # Relationships
    project = relationship("Project", backref="workflows")
    created_by = relationship("User", foreign_keys=[created_by_id])
    steps = relationship(
        "ApprovalStep",
        back_populates="workflow",
        order_by="ApprovalStep.sequence_order",
        cascade="all, delete-orphan",
    )


class ApprovalStep(BaseModel):
    """A single step in an approval workflow."""

    __tablename__ = "approval_steps"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(
        UUID(), ForeignKey("approval_workflows.id"), nullable=False, index=True
    )

    name = Column(String(255), nullable=False)
    sequence_order = Column(Integer, nullable=False)

    # Who is required to approve this step?
    # Can be a specific role (ANY user with this role in the project)
    required_role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    # OR a specific user
    required_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)

    status = Column(
        SQLEnum(StepStatus, values_callable=lambda x: [e.value for e in x]),
        default=StepStatus.PENDING,
        nullable=False,
    )

    # Outcome
    approved_by_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    decision_at = Column(DateTime)
    comments = Column(Text)

    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    required_user = relationship("User", foreign_keys=[required_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
