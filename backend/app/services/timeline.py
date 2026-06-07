"""Timeline view — ordered events with truncated previews, plus full span detail."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db.models import Agent, Cost, Span
from app.schemas.api import (
    SpanDetail,
    SpanIODetail,
    TimelineCost,
    TimelineEvent,
    TimelinePreview,
    TimelineResponse,
)

_PREVIEW_CHARS = 280


def _clip(text: str | None) -> str | None:
    if text is None:
        return None
    return text if len(text) <= _PREVIEW_CHARS else text[:_PREVIEW_CHARS] + "…"


def build_timeline(
    db: DbSession, session_id: uuid.UUID, from_seq: int = 0, limit: int = 1000
) -> TimelineResponse:
    spans = list(
        db.scalars(
            select(Span)
            .where(Span.session_id == session_id, Span.sequence >= from_seq)
            .order_by(Span.sequence)
            .limit(limit)
        )
    )
    agents = {a.id: a.name for a in db.scalars(select(Agent).where(Agent.session_id == session_id))}
    costs = {c.span_id: c for c in db.scalars(select(Cost).where(Cost.session_id == session_id))}

    items: list[TimelineEvent] = []
    for sp in spans:
        preview = TimelinePreview()
        for io in sp.io:
            if io.io_type == "prompt":
                preview.prompt = _clip(io.content_text)
            elif io.io_type == "response":
                preview.response = _clip(io.content_text)
            elif io.io_type == "tool_input":
                preview.tool_input = _clip(io.content_text)
            elif io.io_type == "tool_output":
                preview.tool_output = _clip(io.content_text)
        if sp.error:
            preview.error = _clip(sp.error.message)

        cost = costs.get(sp.id)
        items.append(
            TimelineEvent(
                span_id=sp.id,
                sequence=sp.sequence,
                kind=sp.span_kind,
                name=sp.name,
                agent_name=agents.get(sp.agent_id) if sp.agent_id else None,
                start_time=sp.start_time,
                end_time=sp.end_time,
                duration_ms=sp.duration_ms,
                status=sp.status,
                preview=preview,
                cost=(
                    TimelineCost(
                        input_tokens=cost.input_tokens,
                        output_tokens=cost.output_tokens,
                        cost_usd=float(cost.cost_usd),
                    )
                    if cost
                    else None
                ),
            )
        )
    return TimelineResponse(items=items)


def build_span_detail(db: DbSession, span_id: uuid.UUID) -> SpanDetail | None:
    sp = db.get(Span, span_id)
    if sp is None:
        return None
    agent_name = None
    if sp.agent_id:
        a = db.get(Agent, sp.agent_id)
        agent_name = a.name if a else None

    cost = sp.cost
    return SpanDetail(
        id=sp.id,
        external_span_id=sp.external_span_id,
        kind=sp.span_kind,
        name=sp.name,
        agent_name=agent_name,
        status=sp.status,
        start_time=sp.start_time,
        end_time=sp.end_time,
        duration_ms=sp.duration_ms,
        attributes=sp.attributes or {},
        io=[
            SpanIODetail(
                io_type=io.io_type,
                role=io.role,
                content_text=io.content_text,
                file_path=io.file_path,
                byte_size=io.byte_size,
                truncated=io.truncated,
            )
            for io in sp.io
        ],
        cost=(
            TimelineCost(
                input_tokens=cost.input_tokens,
                output_tokens=cost.output_tokens,
                cost_usd=float(cost.cost_usd),
            )
            if cost
            else None
        ),
        error=sp.error.message if sp.error else None,
    )
