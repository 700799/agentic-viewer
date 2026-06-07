"""Concrete ORM table definitions.

Type portability notes:
- ``Uuid`` → native UUID on Postgres, CHAR(32) on SQLite.
- ``JSON`` → JSONB on Postgres, JSON-as-text on SQLite.
- ``Numeric`` for money; ``DateTime(timezone=True)`` for timestamps.
Query-critical attributes are real columns (kind, agent_id, cost columns, file_path);
``JSON`` is reserved for non-queried metadata to keep SQLite↔Postgres parity.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Session(Base):
    __tablename__ = "session"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str] = mapped_column(String(32), index=True)  # claude_code, openai_agents, ...
    title: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="completed")  # running/completed/error
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Denormalized rollups for fast session-list rendering.
    total_cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    span_count: Mapped[int] = mapped_column(Integer, default=0)

    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    spans: Mapped[list["Span"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_session_source_external"),
        Index("ix_session_started_at", "started_at"),
    )


class Agent(Base):
    __tablename__ = "agent"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("session.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("session_id", "name", name="uq_agent_session_name"),
    )


class McpServer(Base):
    __tablename__ = "mcp_server"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("session.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    transport: Mapped[str | None] = mapped_column(String(32))  # stdio/http/sse
    url: Mapped[str | None] = mapped_column(String(512))
    tools: Mapped[list] = mapped_column(JSON, default=list)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("session_id", "name", name="uq_mcp_session_name"),
    )


class Span(Base):
    """The spine of the model — one row per unit of work in a run."""

    __tablename__ = "span"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("session.id", ondelete="CASCADE"), index=True
    )
    external_span_id: Mapped[str] = mapped_column(String(255))
    parent_span_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("span.id", ondelete="CASCADE"), index=True
    )

    span_kind: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(512))

    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agent.id", ondelete="SET NULL"), index=True
    )
    mcp_server_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("mcp_server.id", ondelete="SET NULL")
    )

    status: Mapped[str] = mapped_column(String(16), default="ok")  # ok/error
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    sequence: Mapped[int] = mapped_column(Integer, default=0)  # global order within session
    depth: Mapped[int] = mapped_column(Integer, default=0)  # tree depth (precomputed)

    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    session: Mapped["Session"] = relationship(back_populates="spans")
    io: Mapped[list["SpanIO"]] = relationship(
        back_populates="span", cascade="all, delete-orphan"
    )
    cost: Mapped["Cost | None"] = relationship(
        back_populates="span", cascade="all, delete-orphan", uselist=False
    )
    error: Mapped["ErrorRecord | None"] = relationship(
        back_populates="span", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("session_id", "external_span_id", name="uq_span_session_external"),
        Index("ix_span_session_sequence", "session_id", "sequence"),
        Index("ix_span_session_kind", "session_id", "span_kind"),
    )


class SpanIO(Base):
    """Prompts, responses, tool inputs/outputs, file reads/writes, memory ops."""

    __tablename__ = "span_io"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    span_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("span.id", ondelete="CASCADE"), index=True
    )
    io_type: Mapped[str] = mapped_column(String(32))  # prompt/response/tool_input/...
    role: Mapped[str | None] = mapped_column(String(32))  # system/user/assistant/tool
    content_text: Mapped[str | None] = mapped_column(Text)
    content_ref: Mapped[str | None] = mapped_column(String(512))  # object-store key (V1)
    file_path: Mapped[str | None] = mapped_column(String(1024), index=True)
    byte_size: Mapped[int | None] = mapped_column(Integer)
    truncated: Mapped[bool] = mapped_column(default=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    span: Mapped["Span"] = relationship(back_populates="io")

    __table_args__ = (Index("ix_span_io_span_type", "span_id", "io_type"),)


class Cost(Base):
    __tablename__ = "cost"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    span_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("span.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("session.id", ondelete="CASCADE"), index=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agent.id", ondelete="SET NULL"), index=True
    )
    model: Mapped[str | None] = mapped_column(String(128), index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
    estimated: Mapped[bool] = mapped_column(default=False)  # true if price was unknown

    span: Mapped["Span"] = relationship(back_populates="cost")


class ErrorRecord(Base):
    __tablename__ = "error"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    span_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("span.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("session.id", ondelete="CASCADE"), index=True
    )
    error_type: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(Text)
    stack: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    span: Mapped["Span"] = relationship(back_populates="error")


class Edge(Base):
    """Explicit DAG relationships beyond span parent/child (handoff, data flow, ...)."""

    __tablename__ = "edge"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("session.id", ondelete="CASCADE"), index=True
    )
    source_span_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("span.id", ondelete="CASCADE"), index=True
    )
    target_span_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("span.id", ondelete="CASCADE"), index=True
    )
    edge_kind: Mapped[str] = mapped_column(String(32))  # call/handoff/data_flow/mcp_link/...
    label: Mapped[str | None] = mapped_column(String(255))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (Index("ix_edge_session_kind", "session_id", "edge_kind"),)


class RawTrace(Base):
    """Append-only store of the original ingestion envelope, for re-projection."""

    __tablename__ = "raw_trace"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("session.id", ondelete="CASCADE")
    )
    source: Mapped[str] = mapped_column(String(32))
    schema_version: Mapped[str] = mapped_column(String(16))
    payload: Mapped[dict] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ModelPrice(Base):
    """Reference price table; cost is computed at ingest from this."""

    __tablename__ = "model_price"

    model: Mapped[str] = mapped_column(String(128), primary_key=True)
    input_per_mtok: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
    output_per_mtok: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
    cache_read_per_mtok: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
    cache_write_per_mtok: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
