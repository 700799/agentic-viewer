import type { SessionSummary } from "@/types/api";

interface Props {
  sessions: SessionSummary[];
  selectedId: string | undefined;
  onSelect: (id: string) => void;
}

export function SessionSidebar({ sessions, selectedId, onSelect }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>
          <span className="logo" />
          Agent Canvas
        </h1>
        <p>Visual canvas for Claude Code &amp; agent workflows</p>
      </div>
      <div className="session-list">
        {sessions.length === 0 && (
          <div style={{ padding: 16, fontSize: 12, color: "var(--text-dim)" }}>
            No sessions yet. Run <code>make seed</code> or{" "}
            <code>agentcanvas ingest &lt;file&gt;</code>.
          </div>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`session-item ${s.id === selectedId ? "active" : ""}`}
            onClick={() => onSelect(s.id)}
          >
            <div className="title">{s.title ?? s.external_id}</div>
            <div className="meta">
              <span className="badge">{s.source}</span>
              <span>{s.span_count} spans</span>
              <span>${s.total_cost_usd.toFixed(4)}</span>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
