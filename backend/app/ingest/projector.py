"""Projector — turns a Canonical Trace Envelope into queryable rows.

This is the only writer of the projected tables. It is idempotent on
``(session_id, external_span_id)``: re-ingesting the same envelope updates rows rather
than duplicating them, which makes streaming/append and re-projection safe.

Steps:
1. Upsert the session (keyed on source + external_id).
2. Upsert agents and MCP servers, building external_id -> internal UUID maps.
3. Insert/replace spans; resolve parent refs in a second pass.
4. Attach IO, cost (computed from prices), and errors.
5. Compute sequence (global order) and depth (tree level).
6. Insert explicit edges.
7. Recompute denormalized session rollups.
8. Store the raw envelope for re-projection.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.db.models import (
    Agent,
    Cost,
    Edge,
    ErrorRecord,
    McpServer,
    RawTrace,
    Session,
    Span,
    SpanIO,
)
from app.ingest.pricing import compute_cost, seed_prices
from app.schemas.canonical import CanonicalEnvelope, SpanInput


def _truncate(text: str | None) -> tuple[str | None, bool]:
    if text is None:
        return None, False
    limit = settings.max_inline_content_chars
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def _duration_ms(start: datetime | None, end: datetime | None) -> int | None:
    if start and end:
        return max(0, int((end - start).total_seconds() * 1000))
    return None


def ingest_envelope(db: DbSession, envelope: CanonicalEnvelope) -> tuple[uuid.UUID, int, int]:
    """Project an envelope. Returns (session_id, spans_ingested, edges_ingested)."""
    seed_prices(db)

    session = _upsert_session(db, envelope)
    db.flush()

    # Wipe prior projection for this session so re-ingest is a clean replace.
    db.execute(delete(Edge).where(Edge.session_id == session.id))
    db.execute(delete(Span).where(Span.session_id == session.id))
    db.flush()

    agent_map = _upsert_agents(db, session, envelope)
    mcp_map = _upsert_mcp_servers(db, session, envelope)
    db.flush()

    ext_to_uuid = _insert_spans(db, session, envelope, agent_map, mcp_map)
    edges_ingested = _insert_edges(db, session, envelope, ext_to_uuid)

    _recompute_rollups(db, session)

    db.add(
        RawTrace(
            session_id=session.id,
            source=envelope.source.value,
            schema_version=envelope.schema_version,
            payload=envelope.model_dump(mode="json"),
        )
    )

    db.commit()
    return session.id, len(envelope.spans), edges_ingested


def _upsert_session(db: DbSession, envelope: CanonicalEnvelope) -> Session:
    info = envelope.session
    stmt = select(Session).where(
        Session.source == envelope.source.value,
        Session.external_id == info.external_id,
    )
    session = db.scalars(stmt).first()
    if session is None:
        session = Session(source=envelope.source.value, external_id=info.external_id)
        db.add(session)
    session.title = info.title
    session.status = info.status
    session.started_at = info.started_at
    session.ended_at = info.ended_at
    session.meta = info.meta
    return session


def _upsert_agents(
    db: DbSession, session: Session, envelope: CanonicalEnvelope
) -> dict[str, uuid.UUID]:
    existing = {a.name: a for a in db.scalars(select(Agent).where(Agent.session_id == session.id))}
    out: dict[str, uuid.UUID] = {}
    for info in envelope.agents:
        agent = existing.get(info.name)
        if agent is None:
            agent = Agent(session_id=session.id, name=info.name)
            db.add(agent)
        agent.external_id = info.external_id
        agent.role = info.role
        agent.model = info.model
        agent.meta = info.meta
        db.flush()
        out[info.external_id] = agent.id
    return out


def _upsert_mcp_servers(
    db: DbSession, session: Session, envelope: CanonicalEnvelope
) -> dict[str, uuid.UUID]:
    existing = {
        m.name: m for m in db.scalars(select(McpServer).where(McpServer.session_id == session.id))
    }
    out: dict[str, uuid.UUID] = {}
    for info in envelope.mcp_servers:
        server = existing.get(info.name)
        if server is None:
            server = McpServer(session_id=session.id, name=info.name)
            db.add(server)
        server.external_id = info.external_id
        server.transport = info.transport
        server.url = info.url
        server.tools = info.tools
        server.meta = info.meta
        db.flush()
        out[info.external_id] = server.id
    return out


def _order_spans(spans: list[SpanInput]) -> list[SpanInput]:
    """Stable order: by start_time when present, else original order."""
    _far_future = datetime.max.replace(tzinfo=timezone.utc)

    def _key(start: datetime | None) -> datetime:
        if start is None:
            return _far_future
        # Normalize naive datetimes to UTC so all keys are comparable.
        return start if start.tzinfo else start.replace(tzinfo=timezone.utc)

    indexed = list(enumerate(spans))
    indexed.sort(key=lambda pair: (_key(pair[1].start_time), pair[0]))
    return [s for _, s in indexed]


def _insert_spans(
    db: DbSession,
    session: Session,
    envelope: CanonicalEnvelope,
    agent_map: dict[str, uuid.UUID],
    mcp_map: dict[str, uuid.UUID],
) -> dict[str, uuid.UUID]:
    ordered = _order_spans(envelope.spans)
    ext_to_uuid: dict[str, uuid.UUID] = {}

    # First pass: create span rows and IO/cost/error, assign sequence.
    for seq, sp in enumerate(ordered):
        span = Span(
            session_id=session.id,
            external_span_id=sp.external_span_id,
            span_kind=sp.kind.value,
            name=sp.name,
            agent_id=agent_map.get(sp.agent_external_id) if sp.agent_external_id else None,
            mcp_server_id=(
                mcp_map.get(sp.mcp_server_external_id) if sp.mcp_server_external_id else None
            ),
            status=sp.status,
            start_time=sp.start_time,
            end_time=sp.end_time,
            duration_ms=_duration_ms(sp.start_time, sp.end_time),
            sequence=seq,
            attributes=sp.attributes,
        )
        db.add(span)
        db.flush()
        ext_to_uuid[sp.external_span_id] = span.id

        for rec in sp.io:
            content, truncated = _truncate(rec.content_text)
            db.add(
                SpanIO(
                    span_id=span.id,
                    io_type=rec.io_type.value,
                    role=rec.role,
                    content_text=content,
                    truncated=truncated,
                    file_path=rec.file_path,
                    byte_size=rec.byte_size,
                    meta=rec.meta,
                )
            )

        if sp.cost is not None:
            cost_usd, estimated = compute_cost(db, sp.cost)
            db.add(
                Cost(
                    span_id=span.id,
                    session_id=session.id,
                    agent_id=span.agent_id,
                    model=sp.cost.model,
                    input_tokens=sp.cost.input_tokens,
                    output_tokens=sp.cost.output_tokens,
                    cache_read_tokens=sp.cost.cache_read_tokens,
                    cache_write_tokens=sp.cost.cache_write_tokens,
                    cost_usd=cost_usd,
                    estimated=estimated,
                )
            )

        if sp.error is not None:
            db.add(
                ErrorRecord(
                    span_id=span.id,
                    session_id=session.id,
                    error_type=sp.error.error_type,
                    message=sp.error.message,
                    stack=sp.error.stack,
                    meta=sp.error.meta,
                )
            )

    db.flush()

    # Second pass: resolve parent refs (now all spans exist) and compute depth.
    parent_of: dict[str, str | None] = {
        sp.external_span_id: sp.parent_external_span_id for sp in ordered
    }
    for sp in ordered:
        parent_ext = sp.parent_external_span_id
        if parent_ext and parent_ext in ext_to_uuid:
            span = db.get(Span, ext_to_uuid[sp.external_span_id])
            span.parent_span_id = ext_to_uuid[parent_ext]
            span.depth = _depth(sp.external_span_id, parent_of)
    db.flush()
    return ext_to_uuid


def _depth(ext_id: str, parent_of: dict[str, str | None], _guard: int = 0) -> int:
    parent = parent_of.get(ext_id)
    if parent is None or _guard > 1000:
        return 0
    return 1 + _depth(parent, parent_of, _guard + 1)


def _insert_edges(
    db: DbSession,
    session: Session,
    envelope: CanonicalEnvelope,
    ext_to_uuid: dict[str, uuid.UUID],
) -> int:
    count = 0
    for e in envelope.edges:
        src = ext_to_uuid.get(e.source_external_span_id)
        tgt = ext_to_uuid.get(e.target_external_span_id)
        if src is None or tgt is None:
            continue
        db.add(
            Edge(
                session_id=session.id,
                source_span_id=src,
                target_span_id=tgt,
                edge_kind=e.kind.value,
                label=e.label,
                meta=e.meta,
            )
        )
        count += 1
    db.flush()
    return count


def _recompute_rollups(db: DbSession, session: Session) -> None:
    costs = list(db.scalars(select(Cost).where(Cost.session_id == session.id)))
    session.total_cost_usd = sum((c.cost_usd for c in costs), start=0)
    session.total_input_tokens = sum(c.input_tokens for c in costs)
    session.total_output_tokens = sum(c.output_tokens for c in costs)
    session.span_count = db.query(Span).filter(Span.session_id == session.id).count()
    db.flush()
