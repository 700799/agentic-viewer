"""Run comparison — align two sessions by span signature and diff cost/latency."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db.models import Cost, Session, Span
from app.schemas.api import (
    AlignedSpan,
    CompareCostByAgent,
    CompareReport,
    CompareSummary,
)
from app.services.cost_aggregator import build_cost_report


def _signature(sp: Span) -> str:
    """A structural key independent of run-specific UUIDs: kind + depth + name."""
    return f"{sp.span_kind}:{sp.depth}:{sp.name}"


def _span_index(db: DbSession, session_id: uuid.UUID) -> dict[str, Span]:
    out: dict[str, Span] = {}
    for sp in db.scalars(select(Span).where(Span.session_id == session_id).order_by(Span.sequence)):
        sig = _signature(sp)
        # keep first occurrence of a signature
        out.setdefault(sig, sp)
    return out


def compare(db: DbSession, a_id: uuid.UUID, b_id: uuid.UUID) -> CompareReport | None:
    a_sess = db.get(Session, a_id)
    b_sess = db.get(Session, b_id)
    if a_sess is None or b_sess is None:
        return None

    a_spans = _span_index(db, a_id)
    b_spans = _span_index(db, b_id)
    a_costs = {c.span_id: c for c in db.scalars(select(Cost).where(Cost.session_id == a_id))}
    b_costs = {c.span_id: c for c in db.scalars(select(Cost).where(Cost.session_id == b_id))}

    aligned: list[AlignedSpan] = []
    for sig in sorted(set(a_spans) | set(b_spans)):
        a_sp = a_spans.get(sig)
        b_sp = b_spans.get(sig)
        if a_sp and not b_sp:
            status = "removed"
        elif b_sp and not a_sp:
            status = "added"
        else:
            status = "same"
            if a_sp.duration_ms != b_sp.duration_ms or a_sp.status != b_sp.status:
                status = "changed"
        aligned.append(
            AlignedSpan(
                signature=sig,
                status=status,
                a_cost_usd=float(a_costs[a_sp.id].cost_usd) if a_sp and a_sp.id in a_costs else None,
                b_cost_usd=float(b_costs[b_sp.id].cost_usd) if b_sp and b_sp.id in b_costs else None,
                a_duration_ms=a_sp.duration_ms if a_sp else None,
                b_duration_ms=b_sp.duration_ms if b_sp else None,
            )
        )

    a_cost = build_cost_report(db, a_id)
    b_cost = build_cost_report(db, b_id)
    b_by_name = {x.name: x.cost_usd for x in b_cost.per_agent}
    a_by_name = {x.name: x.cost_usd for x in a_cost.per_agent}
    cost_by_agent = [
        CompareCostByAgent(
            name=name,
            a_usd=a_by_name.get(name, 0.0),
            b_usd=b_by_name.get(name, 0.0),
            delta_usd=round(b_by_name.get(name, 0.0) - a_by_name.get(name, 0.0), 6),
        )
        for name in sorted(set(a_by_name) | set(b_by_name))
    ]

    summary = CompareSummary(
        cost_delta_usd=round(float(b_sess.total_cost_usd) - float(a_sess.total_cost_usd), 6),
        duration_delta_ms=_total_duration(b_spans) - _total_duration(a_spans),
        span_count_delta=b_sess.span_count - a_sess.span_count,
    )
    return CompareReport(summary=summary, aligned_spans=aligned, cost_by_agent=cost_by_agent)


def _total_duration(spans: dict[str, Span]) -> int:
    return sum((sp.duration_ms or 0) for sp in spans.values())
