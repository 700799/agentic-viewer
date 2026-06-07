"""The Canonical Trace Envelope — the contract every adapter emits.

This is the single most important type in the system. Each framework adapter
(Claude Code, OpenAI Agents, LangGraph, CrewAI, AutoGen) is a pure function
``native_trace -> CanonicalEnvelope``. The projector consumes envelopes and is the
only writer of the projected tables.

The JSON Schema of :class:`CanonicalEnvelope` is exported and converted to TypeScript
for the frontend, so backend and frontend never drift.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"


class Source(str, Enum):
    claude_code = "claude_code"
    openai_agents = "openai_agents"
    langgraph = "langgraph"
    crewai = "crewai"
    autogen = "autogen"
    custom = "custom"


class SpanKind(str, Enum):
    session_root = "session_root"
    agent = "agent"
    llm = "llm"
    tool = "tool"
    mcp_tool = "mcp_tool"
    file_io = "file_io"
    memory = "memory"
    handoff = "handoff"
    chain = "chain"
    retrieval = "retrieval"
    custom = "custom"


class IOType(str, Enum):
    prompt = "prompt"
    response = "response"
    tool_input = "tool_input"
    tool_output = "tool_output"
    file_read = "file_read"
    file_write = "file_write"
    memory_read = "memory_read"
    memory_write = "memory_write"


class EdgeKind(str, Enum):
    call = "call"
    handoff = "handoff"
    data_flow = "data_flow"
    mcp_link = "mcp_link"
    file_dep = "file_dep"
    memory_dep = "memory_dep"


class SessionInfo(BaseModel):
    external_id: str
    title: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: str = "completed"
    meta: dict = Field(default_factory=dict)


class AgentInfo(BaseModel):
    external_id: str
    name: str
    role: str | None = None
    model: str | None = None
    meta: dict = Field(default_factory=dict)


class McpServerInfo(BaseModel):
    external_id: str
    name: str
    transport: str | None = None
    url: str | None = None
    tools: list[str] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class IORecord(BaseModel):
    io_type: IOType
    role: str | None = None
    content_text: str | None = None
    file_path: str | None = None
    byte_size: int | None = None
    meta: dict = Field(default_factory=dict)


class CostRecord(BaseModel):
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    # If set, used verbatim; otherwise computed from the model price table.
    cost_usd: float | None = None


class ErrorInfo(BaseModel):
    error_type: str | None = None
    message: str | None = None
    stack: str | None = None
    meta: dict = Field(default_factory=dict)


class SpanInput(BaseModel):
    external_span_id: str
    parent_external_span_id: str | None = None
    kind: SpanKind
    name: str
    agent_external_id: str | None = None
    mcp_server_external_id: str | None = None
    status: str = "ok"
    start_time: datetime | None = None
    end_time: datetime | None = None
    attributes: dict = Field(default_factory=dict)
    io: list[IORecord] = Field(default_factory=list)
    cost: CostRecord | None = None
    error: ErrorInfo | None = None


class EdgeInput(BaseModel):
    source_external_span_id: str
    target_external_span_id: str
    kind: EdgeKind = EdgeKind.call
    label: str | None = None
    meta: dict = Field(default_factory=dict)


class CanonicalEnvelope(BaseModel):
    """A complete (or appended) trace, normalized across frameworks."""

    schema_version: str = SCHEMA_VERSION
    source: Source
    session: SessionInfo
    agents: list[AgentInfo] = Field(default_factory=list)
    mcp_servers: list[McpServerInfo] = Field(default_factory=list)
    spans: list[SpanInput] = Field(default_factory=list)
    edges: list[EdgeInput] = Field(default_factory=list)
