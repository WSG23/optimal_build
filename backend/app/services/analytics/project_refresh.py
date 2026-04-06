"""Build persisted Advanced Intelligence snapshots from live project records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import erfc, sqrt
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.advanced_intelligence import (
    WorkspaceCorrelationSnapshot,
    WorkspaceGraphSnapshot,
    WorkspacePredictiveSnapshot,
    WorkspaceSignalSnapshot,
)
from app.models.finance import FinScenario
from app.models.projects import Project
from app.models.workflow import ApprovalWorkflow, StepStatus, WorkflowStatus
from app.services.analytics.workspace_snapshots import WorkspaceAnalyticsSnapshotService

_SNAPSHOT_MAX_AGE = timedelta(seconds=60)


@dataclass(slots=True)
class _WorkflowMetrics:
    workflow: ApprovalWorkflow
    completion: float
    total_steps: int
    approved_steps: int
    age_days: float


@dataclass(slots=True)
class _ScenarioMetrics:
    scenario: FinScenario
    probability: float
    capital_sources: int
    primary_result: float | None


class ProjectAnalyticsSnapshotRefresher:
    """Refresh snapshot payloads from persisted project data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._snapshot_service = WorkspaceAnalyticsSnapshotService(session)

    async def ensure_project_snapshots(
        self,
        *,
        project_id: str,
        workspace_id: str,
        snapshot_kind: str,
    ) -> None:
        """Refresh snapshots when the project scope is missing or stale."""

        if await self._snapshot_is_fresh(workspace_id, snapshot_kind=snapshot_kind):
            return
        await self.refresh_project_snapshots(
            project_id=project_id,
            workspace_id=workspace_id,
        )

    async def refresh_project_snapshots(
        self,
        *,
        project_id: str,
        workspace_id: str,
    ) -> None:
        """Rebuild all snapshot payloads for a project scope."""

        project = await self._session.get(Project, project_id)
        if project is None:
            return

        workflows = await self._load_workflows(project_id)
        scenarios = await self._load_finance_scenarios(project_id)

        workflow_metrics = [self._build_workflow_metrics(item) for item in workflows]
        scenario_metrics = [self._build_scenario_metrics(item) for item in scenarios]
        generated_at = datetime.now(UTC)

        signal_payload, signal_sample_size = self._build_signals_payload(
            project=project,
            workflow_metrics=workflow_metrics,
            scenario_metrics=scenario_metrics,
            generated_at=generated_at,
        )
        graph_payload, graph_sample_size = self._build_graph_payload(
            project=project,
            workflow_metrics=workflow_metrics,
            scenario_metrics=scenario_metrics,
            generated_at=generated_at,
        )
        predictive_payload, predictive_sample_size = self._build_predictive_payload(
            project=project,
            workflow_metrics=workflow_metrics,
            scenario_metrics=scenario_metrics,
            generated_at=generated_at,
        )
        correlation_payload, correlation_sample_size = self._build_correlation_payload(
            project=project,
            workflow_metrics=workflow_metrics,
            scenario_metrics=scenario_metrics,
            generated_at=generated_at,
        )

        await self._snapshot_service.save_signal_snapshot(
            workspace_id,
            payload=signal_payload,
            sample_size=signal_sample_size,
        )
        await self._snapshot_service.save_graph_snapshot(
            workspace_id,
            payload=graph_payload,
            sample_size=graph_sample_size,
        )
        await self._snapshot_service.save_predictive_snapshot(
            workspace_id,
            payload=predictive_payload,
            sample_size=predictive_sample_size,
        )
        await self._snapshot_service.save_correlation_snapshot(
            workspace_id,
            payload=correlation_payload,
            sample_size=correlation_sample_size,
        )

    async def _snapshot_is_fresh(
        self,
        workspace_id: str,
        *,
        snapshot_kind: str,
    ) -> bool:
        now = datetime.now(UTC)
        snapshot_models = {
            "signals": WorkspaceSignalSnapshot,
            "graph": WorkspaceGraphSnapshot,
            "predictive": WorkspacePredictiveSnapshot,
            "correlation": WorkspaceCorrelationSnapshot,
        }
        model = snapshot_models[snapshot_kind]
        snapshot = await self._session.scalar(
            select(model).where(model.workspace_id == workspace_id)
        )
        if snapshot is None:
            return False
        updated_at = snapshot.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=UTC)
        return now - updated_at <= _SNAPSHOT_MAX_AGE

    async def _load_workflows(self, project_id: str) -> list[ApprovalWorkflow]:
        result = await self._session.scalars(
            select(ApprovalWorkflow)
            .where(ApprovalWorkflow.project_id == project_id)
            .options(selectinload(ApprovalWorkflow.steps))
            .order_by(ApprovalWorkflow.created_at.asc())
        )
        return list(result.unique().all())

    async def _load_finance_scenarios(self, project_id: str) -> list[FinScenario]:
        result = await self._session.scalars(
            select(FinScenario)
            .where(FinScenario.project_id == project_id)
            .options(
                selectinload(FinScenario.results),
                selectinload(FinScenario.capital_stack),
            )
            .order_by(FinScenario.created_at.asc())
        )
        return list(result.unique().all())

    def _build_workflow_metrics(self, workflow: ApprovalWorkflow) -> _WorkflowMetrics:
        steps = workflow.steps or []
        total_steps = len(steps)
        approved_steps = sum(
            1
            for step in steps
            if step.status in {StepStatus.APPROVED, StepStatus.SKIPPED}
        )
        completion = self._workflow_completion_ratio(workflow)
        age_days = max(
            (datetime.now(UTC) - self._coerce_utc(workflow.created_at)).total_seconds()
            / 86400,
            0.0,
        )
        return _WorkflowMetrics(
            workflow=workflow,
            completion=completion,
            total_steps=total_steps,
            approved_steps=approved_steps,
            age_days=age_days,
        )

    def _build_scenario_metrics(self, scenario: FinScenario) -> _ScenarioMetrics:
        result_metric = self._primary_scenario_result(scenario)
        capital_sources = sum(
            1
            for item in scenario.capital_stack
            if self._to_float(item.amount) is not None
        )
        probability = self._scenario_probability(
            scenario, result_metric, capital_sources
        )
        return _ScenarioMetrics(
            scenario=scenario,
            probability=probability,
            capital_sources=capital_sources,
            primary_result=result_metric,
        )

    def _build_signals_payload(
        self,
        *,
        project: Project,
        workflow_metrics: Sequence[_WorkflowMetrics],
        scenario_metrics: Sequence[_ScenarioMetrics],
        generated_at: datetime,
    ) -> tuple[dict[str, object], int]:
        approval_readiness = self._approval_readiness(project, workflow_metrics)
        finance_coverage = self._finance_coverage(scenario_metrics)
        active_workflows = sum(
            1
            for item in workflow_metrics
            if item.workflow.status
            in {WorkflowStatus.DRAFT, WorkflowStatus.IN_PROGRESS}
        )
        intelligence_score = self._intelligence_score(
            project=project,
            approval_readiness=approval_readiness,
            finance_coverage=finance_coverage,
        )

        signals = [
            {
                "signalId": "approval-readiness",
                "label": "Approval Readiness",
                "value": approval_readiness,
                "unit": "%",
                "trend": self._approval_readiness_trend(workflow_metrics),
            },
            {
                "signalId": "finance-coverage",
                "label": "Finance Coverage",
                "value": finance_coverage,
                "unit": "%",
                "trend": self._finance_coverage_trend(scenario_metrics),
            },
            {
                "signalId": "active-workflows",
                "label": "Active Workflows",
                "value": float(active_workflows) if workflow_metrics else None,
                "unit": "count",
                "trend": self._active_workflow_trend(workflow_metrics),
            },
            {
                "signalId": "intelligence-score",
                "label": "Intelligence Score",
                "value": intelligence_score,
                "unit": "score",
                "trend": [],
            },
        ]
        available_values = [
            item["value"] for item in signals if item["value"] is not None
        ]
        sample_size = len(workflow_metrics) + len(scenario_metrics)
        if not available_values:
            return (
                {
                    "kind": "signals",
                    "status": "empty",
                    "summary": (
                        "No project, workflow, or finance records are available "
                        f"to compute signals for '{project.project_name}'."
                    ),
                },
                0,
            )

        return (
            {
                "kind": "signals",
                "status": "ok",
                "summary": (
                    f"Computed {len(available_values)} signal groups from "
                    f"{sample_size} workflow and finance records."
                ),
                "generatedAt": self._isoformat(generated_at),
                "signals": signals,
            },
            sample_size,
        )

    def _build_graph_payload(
        self,
        *,
        project: Project,
        workflow_metrics: Sequence[_WorkflowMetrics],
        scenario_metrics: Sequence[_ScenarioMetrics],
        generated_at: datetime,
    ) -> tuple[dict[str, object], int]:
        has_network = bool(workflow_metrics or scenario_metrics)
        if not has_network:
            return (
                {
                    "kind": "graph",
                    "status": "empty",
                    "summary": (
                        "Add approval workflows or finance scenarios to render "
                        f"a relationship graph for '{project.project_name}'."
                    ),
                },
                0,
            )

        project_progress = self._project_progress(project)
        nodes: list[dict[str, object]] = [
            {
                "id": f"project:{project.id}",
                "label": project.project_name,
                "category": "Project",
                "score": project_progress / 100,
            },
            {
                "id": f"phase:{project.current_phase.value}",
                "label": self._humanize_token(project.current_phase.value),
                "category": "Workflow",
                "score": project_progress / 100,
            },
        ]
        edges: list[dict[str, object]] = [
            {
                "id": f"edge:project-phase:{project.id}",
                "source": f"project:{project.id}",
                "target": f"phase:{project.current_phase.value}",
                "weight": max(project_progress / 100, 0.25),
            }
        ]

        if project.owner_email:
            owner_label = project.owner_email.split("@", 1)[0] or "Project owner"
            nodes.append(
                {
                    "id": f"owner:{project.id}",
                    "label": owner_label,
                    "category": "Team",
                    "score": 0.6,
                }
            )
            edges.append(
                {
                    "id": f"edge:owner-project:{project.id}",
                    "source": f"owner:{project.id}",
                    "target": f"project:{project.id}",
                    "weight": 0.6,
                }
            )

        for item in workflow_metrics[:6]:
            workflow = item.workflow
            node_id = f"workflow:{workflow.id}"
            nodes.append(
                {
                    "id": node_id,
                    "label": workflow.title,
                    "category": "Workflow",
                    "score": item.completion,
                }
            )
            edges.append(
                {
                    "id": f"edge:phase-workflow:{workflow.id}",
                    "source": f"phase:{project.current_phase.value}",
                    "target": node_id,
                    "weight": max(item.completion, 0.2),
                }
            )

        primary_scenario_id: str | None = None
        for item in scenario_metrics[:4]:
            scenario = item.scenario
            node_id = f"scenario:{scenario.id}"
            if scenario.is_primary and primary_scenario_id is None:
                primary_scenario_id = node_id
            nodes.append(
                {
                    "id": node_id,
                    "label": scenario.name,
                    "category": "Finance",
                    "score": item.probability,
                }
            )
            edges.append(
                {
                    "id": f"edge:project-scenario:{scenario.id}",
                    "source": f"project:{project.id}",
                    "target": node_id,
                    "weight": max(item.probability, 0.25),
                }
            )

        if primary_scenario_id is not None:
            for item in workflow_metrics[:4]:
                edges.append(
                    {
                        "id": f"edge:workflow-scenario:{item.workflow.id}",
                        "source": f"workflow:{item.workflow.id}",
                        "target": primary_scenario_id,
                        "weight": max((item.completion + 0.6) / 2, 0.2),
                    }
                )

        return (
            {
                "kind": "graph",
                "status": "ok",
                "summary": (
                    f"Mapped {len(nodes)} project, workflow, and finance nodes "
                    f"for '{project.project_name}'."
                ),
                "generatedAt": self._isoformat(generated_at),
                "graph": {"nodes": nodes, "edges": edges},
            },
            len(workflow_metrics) + len(scenario_metrics),
        )

    def _build_predictive_payload(
        self,
        *,
        project: Project,
        workflow_metrics: Sequence[_WorkflowMetrics],
        scenario_metrics: Sequence[_ScenarioMetrics],
        generated_at: datetime,
    ) -> tuple[dict[str, object], int]:
        segments: list[dict[str, object]] = []

        project_progress = self._project_progress(project)
        segments.append(
            {
                "segmentId": f"project:{project.id}:delivery",
                "segmentName": "Project delivery readiness",
                "baseline": round(project_progress, 2),
                "projection": round(min(project_progress + 12.0, 100.0), 2),
                "probability": round(
                    self._clamp(project_progress / 100, 0.05, 0.99), 4
                ),
            }
        )

        for item in sorted(
            workflow_metrics,
            key=lambda metric: metric.workflow.updated_at,
            reverse=True,
        )[:3]:
            segments.append(
                {
                    "segmentId": f"workflow:{item.workflow.id}",
                    "segmentName": item.workflow.title,
                    "baseline": float(item.approved_steps),
                    "projection": float(max(item.total_steps, item.approved_steps)),
                    "probability": round(item.completion, 4),
                }
            )

        for item in scenario_metrics[:2]:
            baseline = item.primary_result if item.primary_result is not None else 0.0
            projection = (
                baseline * (0.95 + item.probability * 0.2)
                if baseline != 0
                else item.probability * 100
            )
            segments.append(
                {
                    "segmentId": f"scenario:{item.scenario.id}",
                    "segmentName": item.scenario.name,
                    "baseline": round(baseline, 2),
                    "projection": round(projection, 2),
                    "probability": round(item.probability, 4),
                }
            )

        if len(segments) <= 1 and not workflow_metrics and not scenario_metrics:
            return (
                {
                    "kind": "predictive",
                    "status": "empty",
                    "summary": (
                        "Predictive signals need at least one workflow or finance "
                        f"scenario for '{project.project_name}'."
                    ),
                },
                0,
            )

        return (
            {
                "kind": "predictive",
                "status": "ok",
                "summary": (
                    f"Built {len(segments)} predictive segments from live project, "
                    "workflow, and finance records."
                ),
                "generatedAt": self._isoformat(generated_at),
                "horizonMonths": 6,
                "segments": segments,
            },
            len(segments),
        )

    def _build_correlation_payload(
        self,
        *,
        project: Project,
        workflow_metrics: Sequence[_WorkflowMetrics],
        scenario_metrics: Sequence[_ScenarioMetrics],
        generated_at: datetime,
    ) -> tuple[dict[str, object], int]:
        relationships: list[dict[str, object]] = []

        workflow_steps = [float(item.total_steps) for item in workflow_metrics]
        workflow_completion = [item.completion for item in workflow_metrics]
        workflow_age = [item.age_days for item in workflow_metrics]
        scenario_sources = [float(item.capital_sources) for item in scenario_metrics]
        scenario_probabilities = [item.probability for item in scenario_metrics]

        relationships.extend(
            self._build_relationships(
                (
                    (
                        "workflow-steps-completion",
                        "Workflow step count",
                        "Workflow readiness",
                        workflow_steps,
                        workflow_completion,
                    ),
                    (
                        "workflow-age-completion",
                        "Workflow age (days)",
                        "Workflow readiness",
                        workflow_age,
                        workflow_completion,
                    ),
                    (
                        "capital-sources-confidence",
                        "Capital sources",
                        "Finance confidence",
                        scenario_sources,
                        scenario_probabilities,
                    ),
                )
            )
        )

        if not relationships:
            return (
                {
                    "kind": "correlation",
                    "status": "empty",
                    "summary": (
                        "Cross-correlation needs at least three varying workflow or "
                        f"finance observations for '{project.project_name}'."
                    ),
                },
                0,
            )

        return (
            {
                "kind": "correlation",
                "status": "ok",
                "summary": (
                    f"Computed {len(relationships)} relationship coefficients "
                    f"for '{project.project_name}'."
                ),
                "updatedAt": self._isoformat(generated_at),
                "relationships": relationships,
            },
            len(relationships),
        )

    def _build_relationships(
        self,
        candidates: Iterable[tuple[str, str, str, Sequence[float], Sequence[float]]],
    ) -> list[dict[str, object]]:
        relationships: list[dict[str, object]] = []
        for pair_id, driver, outcome, xs, ys in candidates:
            if len(xs) < 3 or len(xs) != len(ys):
                continue
            if len(set(xs)) <= 1 or len(set(ys)) <= 1:
                continue
            coefficient = self._pearson(xs, ys)
            p_value = self._approximate_p_value(coefficient, len(xs))
            relationships.append(
                {
                    "pairId": pair_id,
                    "driver": driver,
                    "outcome": outcome,
                    "coefficient": round(coefficient, 4),
                    "pValue": round(p_value, 4),
                }
            )
        return relationships

    def _approval_readiness(
        self,
        project: Project,
        workflow_metrics: Sequence[_WorkflowMetrics],
    ) -> float | None:
        if workflow_metrics:
            return round(
                sum(item.completion for item in workflow_metrics)
                / len(workflow_metrics)
                * 100,
                2,
            )
        project_progress = self._to_float(project.completion_percentage)
        if project_progress is None:
            return None
        return round(project_progress, 2)

    def _finance_coverage(
        self,
        scenario_metrics: Sequence[_ScenarioMetrics],
    ) -> float | None:
        if not scenario_metrics:
            return None
        return round(
            sum(item.probability for item in scenario_metrics)
            / len(scenario_metrics)
            * 100,
            2,
        )

    def _intelligence_score(
        self,
        *,
        project: Project,
        approval_readiness: float | None,
        finance_coverage: float | None,
    ) -> float | None:
        components = [
            value
            for value in (
                approval_readiness,
                finance_coverage,
                self._project_progress(project),
            )
            if value is not None
        ]
        if not components:
            return None
        return round(sum(components) / len(components), 2)

    def _approval_readiness_trend(
        self,
        workflow_metrics: Sequence[_WorkflowMetrics],
    ) -> list[dict[str, object]]:
        if not workflow_metrics:
            return []
        running_total = 0.0
        points: list[dict[str, object]] = []
        for index, item in enumerate(workflow_metrics, start=1):
            running_total += item.completion
            points.append(
                {
                    "timestamp": self._isoformat(item.workflow.created_at),
                    "value": round((running_total / index) * 100, 2),
                }
            )
        return points

    def _finance_coverage_trend(
        self,
        scenario_metrics: Sequence[_ScenarioMetrics],
    ) -> list[dict[str, object]]:
        if not scenario_metrics:
            return []
        running_total = 0.0
        points: list[dict[str, object]] = []
        for index, item in enumerate(scenario_metrics, start=1):
            running_total += item.probability
            points.append(
                {
                    "timestamp": self._isoformat(item.scenario.created_at),
                    "value": round((running_total / index) * 100, 2),
                }
            )
        return points

    def _active_workflow_trend(
        self,
        workflow_metrics: Sequence[_WorkflowMetrics],
    ) -> list[dict[str, object]]:
        if not workflow_metrics:
            return []
        active = 0
        points: list[dict[str, object]] = []
        for item in workflow_metrics:
            if item.workflow.status in {
                WorkflowStatus.DRAFT,
                WorkflowStatus.IN_PROGRESS,
            }:
                active += 1
            points.append(
                {
                    "timestamp": self._isoformat(item.workflow.created_at),
                    "value": float(active),
                }
            )
        return points

    def _project_progress(self, project: Project) -> float:
        completion_percentage = self._to_float(project.completion_percentage)
        if completion_percentage is not None:
            return round(self._clamp(completion_percentage, 0.0, 100.0), 2)
        phase_progress = {
            "concept": 10.0,
            "feasibility": 22.0,
            "design": 38.0,
            "approval": 52.0,
            "tender": 64.0,
            "construction": 78.0,
            "testing_commissioning": 90.0,
            "handover": 96.0,
            "operation": 100.0,
        }
        return phase_progress.get(project.current_phase.value, 0.0)

    def _workflow_completion_ratio(self, workflow: ApprovalWorkflow) -> float:
        if workflow.status == WorkflowStatus.APPROVED:
            return 1.0
        if workflow.status in {WorkflowStatus.REJECTED, WorkflowStatus.CANCELLED}:
            return 0.05

        weighted_total = 0.0
        steps = workflow.steps or []
        if steps:
            for step in steps:
                if step.status in {StepStatus.APPROVED, StepStatus.SKIPPED}:
                    weighted_total += 1.0
                elif step.status == StepStatus.IN_REVIEW:
                    weighted_total += 0.65
                elif step.status == StepStatus.PENDING:
                    weighted_total += 0.2
            return round(self._clamp(weighted_total / len(steps), 0.05, 0.99), 4)

        if workflow.status == WorkflowStatus.IN_PROGRESS:
            return 0.55
        return 0.2

    def _primary_scenario_result(self, scenario: FinScenario) -> float | None:
        preferred_names = ("irr", "roi", "npv", "profit", "yield")
        preferred_result: float | None = None
        fallback_result: float | None = None
        for result in scenario.results:
            value = self._to_float(result.value)
            if value is None:
                continue
            fallback_result = value if fallback_result is None else fallback_result
            name = result.name.lower()
            if any(token in name for token in preferred_names):
                preferred_result = value
                break
        return preferred_result if preferred_result is not None else fallback_result

    def _scenario_probability(
        self,
        scenario: FinScenario,
        result_metric: float | None,
        capital_sources: int,
    ) -> float:
        result_component = 0.45
        if result_metric is not None:
            if result_metric > 0:
                result_component = 0.75
            elif result_metric < 0:
                result_component = 0.2
        capital_component = self._clamp(capital_sources / 3, 0.0, 1.0)
        primary_bonus = 0.1 if scenario.is_primary else 0.0
        return round(
            self._clamp(
                0.2
                + (result_component * 0.45)
                + (capital_component * 0.25)
                + primary_bonus,
                0.05,
                0.99,
            ),
            4,
        )

    def _pearson(self, xs: Sequence[float], ys: Sequence[float]) -> float:
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
        denominator_x = sqrt(sum((x - mean_x) ** 2 for x in xs))
        denominator_y = sqrt(sum((y - mean_y) ** 2 for y in ys))
        denominator = denominator_x * denominator_y
        if denominator == 0:
            return 0.0
        return self._clamp(numerator / denominator, -1.0, 1.0)

    def _approximate_p_value(self, coefficient: float, sample_size: int) -> float:
        if sample_size < 3 or abs(coefficient) >= 1:
            return 0.0
        t_stat = abs(coefficient) * sqrt(
            (sample_size - 2) / max(1 - coefficient**2, 1e-6)
        )
        return self._clamp(erfc(t_stat / sqrt(2)), 0.0, 1.0)

    def _humanize_token(self, value: str) -> str:
        return value.replace("_", " ").title()

    def _coerce_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _isoformat(self, value: datetime) -> str:
        return (
            self._coerce_utc(value)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    def _to_float(self, value: object) -> float | None:
        if value is None:
            return None
        if not isinstance(value, (int, float, Decimal, str)):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(value, maximum))


__all__ = ["ProjectAnalyticsSnapshotRefresher"]
