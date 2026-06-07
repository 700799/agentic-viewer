"""SQLAlchemy ORM models for Agent Canvas.

The schema spine is the ``span`` table (OpenTelemetry-GenAI inspired): every agent,
LLM call, tool call, file I/O and memory op is a span discriminated by ``span_kind``.
Dimension tables (agent, mcp_server) and side tables (span_io, cost, error, edge) hang
off it. ``raw_trace`` keeps the original envelope so projected tables can be rebuilt.

All entities are exported here so ``from app.db.models import Session, Span`` works and
Alembic autogenerate sees them via ``app.db.models``.
"""

from app.db.models.entities import (
    Agent,
    Cost,
    Edge,
    ErrorRecord,
    McpServer,
    ModelPrice,
    RawTrace,
    Session,
    Span,
    SpanIO,
)

__all__ = [
    "Agent",
    "Cost",
    "Edge",
    "ErrorRecord",
    "McpServer",
    "ModelPrice",
    "RawTrace",
    "Session",
    "Span",
    "SpanIO",
]
