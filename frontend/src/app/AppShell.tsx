import { useEffect, useState } from "react";
import { useSessions } from "@/api/hooks";
import { SessionSidebar } from "@/features/sessions/SessionSidebar";
import { DagView } from "@/features/dag/DagView";
import { TimelineView } from "@/features/timeline/TimelineView";
import { CostView } from "@/features/cost/CostView";
import { ArchitectureView } from "@/features/architecture/ArchitectureView";
import { CompareView } from "@/features/compare/CompareView";
import { useCanvasStore } from "@/store/canvasStore";

type View = "dag" | "timeline" | "cost" | "architecture" | "compare";

const TABS: { id: View; label: string }[] = [
  { id: "dag", label: "DAG" },
  { id: "timeline", label: "Timeline" },
  { id: "cost", label: "Cost" },
  { id: "architecture", label: "Architecture" },
  { id: "compare", label: "Compare" },
];

export function AppShell() {
  const { data } = useSessions();
  const [selectedSession, setSelectedSession] = useState<string | undefined>();
  const [view, setView] = useState<View>("dag");
  const reset = useCanvasStore((s) => s.reset);

  // Default to the first session once loaded.
  useEffect(() => {
    if (!selectedSession && data?.items.length) {
      setSelectedSession(data.items[0].id);
    }
  }, [data, selectedSession]);

  function pickSession(id: string) {
    setSelectedSession(id);
    reset();
  }

  return (
    <div className="app">
      <SessionSidebar
        sessions={data?.items ?? []}
        selectedId={selectedSession}
        onSelect={pickSession}
      />
      <div className="main">
        <div className="tabbar">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab ${view === t.id ? "active" : ""}`}
              onClick={() => setView(t.id)}
            >
              {t.label}
            </button>
          ))}
          <div className="spacer" />
          <Legend />
        </div>
        <div className="view">
          {!selectedSession ? (
            <div className="empty">Ingest a trace, then select a session.</div>
          ) : view === "dag" ? (
            <DagView sessionId={selectedSession} />
          ) : view === "timeline" ? (
            <TimelineView sessionId={selectedSession} />
          ) : view === "cost" ? (
            <CostView sessionId={selectedSession} />
          ) : view === "architecture" ? (
            <ArchitectureView sessionId={selectedSession} />
          ) : (
            <CompareView baseId={selectedSession} sessions={data?.items ?? []} />
          )}
        </div>
      </div>
    </div>
  );
}

function Legend() {
  const items: [string, string][] = [
    ["agent", "Agent"],
    ["llm", "LLM"],
    ["tool", "Tool"],
    ["mcpTool", "MCP"],
    ["file", "File"],
    ["memory", "Memory"],
  ];
  return (
    <div className="legend">
      {items.map(([k, label]) => (
        <span key={k}>
          <i className={`node-kind dot-${k}`} style={{ display: "inline-block" }} /> {label}
        </span>
      ))}
    </div>
  );
}
