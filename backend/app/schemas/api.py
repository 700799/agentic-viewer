"""API response/request DTOs (the read models the frontend consumes)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---- Sessions ----
class SessionSummary(BaseModel):
    id: uuid.UUID
    external_id: str
    source: str
    title: str | None
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    span_count: int
    meta: dict = Field(default_factory=dict)


class SessionList(BaseModel):
    items: list[SessionSummary]
    next_cursor: str | None = None


class SessionPatch(BaseModel):
    title: str | None = None
    status: str | None = None


class IngestResult(BaseModel):
    session_id: uuid.UUID
    spans_ingested: int
    edges_ingested: int


# ---- Graph (DAG view) ----
class GraphNode(BaseModel):
    id: str
    type: str  # react-flow node type: agent/llm/tool/mcpTool/mcpServer/file/memory/group
    label: str
    parent_id: str | None = None
    group: str | None = None
    data: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # call/handoff/data/mcp
    label: str | None = None


class GroupInfo(BaseModel):
    id: str
    label: str
    node_ids: list[str]


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    groups: list[GroupInfo] = Field(default_factory=list)


# ---- Timeline ----
class TimelinePreview(BaseModel):
    prompt: str | None = None
    response: str | None = None
    tool_input: str | None = None
    tool_output: str | None = None
    error: str | None = None


class TimelineCost(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0


class TimelineEvent(BaseModel):
    span_id: uuid.UUID
    sequence: int
    kind: str
    name: str
    agent_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_ms: int | None = None
    status: str
    preview: TimelinePreview
    cost: TimelineCost | None = None


class TimelineResponse(BaseModel):
    items: list[TimelineEvent]


class SpanIODetail(BaseModel):
    io_type: str
    role: str | None
    content_text: str | None
    file_path: str | None
    byte_size: int | None
    truncated: bool


class SpanDetail(BaseModel):
    id: uuid.UUID
    external_span_id: str
    kind: str
    name: str
    agent_name: str | None
    status: str
    start_time: datetime | None
    end_time: datetime | None
    duration_ms: int | None
    attributes: dict
    io: list[SpanIODetail]
    cost: TimelineCost | None
    error: str | None


# ---- Cost ----
class CostTotal(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0


class CostPerAgent(BaseModel):
    agent_id: uuid.UUID | None
    name: str
    cost_usd: float
    input_tokens: int
    output_tokens: int


class CostPerModel(BaseModel):
    model: str
    cost_usd: float
    input_tokens: int
    output_tokens: int


class CostPerStep(BaseModel):
    span_id: uuid.UUID
    name: str
    sequence: int
    cost_usd: float


class CostCumulativePoint(BaseModel):
    sequence: int
    cumulative_cost_usd: float


class CostReport(BaseModel):
    total: CostTotal
    per_agent: list[CostPerAgent]
    per_model: list[CostPerModel]
    per_step: list[CostPerStep]
    timeline: list[CostCumulativePoint]


# ---- Diagram ----
class DiagramResponse(BaseModel):
    type: str
    mermaid: str


# ---- Compare ----
class CompareSummary(BaseModel):
    cost_delta_usd: float
    duration_delta_ms: int
    span_count_delta: int


class AlignedSpan(BaseModel):
    signature: str
    status: str  # added/removed/changed/same
    a_cost_usd: float | None = None
    b_cost_usd: float | None = None
    a_duration_ms: int | None = None
    b_duration_ms: int | None = None


class CompareCostByAgent(BaseModel):
    name: str
    a_usd: float
    b_usd: float
    delta_usd: float


class CompareReport(BaseModel):
    summary: CompareSummary
    aligned_spans: list[AlignedSpan]
    cost_by_agent: list[CompareCostByAgent]
