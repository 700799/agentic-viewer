"""Service-layer tests: graph builder, cost aggregator, timeline, mermaid, compare."""

from __future__ import annotations

from pathlib import Path

from app.adapters.claude_code import parse_jsonl
from app.ingest.projector import ingest_envelope
from app.services.comparator import compare
from app.services.cost_aggregator import build_cost_report
from app.services.graph_builder import build_graph
from app.services.mermaid import generate
from app.services.timeline import build_timeline

SAMPLE = Path(__file__).resolve().parents[1] / "app" / "seed" / "sample_claude_code.jsonl"


def _ingest(db):
    return ingest_envelope(db, parse_jsonl(SAMPLE))[0]


def test_graph_has_expected_node_types(db):
    sid = _ingest(db)
    graph = build_graph(db, sid)
    types = {n.type for n in graph.nodes}
    assert {"agent", "llm", "tool", "mcpTool", "mcpServer", "file"} <= types
    assert graph.edges
    assert graph.groups  # at least the main agent group


def test_cost_report_totals_and_breakdowns(db):
    sid = _ingest(db)
    report = build_cost_report(db, sid)
    assert report.total.cost_usd > 0
    assert report.per_model
    assert report.per_step
    # Cumulative timeline is monotonically non-decreasing.
    cumulative = [p.cumulative_cost_usd for p in report.timeline]
    assert cumulative == sorted(cumulative)


def test_timeline_ordered_by_sequence(db):
    sid = _ingest(db)
    tl = build_timeline(db, sid)
    seqs = [e.sequence for e in tl.items]
    assert seqs == sorted(seqs)
    assert any(e.preview.tool_output for e in tl.items)


def test_mermaid_diagrams_render(db):
    sid = _ingest(db)
    assert generate(db, sid, "flowchart").startswith("flowchart")
    assert generate(db, sid, "sequence").startswith("sequenceDiagram")
    assert generate(db, sid, "dependency").startswith("graph LR")
    assert "subgraph" in generate(db, sid, "architecture")


def test_compare_same_session_has_zero_deltas(db):
    sid = _ingest(db)
    report = compare(db, sid, sid)
    assert report is not None
    assert report.summary.cost_delta_usd == 0
    assert report.summary.span_count_delta == 0
    assert all(s.status in ("same", "changed") for s in report.aligned_spans)
