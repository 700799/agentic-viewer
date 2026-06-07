import { useTimeline } from "@/api/hooks";
import { useCanvasStore } from "@/store/canvasStore";
import { SpanDetailDrawer } from "@/components/SpanDetailDrawer";
import type { TimelineEvent } from "@/types/api";

const KIND_COLOR: Record<string, string> = {
  agent: "var(--agent)",
  session_root: "var(--agent)",
  llm: "var(--llm)",
  tool: "var(--tool)",
  mcp_tool: "var(--mcp)",
  memory: "var(--memory)",
};

function snippet(e: TimelineEvent): { label: string; text: string | null } {
  const p = e.preview;
  if (p.error) return { label: "error", text: p.error };
  if (p.response) return { label: "response", text: p.response };
  if (p.tool_output) return { label: "output", text: p.tool_output };
  if (p.tool_input) return { label: "input", text: p.tool_input };
  if (p.prompt) return { label: "prompt", text: p.prompt };
  return { label: "", text: null };
}

export function TimelineView({ sessionId }: { sessionId: string }) {
  const { data, isLoading } = useTimeline(sessionId);
  const selectedSpanId = useCanvasStore((s) => s.selectedSpanId);
  const setSelected = useCanvasStore((s) => s.setSelected);
  const replayCursor = useCanvasStore((s) => s.replayCursor);

  if (isLoading) return <div className="empty">Loading timeline…</div>;
  if (!data || data.items.length === 0) return <div className="empty">No events.</div>;

  return (
    <div style={{ height: "100%", position: "relative" }}>
      <div className="timeline">
        {data.items.map((e) => {
          const s = snippet(e);
          const dim = replayCursor != null && e.sequence > replayCursor;
          return (
            <div
              key={e.span_id}
              className={`tl-row ${selectedSpanId === e.span_id ? "active" : ""} ${dim ? "dim" : ""}`}
              onClick={() => setSelected(e.span_id)}
            >
              <div className="tl-seq">#{e.sequence}</div>
              <div className="tl-kind" style={{ color: KIND_COLOR[e.kind] ?? "var(--text)" }}>
                {e.kind}
              </div>
              <div className="tl-body">
                <div className="label">
                  {e.name}
                  {e.agent_name ? (
                    <span style={{ color: "var(--text-dim)", fontWeight: 400 }}> · @{e.agent_name}</span>
                  ) : null}
                </div>
                {s.text && (
                  <div className={`snippet ${s.label === "error" ? "tl-error" : ""}`}>
                    <strong>{s.label}:</strong> {s.text}
                  </div>
                )}
              </div>
              <div className="tl-metrics">
                {e.duration_ms != null && <div>{e.duration_ms} ms</div>}
                {e.cost && <div>${e.cost.cost_usd.toFixed(4)}</div>}
                {e.cost && (
                  <div>
                    {e.cost.input_tokens}/{e.cost.output_tokens} tok
                  </div>
                )}
                {e.status === "error" && <div className="tl-error">error</div>}
              </div>
            </div>
          );
        })}
      </div>
      {selectedSpanId && <SpanDetailDrawer spanId={selectedSpanId} />}
    </div>
  );
}
