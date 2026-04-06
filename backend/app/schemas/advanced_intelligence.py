"""Typed response schemas for Advanced Intelligence routes."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias, cast

from pydantic import BaseModel, Field, TypeAdapter


class GraphNode(BaseModel):
    id: str
    label: str
    category: str
    score: float = Field(ge=0)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    weight: float | None = None


class GraphSuccessResponse(BaseModel):
    kind: Literal["graph"]
    status: Literal["ok"]
    summary: str
    generatedAt: str
    graph: dict[str, list[GraphNode] | list[GraphEdge]]


class GraphEmptyResponse(BaseModel):
    kind: Literal["graph"]
    status: Literal["empty"]
    summary: str


class GraphErrorResponse(BaseModel):
    kind: Literal["graph"]
    status: Literal["error"]
    error: str


GraphIntelligenceResponse: TypeAlias = Annotated[
    GraphSuccessResponse | GraphEmptyResponse | GraphErrorResponse,
    Field(discriminator="status"),
]


class PredictiveSegment(BaseModel):
    segmentId: str
    segmentName: str
    baseline: float
    projection: float
    probability: float = Field(ge=0, le=1)


class PredictiveSuccessResponse(BaseModel):
    kind: Literal["predictive"]
    status: Literal["ok"]
    summary: str
    generatedAt: str
    horizonMonths: int = Field(ge=0)
    segments: list[PredictiveSegment]


class PredictiveEmptyResponse(BaseModel):
    kind: Literal["predictive"]
    status: Literal["empty"]
    summary: str


class PredictiveErrorResponse(BaseModel):
    kind: Literal["predictive"]
    status: Literal["error"]
    error: str


PredictiveIntelligenceResponse: TypeAlias = Annotated[
    PredictiveSuccessResponse | PredictiveEmptyResponse | PredictiveErrorResponse,
    Field(discriminator="status"),
]


class CorrelationRelationship(BaseModel):
    pairId: str
    driver: str
    outcome: str
    coefficient: float = Field(ge=-1, le=1)
    pValue: float = Field(ge=0, le=1)


class CorrelationSuccessResponse(BaseModel):
    kind: Literal["correlation"]
    status: Literal["ok"]
    summary: str
    updatedAt: str
    relationships: list[CorrelationRelationship]


class CorrelationEmptyResponse(BaseModel):
    kind: Literal["correlation"]
    status: Literal["empty"]
    summary: str


class CorrelationErrorResponse(BaseModel):
    kind: Literal["correlation"]
    status: Literal["error"]
    error: str


CrossCorrelationIntelligenceResponse: TypeAlias = Annotated[
    CorrelationSuccessResponse | CorrelationEmptyResponse | CorrelationErrorResponse,
    Field(discriminator="status"),
]


class SignalHistoryPoint(BaseModel):
    timestamp: str
    value: float


class WorkspaceSignal(BaseModel):
    signalId: str
    label: str
    value: float | None = None
    unit: str | None = None
    trend: list[SignalHistoryPoint] = Field(default_factory=list)


class SignalSuccessResponse(BaseModel):
    kind: Literal["signals"]
    status: Literal["ok"]
    summary: str
    generatedAt: str
    signals: list[WorkspaceSignal]


class SignalEmptyResponse(BaseModel):
    kind: Literal["signals"]
    status: Literal["empty"]
    summary: str


class SignalErrorResponse(BaseModel):
    kind: Literal["signals"]
    status: Literal["error"]
    error: str


WorkspaceSignalsResponse: TypeAlias = Annotated[
    SignalSuccessResponse | SignalEmptyResponse | SignalErrorResponse,
    Field(discriminator="status"),
]

_graph_adapter: TypeAdapter[GraphIntelligenceResponse] = TypeAdapter(
    GraphIntelligenceResponse
)
_predictive_adapter: TypeAdapter[PredictiveIntelligenceResponse] = TypeAdapter(
    PredictiveIntelligenceResponse
)
_correlation_adapter: TypeAdapter[CrossCorrelationIntelligenceResponse] = TypeAdapter(
    CrossCorrelationIntelligenceResponse
)
_signals_adapter: TypeAdapter[WorkspaceSignalsResponse] = TypeAdapter(
    WorkspaceSignalsResponse
)


def parse_graph_response(payload: Any) -> GraphIntelligenceResponse:
    return cast(GraphIntelligenceResponse, _graph_adapter.validate_python(payload))


def parse_predictive_response(payload: Any) -> PredictiveIntelligenceResponse:
    return cast(
        PredictiveIntelligenceResponse,
        _predictive_adapter.validate_python(payload),
    )


def parse_correlation_response(payload: Any) -> CrossCorrelationIntelligenceResponse:
    return cast(
        CrossCorrelationIntelligenceResponse,
        _correlation_adapter.validate_python(payload),
    )


def parse_signals_response(payload: Any) -> WorkspaceSignalsResponse:
    return cast(WorkspaceSignalsResponse, _signals_adapter.validate_python(payload))


__all__ = [
    "CorrelationRelationship",
    "CrossCorrelationIntelligenceResponse",
    "GraphEdge",
    "GraphIntelligenceResponse",
    "GraphNode",
    "PredictiveIntelligenceResponse",
    "PredictiveSegment",
    "WorkspaceSignal",
    "WorkspaceSignalsResponse",
    "parse_correlation_response",
    "parse_graph_response",
    "parse_predictive_response",
    "parse_signals_response",
]
