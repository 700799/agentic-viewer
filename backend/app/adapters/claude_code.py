"""Claude Code adapter — session JSONL transcript -> Canonical Trace Envelope.

Claude Code writes one JSON object per line to
``~/.claude/projects/<project>/<session-uuid>.jsonl``. Each object is roughly::

    {"type": "user"|"assistant", "uuid": ..., "parentUuid": ..., "timestamp": ...,
     "sessionId": ..., "cwd": ...,
     "message": {"role": ..., "model": ..., "usage": {...},
                 "content": [ {"type": "text"|"tool_use"|"tool_result", ...} ]}}

Mapping to the canonical model:
- the run               -> session + a ``session_root`` span (the main agent)
- each assistant turn   -> ``llm`` span carrying token ``usage`` -> cost
- each ``tool_use``     -> ``tool`` span (or ``mcp_tool`` if name is ``mcp__srv__tool``)
- matching ``tool_result`` -> the tool span's ``tool_output`` IO + end_time/status
- Read/Write/Edit tools -> ``file_read`` / ``file_write`` IO with file_path
- the ``Task`` tool     -> a child ``agent`` (subagent) span

This adapter is intentionally defensive: real transcripts vary across versions, so every
field access tolerates absence. Unknown shapes degrade to a ``custom`` span rather than
failing the whole ingest.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dateutil import parser as dateparser

from app.schemas.canonical import (
    AgentInfo,
    CanonicalEnvelope,
    CostRecord,
    EdgeInput,
    EdgeKind,
    ErrorInfo,
    IORecord,
    IOType,
    McpServerInfo,
    SessionInfo,
    Source,
    SpanInput,
    SpanKind,
)

FILE_READ_TOOLS = {"Read", "NotebookRead"}
FILE_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
MAIN_AGENT_EXT = "agent:main"


def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = dateparser.parse(value) if isinstance(value, str) else None
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _mcp_server_from_tool(tool_name: str) -> str | None:
    """``mcp__filesystem__read_file`` -> ``filesystem``; else None."""
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        if len(parts) >= 3:
            return parts[1]
    return None


def _short_json(obj: Any, limit: int = 4000) -> str:
    try:
        text = json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError):
        text = str(obj)
    return text[:limit]


def parse_jsonl(path: str | Path) -> CanonicalEnvelope:
    """Read a Claude Code JSONL file and return a canonical envelope."""
    path = Path(path)
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return build_envelope(records, default_external_id=path.stem)


def build_envelope(records: list[dict], default_external_id: str = "session") -> CanonicalEnvelope:
    spans: list[SpanInput] = []
    edges: list[EdgeInput] = []
    mcp_servers: dict[str, McpServerInfo] = {}
    agents: dict[str, AgentInfo] = {MAIN_AGENT_EXT: AgentInfo(external_id=MAIN_AGENT_EXT, name="main", role="orchestrator")}

    session_external_id = default_external_id
    session_title: str | None = None
    session_model: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None

    # Map tool_use id -> external span id, so a later tool_result attaches to it.
    tooluse_to_span: dict[str, str] = {}
    first_user_text: str | None = None

    # Root span representing the main agent / overall run.
    root_ext = "span:root"
    spans.append(
        SpanInput(
            external_span_id=root_ext,
            kind=SpanKind.session_root,
            name="main",
            agent_external_id=MAIN_AGENT_EXT,
        )
    )

    counter = 0

    def next_id(prefix: str) -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}:{counter}"

    for rec in records:
        rec_type = rec.get("type")
        msg = rec.get("message") or {}
        ts = _parse_ts(rec.get("timestamp"))
        if ts:
            started_at = ts if started_at is None else started_at
            ended_at = ts if ended_at is None or ts > ended_at else ended_at
        if rec.get("sessionId"):
            session_external_id = rec["sessionId"]

        content = msg.get("content")

        if rec_type == "user":
            text = _extract_user_text(content)
            if text and first_user_text is None:
                first_user_text = text
                session_title = text[:80]
            _attach_tool_results(content, tooluse_to_span, spans, ts)

        elif rec_type == "assistant":
            model = msg.get("model")
            if model:
                session_model = model
            usage = msg.get("usage") or {}
            llm_ext = next_id("span:llm")
            assistant_text = _extract_assistant_text(content)
            io: list[IORecord] = []
            if first_user_text and not any(s.kind == SpanKind.llm for s in spans):
                io.append(IORecord(io_type=IOType.prompt, role="user", content_text=first_user_text))
            if assistant_text:
                io.append(
                    IORecord(io_type=IOType.response, role="assistant", content_text=assistant_text)
                )
            spans.append(
                SpanInput(
                    external_span_id=llm_ext,
                    parent_external_span_id=root_ext,
                    kind=SpanKind.llm,
                    name=model or "assistant",
                    agent_external_id=MAIN_AGENT_EXT,
                    start_time=ts,
                    end_time=ts,
                    attributes={"gen_ai.system": "anthropic", "model": model},
                    io=io,
                    cost=_usage_to_cost(model, usage),
                )
            )
            edges.append(
                EdgeInput(source_external_span_id=root_ext, target_external_span_id=llm_ext, kind=EdgeKind.call)
            )

            # Each tool_use block becomes a tool/mcp_tool/agent child span.
            for block in _blocks(content):
                if block.get("type") != "tool_use":
                    continue
                tool_name = block.get("name", "tool")
                tool_input = block.get("input") or {}
                tool_use_id = block.get("id") or next_id("tu")
                server = _mcp_server_from_tool(tool_name)

                if server:
                    mcp_servers.setdefault(
                        server,
                        McpServerInfo(external_id=f"mcp:{server}", name=server, transport="stdio"),
                    )

                # The Task tool spawns a subagent.
                if tool_name == "Task":
                    sub_name = tool_input.get("subagent_type") or tool_input.get("description") or "subagent"
                    sub_agent_ext = f"agent:{sub_name}:{counter}"
                    agents.setdefault(
                        sub_agent_ext,
                        AgentInfo(external_id=sub_agent_ext, name=str(sub_name), role="subagent"),
                    )
                    span_ext = next_id("span:agent")
                    spans.append(
                        SpanInput(
                            external_span_id=span_ext,
                            parent_external_span_id=llm_ext,
                            kind=SpanKind.agent,
                            name=str(sub_name),
                            agent_external_id=sub_agent_ext,
                            start_time=ts,
                            io=[IORecord(io_type=IOType.prompt, content_text=_short_json(tool_input))],
                        )
                    )
                    edges.append(
                        EdgeInput(source_external_span_id=llm_ext, target_external_span_id=span_ext, kind=EdgeKind.handoff)
                    )
                    tooluse_to_span[tool_use_id] = span_ext
                    continue

                kind = SpanKind.mcp_tool if server else SpanKind.tool
                span_ext = next_id("span:tool")
                io = [IORecord(io_type=IOType.tool_input, content_text=_short_json(tool_input))]
                _maybe_file_io(tool_name, tool_input, io)
                spans.append(
                    SpanInput(
                        external_span_id=span_ext,
                        parent_external_span_id=llm_ext,
                        kind=kind,
                        name=tool_name,
                        agent_external_id=MAIN_AGENT_EXT,
                        mcp_server_external_id=f"mcp:{server}" if server else None,
                        start_time=ts,
                        attributes={"tool": tool_name},
                        io=io,
                    )
                )
                edges.append(
                    EdgeInput(source_external_span_id=llm_ext, target_external_span_id=span_ext, kind=EdgeKind.call)
                )
                if server:
                    edges.append(
                        EdgeInput(
                            source_external_span_id=span_ext,
                            target_external_span_id=span_ext,
                            kind=EdgeKind.mcp_link,
                            label=server,
                        )
                    )
                tooluse_to_span[tool_use_id] = span_ext

    session = SessionInfo(
        external_id=session_external_id,
        title=session_title or "Claude Code session",
        started_at=started_at,
        ended_at=ended_at,
        status="completed",
        meta={"model": session_model} if session_model else {},
    )

    return CanonicalEnvelope(
        source=Source.claude_code,
        session=session,
        agents=list(agents.values()),
        mcp_servers=list(mcp_servers.values()),
        spans=spans,
        edges=edges,
    )


def _blocks(content: Any) -> list[dict]:
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _extract_assistant_text(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    parts = [b.get("text", "") for b in _blocks(content) if b.get("type") == "text"]
    text = "\n".join(p for p in parts if p)
    return text or None


def _extract_user_text(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    parts = [b.get("text", "") for b in _blocks(content) if b.get("type") == "text"]
    text = "\n".join(p for p in parts if p)
    return text or None


def _attach_tool_results(
    content: Any, tooluse_to_span: dict[str, str], spans: list[SpanInput], ts: datetime | None
) -> None:
    """A user message may carry tool_result blocks; attach output to the tool span."""
    by_ext = {s.external_span_id: s for s in spans}
    for block in _blocks(content):
        if block.get("type") != "tool_result":
            continue
        tool_use_id = block.get("tool_use_id")
        span_ext = tooluse_to_span.get(tool_use_id) if tool_use_id else None
        if not span_ext or span_ext not in by_ext:
            continue
        span = by_ext[span_ext]
        result = block.get("content")
        text = result if isinstance(result, str) else _short_json(result)
        span.io.append(IORecord(io_type=IOType.tool_output, content_text=text))
        span.end_time = ts
        if span.start_time is None:
            span.start_time = ts
        if block.get("is_error"):
            span.status = "error"
            span.error = ErrorInfo(error_type="ToolError", message=str(text)[:2000])


def _maybe_file_io(tool_name: str, tool_input: dict, io: list[IORecord]) -> None:
    path = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path")
    if not path:
        return
    if tool_name in FILE_READ_TOOLS:
        io.append(IORecord(io_type=IOType.file_read, file_path=str(path)))
    elif tool_name in FILE_WRITE_TOOLS:
        io.append(IORecord(io_type=IOType.file_write, file_path=str(path)))


def _usage_to_cost(model: str | None, usage: dict) -> CostRecord | None:
    if not usage:
        return None
    return CostRecord(
        model=model,
        input_tokens=int(usage.get("input_tokens", 0) or 0),
        output_tokens=int(usage.get("output_tokens", 0) or 0),
        cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
        cache_write_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
    )
