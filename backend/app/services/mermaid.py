"""Deterministic Mermaid diagram generation from a trace (no LLM required).

Four diagram types:
- flowchart:   agent/tool spans + parent/child + handoff edges
- sequence:    agents & MCP servers as participants, ordered tool/LLM messages
- dependency:  files <-> agents derived from file IO
- architecture: agents + MCP servers grouped as a system view
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db.models import Agent, McpServer, Span, SpanIO


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def _esc(label: str) -> str:
    return label.replace('"', "'").replace("\n", " ")[:60]


def generate(db: DbSession, session_id: uuid.UUID, diagram_type: str) -> str:
    if diagram_type == "sequence":
        return _sequence(db, session_id)
    if diagram_type == "dependency":
        return _dependency(db, session_id)
    if diagram_type == "architecture":
        return _architecture(db, session_id)
    return _flowchart(db, session_id)


def _spans(db: DbSession, session_id: uuid.UUID) -> list[Span]:
    return list(
        db.scalars(select(Span).where(Span.session_id == session_id).order_by(Span.sequence))
    )


def _flowchart(db: DbSession, session_id: uuid.UUID) -> str:
    spans = _spans(db, session_id)
    lines = ["flowchart TD"]
    shapes = {
        "agent": ('[["', '"]]'),
        "session_root": ('[["', '"]]'),
        "llm": ('("', '")'),
        "tool": ('(["', '"])'),
        "mcp_tool": ('{{"', '"}}'),
    }
    for sp in spans:
        nid = f"n_{_safe_id(str(sp.id))}"
        open_s, close_s = shapes.get(sp.span_kind, ('["', '"]'))
        lines.append(f'  {nid}{open_s}{_esc(sp.name)}{close_s}')
    for sp in spans:
        if sp.parent_span_id:
            lines.append(f"  n_{_safe_id(str(sp.parent_span_id))} --> n_{_safe_id(str(sp.id))}")
    return "\n".join(lines)


def _sequence(db: DbSession, session_id: uuid.UUID) -> str:
    spans = _spans(db, session_id)
    agents = {a.id: a.name for a in db.scalars(select(Agent).where(Agent.session_id == session_id))}
    lines = ["sequenceDiagram"]
    participants: list[str] = []
    for name in dict.fromkeys(agents.values()):
        pid = _safe_id(name)
        participants.append(pid)
        lines.append(f"  participant {pid} as {name}")
    for sp in spans:
        if sp.span_kind in ("tool", "mcp_tool") and sp.agent_id:
            actor = _safe_id(agents.get(sp.agent_id, "agent"))
            target = _safe_id(sp.name)
            lines.append(f"  {actor}->>{target}: call")
            lines.append(f"  {target}-->>{actor}: {'error' if sp.status == 'error' else 'result'}")
    return "\n".join(lines)


def _dependency(db: DbSession, session_id: uuid.UUID) -> str:
    io_rows = list(
        db.scalars(
            select(SpanIO).join(Span, SpanIO.span_id == Span.id).where(Span.session_id == session_id)
        )
    )
    spans = {sp.id: sp for sp in _spans(db, session_id)}
    agents = {a.id: a.name for a in db.scalars(select(Agent).where(Agent.session_id == session_id))}
    lines = ["graph LR"]
    seen_files: set[str] = set()
    for io in io_rows:
        if io.io_type not in ("file_read", "file_write") or not io.file_path:
            continue
        fid = f"f_{_safe_id(io.file_path)}"
        if io.file_path not in seen_files:
            lines.append(f'  {fid}[/"{_esc(io.file_path)}"/]')
            seen_files.add(io.file_path)
        sp = spans.get(io.span_id)
        actor = _safe_id(agents.get(sp.agent_id, "agent")) if sp and sp.agent_id else "agent"
        lines.append(f"  {actor}([{actor}])")
        if io.io_type == "file_read":
            lines.append(f"  {fid} -->|read| {actor}")
        else:
            lines.append(f"  {actor} -->|write| {fid}")
    return "\n".join(lines)


def _architecture(db: DbSession, session_id: uuid.UUID) -> str:
    agents = list(db.scalars(select(Agent).where(Agent.session_id == session_id)))
    servers = list(db.scalars(select(McpServer).where(McpServer.session_id == session_id)))
    lines = ["flowchart TB", "  subgraph Agents"]
    for a in agents:
        lines.append(f'    a_{_safe_id(str(a.id))}[["{_esc(a.name)}"]]')
    lines.append("  end")
    if servers:
        lines.append("  subgraph MCP_Servers")
        for s in servers:
            lines.append(f'    s_{_safe_id(str(s.id))}{{{{"{_esc(s.name)}"}}}}')
        lines.append("  end")
    # Connect agents that used mcp tools to servers.
    links = set()
    for sp in db.scalars(
        select(Span).where(Span.session_id == session_id, Span.span_kind == "mcp_tool")
    ):
        if sp.agent_id and sp.mcp_server_id:
            links.add((sp.agent_id, sp.mcp_server_id))
    for aid, sid in links:
        lines.append(f"  a_{_safe_id(str(aid))} --> s_{_safe_id(str(sid))}")
    return "\n".join(lines)
