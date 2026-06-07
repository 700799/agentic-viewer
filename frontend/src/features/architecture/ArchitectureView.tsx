import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { useDiagram } from "@/api/hooks";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  themeVariables: { fontSize: "13px" },
});

type DiagramType = "flowchart" | "sequence" | "dependency" | "architecture";

const TYPES: { id: DiagramType; label: string }[] = [
  { id: "flowchart", label: "Flowchart" },
  { id: "sequence", label: "Sequence" },
  { id: "dependency", label: "Dependencies" },
  { id: "architecture", label: "System" },
];

export function ArchitectureView({ sessionId }: { sessionId: string }) {
  const [type, setType] = useState<DiagramType>("flowchart");
  const { data } = useDiagram(sessionId, type);
  const hostRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function render() {
      if (!data?.mermaid || !hostRef.current) return;
      try {
        const id = `mmd-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, data.mermaid);
        if (!cancelled && hostRef.current) hostRef.current.innerHTML = svg;
        setError(null);
      } catch (e) {
        setError(String(e));
      }
    }
    render();
    return () => {
      cancelled = true;
    };
  }, [data]);

  return (
    <div className="arch">
      <div className="arch-controls">
        {TYPES.map((t) => (
          <button
            key={t.id}
            className={`tab ${type === t.id ? "active" : ""}`}
            onClick={() => setType(t.id)}
          >
            {t.label}
          </button>
        ))}
        <div className="spacer" style={{ flex: 1 }} />
        <button
          className="btn"
          onClick={() => data && navigator.clipboard.writeText(data.mermaid)}
        >
          Copy Mermaid
        </button>
      </div>

      <div className="mermaid-host" ref={hostRef} />
      {error && <div className="tl-error" style={{ marginTop: 12 }}>{error}</div>}

      <div className="mermaid-src">
        <h3 style={{ fontSize: 12, color: "var(--text-dim)" }}>Generated source</h3>
        <pre>{data?.mermaid ?? ""}</pre>
      </div>
    </div>
  );
}
