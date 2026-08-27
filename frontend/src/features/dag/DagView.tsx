import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import { useGraph, useTimeline } from "@/api/hooks";
import type { GraphNode } from "@/types/api";
import { layoutGraph } from "./layout";
import { CanvasNode } from "./nodes/CanvasNode";
import { useCanvasStore } from "@/store/canvasStore";
import { SpanDetailDrawer } from "@/components/SpanDetailDrawer";
import { SearchBar } from "@/components/SearchBar";

// React Flow stores our GraphNode under `data.node` (see layout.ts).
type CanvasNodeData = { node?: GraphNode };

const nodeTypes = { canvasNode: CanvasNode };

const MINIMAP_COLORS: Record<string, string> = {
  agent: "#d29922",
  llm: "#a371f7",
  tool: "#3fb950",
  mcpTool: "#ec6547",
  mcpServer: "#ec6547",
  file: "#56d4dd",
  memory: "#db61a2",
};

export function DagView({ sessionId }: { sessionId: string }) {
  const { data: graph, isLoading } = useGraph(sessionId);
  const { data: timeline } = useTimeline(sessionId);
  const setSelected = useCanvasStore((s) => s.setSelected);
  const setReplayCursor = useCanvasStore((s) => s.setReplayCursor);
  const replayCursor = useCanvasStore((s) => s.replayCursor);
  const selectedSpanId = useCanvasStore((s) => s.selectedSpanId);

  const { nodes, edges } = useMemo(
    () => (graph ? layoutGraph(graph) : { nodes: [], edges: [] }),
    [graph]
  );

  const maxSeq = useMemo(
    () => (timeline ? Math.max(0, ...timeline.items.map((i) => i.sequence)) : 0),
    [timeline]
  );

  const onNodeClick: NodeMouseHandler = (_e, node: Node) => {
    if (node.id.startsWith("span:")) setSelected(node.id.slice(5));
  };

  if (isLoading) return <div className="empty">Loading graph…</div>;
  if (!graph || graph.nodes.length === 0) return <div className="empty">No spans in this session.</div>;

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ flex: 1, position: "relative" }}>
        <div style={{ position: "absolute", top: 10, left: 10, zIndex: 5 }}>
          <SearchBar nodes={graph.nodes} />
        </div>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          fitView
          minZoom={0.1}
          maxZoom={4}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#21262d" />
          <Controls />
          <MiniMap
            pannable
            zoomable
            nodeColor={(n) => MINIMAP_COLORS[(n.data as CanvasNodeData).node?.type ?? ""] ?? "#8b949e"}
            maskColor="rgba(13,17,23,0.7)"
            style={{ background: "#161b22" }}
          />
        </ReactFlow>
        {selectedSpanId && <SpanDetailDrawer spanId={selectedSpanId} />}
      </div>
      <div className="replay-bar">
        <button
          className="btn"
          onClick={() => setReplayCursor(replayCursor == null ? 0 : null)}
        >
          {replayCursor == null ? "▶ Replay" : "✕ Show all"}
        </button>
        <input
          type="range"
          min={0}
          max={maxSeq}
          value={replayCursor ?? maxSeq}
          onChange={(e) => setReplayCursor(Number(e.target.value))}
        />
        <span style={{ fontSize: 12, color: "var(--text-dim)", minWidth: 90 }}>
          step {replayCursor ?? maxSeq} / {maxSeq}
        </span>
      </div>
    </div>
  );
}
