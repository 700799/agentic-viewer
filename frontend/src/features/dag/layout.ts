// Dagre layout: turn the backend's logical graph into positioned React Flow nodes.
// (ELK hierarchical/grouped layout is the V1 upgrade; dagre keeps the MVP fast & flat.)

import dagre from "dagre";
import type { Edge, Node } from "reactflow";
import { MarkerType, Position } from "reactflow";
import type { GraphResponse } from "@/types/api";

const NODE_W = 180;
const NODE_H = 56;

const EDGE_STYLE: Record<string, { color: string; dashed: boolean }> = {
  call: { color: "#8b949e", dashed: false },
  handoff: { color: "#d29922", dashed: true },
  data: { color: "#56d4dd", dashed: true },
  mcp: { color: "#ec6547", dashed: false },
};

export interface LayoutResult {
  nodes: Node[];
  edges: Edge[];
}

export function layoutGraph(graph: GraphResponse): LayoutResult {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 40, ranksep: 70, marginx: 20, marginy: 20 });

  for (const n of graph.nodes) {
    g.setNode(n.id, { width: NODE_W, height: NODE_H });
  }
  for (const e of graph.edges) {
    if (g.hasNode(e.source) && g.hasNode(e.target)) {
      g.setEdge(e.source, e.target);
    }
  }
  dagre.layout(g);

  const nodes: Node[] = graph.nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      id: n.id,
      type: "canvasNode",
      position: { x: (pos?.x ?? 0) - NODE_W / 2, y: (pos?.y ?? 0) - NODE_H / 2 },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      data: { node: n },
    };
  });

  const edges: Edge[] = graph.edges
    .filter((e) => e.source !== e.target)
    .map((e) => {
      const style = EDGE_STYLE[e.type] ?? EDGE_STYLE.call;
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label ?? undefined,
        animated: e.type === "call",
        style: {
          stroke: style.color,
          strokeWidth: 1.5,
          strokeDasharray: style.dashed ? "5 4" : undefined,
        },
        labelStyle: { fill: "#8b949e", fontSize: 10 },
        labelBgStyle: { fill: "#161b22" },
        markerEnd: { type: MarkerType.ArrowClosed, color: style.color },
      };
    });

  return { nodes, edges };
}
