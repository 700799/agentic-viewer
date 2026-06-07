"""Build the logical DAG (nodes/edges) the frontend maps onto React Flow.

Layout (x/y) is computed client-side; the backend only returns the logical graph plus
grouping hints. Nodes are emitted for agents, LLM/tool/mcp spans, MCP servers, files,
and memory ops. Files and memory are derived from span IO so the DAG can show data flow.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db.models import Agent, Cost, Edge, McpServer, Span, SpanIO
from app.schemas.api import GraphEdge, GraphNode, GraphResponse, GroupInfo

# span_kind -> react-flow node type
_KIND_TO_TYPE = {
    "session_root": "agent",
    "agent": "agent",
    "llm": "llm",
    "tool": "tool",
    "mcp_tool": "mcpTool",
    "memory": "memory",
    "chain": "tool",
    "retrieval": "tool",
    "handoff": "tool",
    "custom": "tool",
}
_EDGE_KIND_TO_TYPE = {
    "call": "call",
    "handoff": "handoff",
    "data_flow": "data",
    "mcp_link": "mcp",
    "file_dep": "data",
    "memory_dep": "data",
}


def build_graph(
    db: DbSession,
    session_id: uuid.UUID,
    include_files: bool = True,
    include_memory: bool = True,
) -> GraphResponse:
    spans = list(
        db.scalars(
            select(Span).where(Span.session_id == session_id).order_by(Span.sequence)
        )
    )
    agents = {a.id: a for a in db.scalars(select(Agent).where(Agent.session_id == session_id))}
    servers = {
        s.id: s for s in db.scalars(select(McpServer).where(McpServer.session_id == session_id))
    }
    costs = {c.span_id: c for c in db.scalars(select(Cost).where(Cost.session_id == session_id))}

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    groups: dict[str, GroupInfo] = {}

    # MCP server service nodes (connected services).
    for server in servers.values():
        sid = f"mcp:{server.id}"
        nodes.append(
            GraphNode(
                id=sid,
                type="mcpServer",
                label=server.name,
                data={"transport": server.transport, "tools": server.tools},
            )
        )

    span_node_id = {sp.id: f"span:{sp.id}" for sp in spans}

    for sp in spans:
        agent = agents.get(sp.agent_id) if sp.agent_id else None
        group_id = f"group:{agent.id}" if agent else None
        cost = costs.get(sp.id)
        node = GraphNode(
            id=span_node_id[sp.id],
            type=_KIND_TO_TYPE.get(sp.span_kind, "tool"),
            label=sp.name,
            parent_id=group_id,
            group=group_id,
            data={
                "kind": sp.span_kind,
                "status": sp.status,
                "sequence": sp.sequence,
                "durationMs": sp.duration_ms,
                "agentName": agent.name if agent else None,
                "model": (sp.attributes or {}).get("model"),
                "costUsd": float(cost.cost_usd) if cost else None,
                "inputTokens": cost.input_tokens if cost else None,
                "outputTokens": cost.output_tokens if cost else None,
            },
        )
        nodes.append(node)
        if agent and group_id:
            grp = groups.setdefault(
                group_id, GroupInfo(id=group_id, label=agent.name, node_ids=[])
            )
            grp.node_ids.append(node.id)

        # Link mcp_tool spans to their server node.
        if sp.mcp_server_id and sp.mcp_server_id in servers:
            edges.append(
                GraphEdge(
                    id=f"e:mcp:{sp.id}",
                    source=node.id,
                    target=f"mcp:{sp.mcp_server_id}",
                    type="mcp",
                    label="mcp",
                )
            )

    # File and memory nodes derived from span IO.
    if include_files or include_memory:
        io_rows = list(
            db.scalars(
                select(SpanIO).join(Span, SpanIO.span_id == Span.id).where(
                    Span.session_id == session_id
                )
            )
        )
        file_nodes: dict[str, str] = {}
        for io in io_rows:
            if include_files and io.io_type in ("file_read", "file_write") and io.file_path:
                fid = file_nodes.get(io.file_path)
                if fid is None:
                    fid = f"file:{len(file_nodes)}"
                    file_nodes[io.file_path] = fid
                    nodes.append(
                        GraphNode(
                            id=fid, type="file", label=io.file_path.split("/")[-1],
                            data={"path": io.file_path},
                        )
                    )
                src = span_node_id.get(io.span_id)
                if src:
                    if io.io_type == "file_read":
                        edges.append(GraphEdge(id=f"e:fr:{io.id}", source=fid, target=src, type="data", label="read"))
                    else:
                        edges.append(GraphEdge(id=f"e:fw:{io.id}", source=src, target=fid, type="data", label="write"))
            if include_memory and io.io_type in ("memory_read", "memory_write"):
                mid = f"mem:{io.id}"
                nodes.append(GraphNode(id=mid, type="memory", label=io.io_type, data={}))
                src = span_node_id.get(io.span_id)
                if src:
                    edges.append(GraphEdge(id=f"e:mem:{io.id}", source=src, target=mid, type="data"))

    # Explicit edges (call/handoff/data_flow). Skip self-links used only as markers.
    for e in db.scalars(select(Edge).where(Edge.session_id == session_id)):
        if e.source_span_id == e.target_span_id:
            continue
        src = span_node_id.get(e.source_span_id)
        tgt = span_node_id.get(e.target_span_id)
        if not src or not tgt:
            continue
        edges.append(
            GraphEdge(
                id=f"e:{e.id}",
                source=src,
                target=tgt,
                type=_EDGE_KIND_TO_TYPE.get(e.edge_kind, "call"),
                label=e.label,
            )
        )

    return GraphResponse(nodes=nodes, edges=edges, groups=list(groups.values()))
