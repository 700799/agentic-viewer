import { useState } from "react";
import { useCompare } from "@/api/hooks";
import type { SessionSummary } from "@/types/api";

function delta(n: number, invert = false) {
  const cls = n === 0 ? "" : (n > 0) !== invert ? "delta-pos" : "delta-neg";
  const sign = n > 0 ? "+" : "";
  return <span className={cls}>{sign}{n}</span>;
}

export function CompareView({
  baseId,
  sessions,
}: {
  baseId: string;
  sessions: SessionSummary[];
}) {
  const [bId, setBId] = useState<string | undefined>(
    sessions.find((s) => s.id !== baseId)?.id
  );
  const { data, isLoading } = useCompare(baseId, bId);

  return (
    <div className="compare">
      <div className="compare-pick">
        <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Base (A):</span>
        <strong style={{ fontSize: 13 }}>
          {sessions.find((s) => s.id === baseId)?.title ?? baseId}
        </strong>
        <span style={{ fontSize: 12, color: "var(--text-dim)" }}>vs (B):</span>
        <select className="picker" value={bId ?? ""} onChange={(e) => setBId(e.target.value)}>
          <option value="">— pick a run —</option>
          {sessions
            .filter((s) => s.id !== baseId)
            .map((s) => (
              <option key={s.id} value={s.id}>
                {s.title ?? s.external_id}
              </option>
            ))}
        </select>
      </div>

      {!bId && <div className="empty">Pick a second run to compare.</div>}
      {bId && isLoading && <div className="empty">Comparing…</div>}

      {data && (
        <>
          <div className="cost-cards" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            <div className="card">
              <div className="k">Cost Δ (B − A)</div>
              <div className="v">{delta(Number(data.summary.cost_delta_usd.toFixed(4)))}</div>
            </div>
            <div className="card">
              <div className="k">Duration Δ (ms)</div>
              <div className="v">{delta(data.summary.duration_delta_ms)}</div>
            </div>
            <div className="card">
              <div className="k">Span count Δ</div>
              <div className="v">{delta(data.summary.span_count_delta)}</div>
            </div>
          </div>

          <div className="cost-section">
            <h3>Cost by agent</h3>
            <table className="cmp">
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>A ($)</th>
                  <th>B ($)</th>
                  <th>Δ ($)</th>
                </tr>
              </thead>
              <tbody>
                {data.cost_by_agent.map((r) => (
                  <tr key={r.name}>
                    <td>{r.name}</td>
                    <td>{r.a_usd.toFixed(4)}</td>
                    <td>{r.b_usd.toFixed(4)}</td>
                    <td>{delta(Number(r.delta_usd.toFixed(4)))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="cost-section">
            <h3>Structural diff</h3>
            <table className="cmp">
              <thead>
                <tr>
                  <th>Span signature</th>
                  <th>Status</th>
                  <th>A dur (ms)</th>
                  <th>B dur (ms)</th>
                </tr>
              </thead>
              <tbody>
                {data.aligned_spans.map((s) => (
                  <tr key={s.signature}>
                    <td>{s.signature}</td>
                    <td className={`status-${s.status}`}>{s.status}</td>
                    <td>{s.a_duration_ms ?? "—"}</td>
                    <td>{s.b_duration_ms ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
