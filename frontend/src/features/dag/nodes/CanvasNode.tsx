// One custom React Flow node renders every span/file/mcp type, styled by kind.
// Keeping it unified (vs. one component per type) avoids duplication; the `type`
// from the backend drives color + which sub-metrics show.

import { Handle, Position } from "reactflow";
import type { GraphNode } from "@/types/api";
import { useCanvasStore } from "@/store/canvasStore";

interface Props {
  data: { node: GraphNode };
}

function fmtMs(ms?: number | null) {
  if (ms == null) return null;
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

export function CanvasNode({ data }: Props) {
  const n = data.node;
  const d = n.data;
  const selectedSpanId = useCanvasStore((s) => s.selectedSpanId);
  const replayCursor = useCanvasStore((s) => s.replayCursor);
  const highlightIds = useCanvasStore((s) => s.highlightIds);

  const spanId = n.id.startsWith("span:") ? n.id.slice(5) : null;
  const isActive = spanId != null && selectedSpanId === spanId;
  const isMatch = highlightIds.has(n.id);
  const dimmed =
    replayCursor != null && d.sequence != null && d.sequence > replayCursor && !isActive;

  const classes = [
    "rf-node",
    `kind-${n.type}`,
    d.status === "error" ? "status-error" : "",
    isActive ? "active" : "",
    isMatch ? "match" : "",
    dimmed ? "dim" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes}>
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div className="node-head">
        <span className={`node-kind dot-${n.type}`} />
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {n.label}
        </span>
      </div>
      <div className="node-sub">
        {d.agentName && n.type !== "agent" && <span>@{d.agentName}</span>}
        {d.model && <span>{d.model}</span>}
        {fmtMs(d.durationMs) && <span>{fmtMs(d.durationMs)}</span>}
        {d.costUsd != null && d.costUsd > 0 && <span>${d.costUsd.toFixed(4)}</span>}
        {d.transport && <span>{d.transport}</span>}
        {d.path && <span title={d.path}>{d.path}</span>}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
