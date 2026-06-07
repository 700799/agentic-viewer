import { useCost } from "@/api/hooks";
import type { CostReport } from "@/types/api";

function BarList({
  rows,
}: {
  rows: { name: string; value: number; suffix: string }[];
}) {
  const max = Math.max(1e-9, ...rows.map((r) => r.value));
  return (
    <>
      {rows.map((r) => (
        <div className="bar-row" key={r.name}>
          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {r.name}
          </span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(r.value / max) * 100}%` }} />
          </div>
          <span style={{ textAlign: "right" }}>{r.suffix}</span>
        </div>
      ))}
    </>
  );
}

function Sparkline({ report }: { report: CostReport }) {
  const pts = report.timeline;
  if (pts.length < 2) return null;
  const w = 600;
  const h = 120;
  const maxY = Math.max(...pts.map((p) => p.cumulative_cost_usd), 1e-9);
  const stepX = w / (pts.length - 1);
  const d = pts
    .map((p, i) => `${i === 0 ? "M" : "L"} ${i * stepX} ${h - (p.cumulative_cost_usd / maxY) * h}`)
    .join(" ");
  return (
    <svg className="spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <path d={`${d} L ${w} ${h} L 0 ${h} Z`} fill="rgba(163,113,247,0.15)" />
      <path d={d} fill="none" stroke="var(--llm)" strokeWidth={2} />
    </svg>
  );
}

export function CostView({ sessionId }: { sessionId: string }) {
  const { data, isLoading } = useCost(sessionId);
  if (isLoading) return <div className="empty">Loading cost…</div>;
  if (!data) return <div className="empty">No cost data.</div>;

  const t = data.total;
  return (
    <div className="cost">
      <div className="cost-cards">
        <div className="card">
          <div className="k">Total cost</div>
          <div className="v">${t.cost_usd.toFixed(4)}</div>
        </div>
        <div className="card">
          <div className="k">Input tokens</div>
          <div className="v">{t.input_tokens.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="k">Output tokens</div>
          <div className="v">{t.output_tokens.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="k">Cache read</div>
          <div className="v">{t.cache_read_tokens.toLocaleString()}</div>
        </div>
      </div>

      <div className="cost-section">
        <h3>Cumulative cost over execution</h3>
        <Sparkline report={data} />
      </div>

      <div className="cost-section">
        <h3>Cost per agent</h3>
        <BarList
          rows={data.per_agent.map((a) => ({
            name: a.name,
            value: a.cost_usd,
            suffix: `$${a.cost_usd.toFixed(4)}`,
          }))}
        />
      </div>

      <div className="cost-section">
        <h3>Cost per model</h3>
        <BarList
          rows={data.per_model.map((m) => ({
            name: m.model,
            value: m.cost_usd,
            suffix: `$${m.cost_usd.toFixed(4)}`,
          }))}
        />
      </div>

      <div className="cost-section">
        <h3>Cost per step</h3>
        <BarList
          rows={data.per_step.map((s) => ({
            name: `#${s.sequence} ${s.name}`,
            value: s.cost_usd,
            suffix: `$${s.cost_usd.toFixed(4)}`,
          }))}
        />
      </div>
    </div>
  );
}
