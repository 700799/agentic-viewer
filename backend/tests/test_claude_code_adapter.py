"""Contract test: the Claude Code adapter maps a transcript onto the canonical model."""

from __future__ import annotations

from pathlib import Path

from app.adapters.claude_code import build_envelope, parse_jsonl
from app.schemas.canonical import SpanKind

SAMPLE = Path(__file__).resolve().parents[1] / "app" / "seed" / "sample_claude_code.jsonl"


def test_parses_sample_into_canonical_envelope():
    env = parse_jsonl(SAMPLE)
    assert env.source.value == "claude_code"
    assert env.session.external_id == "demo-refactor-auth"
    assert env.session.title.startswith("Refactor the auth module")

    kinds = [s.kind for s in env.spans]
    assert SpanKind.session_root in kinds
    assert SpanKind.llm in kinds
    assert SpanKind.tool in kinds
    assert SpanKind.mcp_tool in kinds  # mcp__library-docs__lookup
    assert SpanKind.agent in kinds  # Task -> subagent


def test_mcp_server_extracted_from_tool_prefix():
    env = parse_jsonl(SAMPLE)
    names = {m.name for m in env.mcp_servers}
    assert "library-docs" in names


def test_file_io_recorded_for_read_and_write():
    env = parse_jsonl(SAMPLE)
    io_types = {io.io_type.value for sp in env.spans for io in sp.io}
    assert "file_read" in io_types
    assert "file_write" in io_types


def test_usage_mapped_to_cost():
    env = parse_jsonl(SAMPLE)
    llm_spans = [s for s in env.spans if s.kind == SpanKind.llm]
    assert llm_spans and all(s.cost is not None for s in llm_spans)
    assert llm_spans[0].cost.input_tokens > 0


def test_tool_result_attached_as_output():
    env = parse_jsonl(SAMPLE)
    outputs = [io for sp in env.spans for io in sp.io if io.io_type.value == "tool_output"]
    assert outputs, "expected tool_result blocks to produce tool_output IO"


def test_build_envelope_handles_empty():
    env = build_envelope([], default_external_id="empty")
    assert env.session.external_id == "empty"
    # Always has at least the root span.
    assert any(s.kind == SpanKind.session_root for s in env.spans)
