"""Projector tests: round-trip ingest, idempotency, cost computation, rollups."""

from __future__ import annotations

from pathlib import Path

from app.adapters.claude_code import parse_jsonl
from app.db.models import Cost, Edge, Span
from app.ingest.projector import ingest_envelope

SAMPLE = Path(__file__).resolve().parents[1] / "app" / "seed" / "sample_claude_code.jsonl"


def test_ingest_creates_spans_and_edges(db):
    env = parse_jsonl(SAMPLE)
    session_id, spans, edges = ingest_envelope(db, env)
    assert spans == len(env.spans)
    assert db.query(Span).filter(Span.session_id == session_id).count() == spans
    assert edges > 0


def test_ingest_is_idempotent(db):
    env = parse_jsonl(SAMPLE)
    sid1, spans1, _ = ingest_envelope(db, env)
    sid2, spans2, _ = ingest_envelope(db, env)
    assert sid1 == sid2  # same source+external_id -> same session
    assert spans1 == spans2
    # No duplicate spans after a second ingest.
    assert db.query(Span).filter(Span.session_id == sid1).count() == spans1


def test_cost_computed_from_price_table(db):
    env = parse_jsonl(SAMPLE)
    sid, _, _ = ingest_envelope(db, env)
    costs = db.query(Cost).filter(Cost.session_id == sid).all()
    assert costs
    assert all(not c.estimated for c in costs)  # claude-opus-4-8 is in the seed prices
    assert sum(float(c.cost_usd) for c in costs) > 0


def test_rollups_match_cost_rows(db):
    from app.db.models import Session as Sess

    env = parse_jsonl(SAMPLE)
    sid, _, _ = ingest_envelope(db, env)
    session = db.get(Sess, sid)
    total = sum(float(c.cost_usd) for c in db.query(Cost).filter(Cost.session_id == sid))
    assert abs(float(session.total_cost_usd) - total) < 1e-6
    assert session.span_count == db.query(Span).filter(Span.session_id == sid).count()


def test_parent_child_and_depth_resolved(db):
    env = parse_jsonl(SAMPLE)
    sid, _, _ = ingest_envelope(db, env)
    spans = db.query(Span).filter(Span.session_id == sid).all()
    # Root has depth 0; at least one child has depth >= 1.
    assert any(s.depth == 0 for s in spans)
    assert any(s.depth >= 1 for s in spans)
    assert any(s.parent_span_id is not None for s in spans)


def test_edges_reference_existing_spans(db):
    env = parse_jsonl(SAMPLE)
    sid, _, _ = ingest_envelope(db, env)
    span_ids = {s.id for s in db.query(Span).filter(Span.session_id == sid)}
    for e in db.query(Edge).filter(Edge.session_id == sid):
        assert e.source_span_id in span_ids
        assert e.target_span_id in span_ids
