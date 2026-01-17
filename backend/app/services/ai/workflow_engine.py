"""Phase 3.4: Workflow Automation Engine.

AI-powered workflow orchestration and automation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_performance import AgentDeal, DealStatus

logger = logging.getLogger(__name__)


class WorkflowTrigger(str, Enum):
    """Events that can trigger workflows."""

    DEAL_CREATED = "deal_created"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    DEAL_VALUE_UPDATED = "deal_value_updated"
    DEAL_CLOSING = "deal_closing"
    SUBMISSION_APPROVED = "submission_approved"
    SUBMISSION_REJECTED = "submission_rejected"
    DOCUMENT_UPLOADED = "document_uploaded"
    DEADLINE_APPROACHING = "deadline_approaching"
    TASK_COMPLETED = "task_completed"
    MANUAL = "manual"


class ActionType(str, Enum):
    """Types of workflow actions."""

    SEND_NOTIFICATION = "send_notification"
    CREATE_TASK = "create_task"
    GENERATE_DOCUMENT = "generate_document"
    UPDATE_RECORD = "update_record"
    TRIGGER_APPROVAL = "trigger_approval"
    SCHEDULE_MEETING = "schedule_meeting"
    SEND_EMAIL = "send_email"
    CREATE_CHECKLIST = "create_checklist"
    ASSIGN_USER = "assign_user"
    LOG_ACTIVITY = "log_activity"


class WorkflowStatus(str, Enum):
    """Status of a workflow instance."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


@dataclass
class WorkflowAction:
    """An action within a workflow."""

    id: str
    action_type: ActionType
    name: str
    config: dict[str, Any]
    order: int
    condition: str | None = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowStep:
    """A step in a workflow execution."""

    action_id: str
    action_type: ActionType
    status: WorkflowStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class WorkflowDefinition:
    """Definition of an automated workflow."""

    id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    trigger_conditions: dict[str, Any]
    actions: list[WorkflowAction]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowInstance:
    """An instance of a running workflow."""

    id: str
    workflow_id: str
    workflow_name: str
    trigger_event: dict[str, Any]
    status: WorkflowStatus
    steps: list[WorkflowStep]
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


@dataclass
class WorkflowResult:
    """Result from workflow execution."""

    success: bool
    instance: WorkflowInstance | None = None
    error: str | None = None


class WorkflowEngineService:
    """Service for workflow automation."""

    def __init__(self) -> None:
        """Initialize the workflow engine."""
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._instances: dict[str, WorkflowInstance] = {}
        self._action_handlers: dict[ActionType, Callable] = {}
        self._initialized = True

        # Register default workflows
        self._register_default_workflows()

    def _register_default_workflows(self) -> None:
        """Register default system workflows."""
        # Workflow 1: New Deal Onboarding
        new_deal_workflow = WorkflowDefinition(
            id="wf_new_deal_onboarding",
            name="New Deal Onboarding",
            description="Automated onboarding when a new deal is created",
            trigger=WorkflowTrigger.DEAL_CREATED,
            trigger_conditions={},
            actions=[
                WorkflowAction(
                    id="act_1",
                    action_type=ActionType.CREATE_CHECKLIST,
                    name="Create Due Diligence Checklist",
                    config={"checklist_type": "due_diligence"},
                    order=1,
                ),
                WorkflowAction(
                    id="act_2",
                    action_type=ActionType.SEND_NOTIFICATION,
                    name="Notify Team",
                    config={
                        "template": "new_deal_notification",
                        "recipients": ["deal_team"],
                    },
                    order=2,
                ),
                WorkflowAction(
                    id="act_3",
                    action_type=ActionType.CREATE_TASK,
                    name="Schedule Site Visit",
                    config={
                        "task_type": "site_visit",
                        "due_days": 7,
                    },
                    order=3,
                ),
            ],
        )
        self._workflows[new_deal_workflow.id] = new_deal_workflow

        # Workflow 2: Deal Stage Progression
        stage_change_workflow = WorkflowDefinition(
            id="wf_stage_progression",
            name="Deal Stage Progression",
            description="Actions when deal moves to new stage",
            trigger=WorkflowTrigger.DEAL_STAGE_CHANGED,
            trigger_conditions={},
            actions=[
                WorkflowAction(
                    id="act_1",
                    action_type=ActionType.LOG_ACTIVITY,
                    name="Log Stage Change",
                    config={"activity_type": "stage_change"},
                    order=1,
                ),
                WorkflowAction(
                    id="act_2",
                    action_type=ActionType.SEND_NOTIFICATION,
                    name="Notify Stakeholders",
                    config={
                        "template": "stage_change_notification",
                    },
                    order=2,
                ),
                WorkflowAction(
                    id="act_3",
                    action_type=ActionType.CREATE_TASK,
                    name="Create Stage Tasks",
                    config={"task_template": "stage_tasks"},
                    order=3,
                    condition="new_stage in ['negotiation', 'due_diligence']",
                ),
            ],
        )
        self._workflows[stage_change_workflow.id] = stage_change_workflow

        # Workflow 3: Deadline Alert
        deadline_workflow = WorkflowDefinition(
            id="wf_deadline_alert",
            name="Deadline Alert",
            description="Alerts when deadlines are approaching",
            trigger=WorkflowTrigger.DEADLINE_APPROACHING,
            trigger_conditions={"days_before": 7},
            actions=[
                WorkflowAction(
                    id="act_1",
                    action_type=ActionType.SEND_NOTIFICATION,
                    name="Send Deadline Alert",
                    config={
                        "template": "deadline_alert",
                        "urgency": "high",
                    },
                    order=1,
                ),
                WorkflowAction(
                    id="act_2",
                    action_type=ActionType.SEND_EMAIL,
                    name="Email Reminder",
                    config={
                        "template": "deadline_reminder_email",
                    },
                    order=2,
                ),
            ],
        )
        self._workflows[deadline_workflow.id] = deadline_workflow

        # Workflow 4: Approval Process
        approval_workflow = WorkflowDefinition(
            id="wf_deal_approval",
            name="Deal Approval Process",
            description="Route deal for IC approval",
            trigger=WorkflowTrigger.DEAL_STAGE_CHANGED,
            trigger_conditions={"new_stage": "ic_review"},
            actions=[
                WorkflowAction(
                    id="act_1",
                    action_type=ActionType.GENERATE_DOCUMENT,
                    name="Generate IC Memo",
                    config={"document_type": "ic_memo"},
                    order=1,
                ),
                WorkflowAction(
                    id="act_2",
                    action_type=ActionType.TRIGGER_APPROVAL,
                    name="Request IC Approval",
                    config={
                        "approval_type": "investment_committee",
                        "approvers": ["ic_members"],
                    },
                    order=2,
                ),
                WorkflowAction(
                    id="act_3",
                    action_type=ActionType.SEND_NOTIFICATION,
                    name="Notify Approvers",
                    config={
                        "template": "approval_request",
                    },
                    order=3,
                ),
            ],
        )
        self._workflows[approval_workflow.id] = approval_workflow

        # Workflow 5: Post-Submission Follow-up
        submission_workflow = WorkflowDefinition(
            id="wf_submission_followup",
            name="Submission Follow-up",
            description="Follow-up actions after regulatory submission",
            trigger=WorkflowTrigger.SUBMISSION_APPROVED,
            trigger_conditions={},
            actions=[
                WorkflowAction(
                    id="act_1",
                    action_type=ActionType.UPDATE_RECORD,
                    name="Update Deal Status",
                    config={"update_type": "regulatory_status"},
                    order=1,
                ),
                WorkflowAction(
                    id="act_2",
                    action_type=ActionType.CREATE_TASK,
                    name="Schedule Next Steps",
                    config={"task_type": "post_approval"},
                    order=2,
                ),
                WorkflowAction(
                    id="act_3",
                    action_type=ActionType.SEND_NOTIFICATION,
                    name="Celebrate Success",
                    config={
                        "template": "approval_celebration",
                    },
                    order=3,
                ),
            ],
        )
        self._workflows[submission_workflow.id] = submission_workflow

    async def trigger_workflow(
        self,
        trigger: WorkflowTrigger,
        event_data: dict[str, Any],
        db: AsyncSession | None = None,
    ) -> list[WorkflowResult]:
        """Trigger workflows based on an event.

        Args:
            trigger: The trigger event
            event_data: Data associated with the event
            db: Database session

        Returns:
            List of WorkflowResult for each triggered workflow
        """
        results = []

        # Find matching workflows
        matching_workflows = [
            wf
            for wf in self._workflows.values()
            if wf.is_active
            and wf.trigger == trigger
            and self._matches_conditions(wf.trigger_conditions, event_data)
        ]

        # Execute each matching workflow
        for workflow in matching_workflows:
            result = await self._execute_workflow(workflow, event_data, db)
            results.append(result)

        return results

    def _matches_conditions(
        self,
        conditions: dict[str, Any],
        event_data: dict[str, Any],
    ) -> bool:
        """Check if event data matches trigger conditions."""
        if not conditions:
            return True

        for key, expected_value in conditions.items():
            actual_value = event_data.get(key)
            if actual_value != expected_value:
                return False

        return True

    async def _execute_workflow(
        self,
        workflow: WorkflowDefinition,
        event_data: dict[str, Any],
        db: AsyncSession | None,
    ) -> WorkflowResult:
        """Execute a workflow instance."""
        # Create instance
        instance = WorkflowInstance(
            id=str(uuid4()),
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            trigger_event=event_data,
            status=WorkflowStatus.RUNNING,
            steps=[],
            started_at=datetime.now(),
        )
        self._instances[instance.id] = instance

        try:
            # Sort actions by order
            sorted_actions = sorted(workflow.actions, key=lambda a: a.order)

            for action in sorted_actions:
                # Check condition
                if action.condition and not self._evaluate_condition(action.condition, event_data):
                    continue

                # Execute action
                step = WorkflowStep(
                    action_id=action.id,
                    action_type=action.action_type,
                    status=WorkflowStatus.RUNNING,
                    started_at=datetime.now(),
                )
                instance.steps.append(step)

                try:
                    result = await self._execute_action(action, event_data, db)
                    step.status = WorkflowStatus.COMPLETED
                    step.completed_at = datetime.now()
                    step.result = result
                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    step.completed_at = datetime.now()
                    step.error = str(e)

                    # Check if we should continue on failure
                    if action.action_type in [ActionType.TRIGGER_APPROVAL]:
                        raise  # Critical actions stop the workflow

            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.now()

            return WorkflowResult(
                success=True,
                instance=instance,
            )

        except Exception as e:
            instance.status = WorkflowStatus.FAILED
            instance.completed_at = datetime.now()
            instance.error = str(e)
            logger.error(f"Workflow {workflow.name} failed: {e}")

            return WorkflowResult(
                success=False,
                instance=instance,
                error=str(e),
            )

    def _evaluate_condition(
        self,
        condition: str,
        event_data: dict[str, Any],
    ) -> bool:
        """Evaluate a condition expression."""
        # Simple condition evaluation
        # In production, use a proper expression evaluator
        try:
            # Very basic evaluation for demo
            if " in " in condition:
                parts = condition.split(" in ")
                key = parts[0].strip()
                values = eval(parts[1].strip())  # noqa: S307
                return event_data.get(key) in values
            return True
        except Exception:
            return True

    async def _execute_action(
        self,
        action: WorkflowAction,
        event_data: dict[str, Any],
        db: AsyncSession | None,
    ) -> dict[str, Any]:
        """Execute a workflow action."""
        # In production, these would be fully implemented
        # Here we simulate the actions

        if action.action_type == ActionType.SEND_NOTIFICATION:
            return {
                "notification_sent": True,
                "template": action.config.get("template"),
                "recipients": action.config.get("recipients", ["owner"]),
            }

        elif action.action_type == ActionType.CREATE_TASK:
            due_date = datetime.now() + timedelta(days=action.config.get("due_days", 7))
            return {
                "task_created": True,
                "task_type": action.config.get("task_type"),
                "due_date": due_date.isoformat(),
            }

        elif action.action_type == ActionType.GENERATE_DOCUMENT:
            return {
                "document_generated": True,
                "document_type": action.config.get("document_type"),
                "document_id": str(uuid4()),
            }

        elif action.action_type == ActionType.UPDATE_RECORD:
            return {
                "record_updated": True,
                "update_type": action.config.get("update_type"),
            }

        elif action.action_type == ActionType.TRIGGER_APPROVAL:
            return {
                "approval_requested": True,
                "approval_type": action.config.get("approval_type"),
                "approvers": action.config.get("approvers", []),
                "approval_id": str(uuid4()),
            }

        elif action.action_type == ActionType.SCHEDULE_MEETING:
            return {
                "meeting_scheduled": True,
                "meeting_type": action.config.get("meeting_type"),
            }

        elif action.action_type == ActionType.SEND_EMAIL:
            return {
                "email_sent": True,
                "template": action.config.get("template"),
            }

        elif action.action_type == ActionType.CREATE_CHECKLIST:
            return {
                "checklist_created": True,
                "checklist_type": action.config.get("checklist_type"),
                "checklist_id": str(uuid4()),
            }

        elif action.action_type == ActionType.ASSIGN_USER:
            return {
                "user_assigned": True,
                "user_id": action.config.get("user_id"),
            }

        elif action.action_type == ActionType.LOG_ACTIVITY:
            return {
                "activity_logged": True,
                "activity_type": action.config.get("activity_type"),
                "timestamp": datetime.now().isoformat(),
            }

        return {"executed": True}

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a new workflow definition.

        Args:
            workflow: Workflow definition to register
        """
        self._workflows[workflow.id] = workflow

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        """Get a workflow definition by ID.

        Args:
            workflow_id: ID of the workflow

        Returns:
            WorkflowDefinition or None
        """
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[WorkflowDefinition]:
        """List all registered workflows.

        Returns:
            List of workflow definitions
        """
        return list(self._workflows.values())

    def get_instance(self, instance_id: str) -> WorkflowInstance | None:
        """Get a workflow instance by ID.

        Args:
            instance_id: ID of the instance

        Returns:
            WorkflowInstance or None
        """
        return self._instances.get(instance_id)

    def list_instances(
        self,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
    ) -> list[WorkflowInstance]:
        """List workflow instances with optional filters.

        Args:
            workflow_id: Filter by workflow ID
            status: Filter by status

        Returns:
            List of workflow instances
        """
        instances = list(self._instances.values())

        if workflow_id:
            instances = [i for i in instances if i.workflow_id == workflow_id]
        if status:
            instances = [i for i in instances if i.status == status]

        return sorted(instances, key=lambda i: i.started_at, reverse=True)

    async def check_deadlines(
        self,
        db: AsyncSession,
    ) -> list[WorkflowResult]:
        """Check for approaching deadlines and trigger alerts.

        Args:
            db: Database session

        Returns:
            List of triggered workflow results
        """
        results = []

        # Check deal deadlines
        deadline_threshold = datetime.now() + timedelta(days=7)
        deal_query = select(AgentDeal).where(
            AgentDeal.expected_close_date <= deadline_threshold,
            AgentDeal.status == DealStatus.OPEN,
        )
        result = await db.execute(deal_query)
        deals = result.scalars().all()

        for deal in deals:
            days_until = (
                (deal.expected_close_date - datetime.now().date()).days
                if deal.expected_close_date
                else 999
            )
            if 0 < days_until <= 7:
                trigger_results = await self.trigger_workflow(
                    WorkflowTrigger.DEADLINE_APPROACHING,
                    {
                        "deal_id": str(deal.id),
                        "deal_title": deal.title,
                        "deadline_type": "expected_close",
                        "deadline_date": (
                            deal.expected_close_date.isoformat()
                            if deal.expected_close_date
                            else None
                        ),
                        "days_until": days_until,
                    },
                    db,
                )
                results.extend(trigger_results)

        return results


# Singleton instance
workflow_engine_service = WorkflowEngineService()
