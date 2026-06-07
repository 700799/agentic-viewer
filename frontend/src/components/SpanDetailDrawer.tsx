import { useSpan } from "@/api/hooks";
import { useCanvasStore } from "@/store/canvasStore";
import type { SpanIODetail } from "@/types/api";

const IO_LABEL: Record<string, string> = {
  prompt: "Prompt",
  response: "Response",
  tool_input: "Tool input",
  tool_output: "Tool output",
  file_read: "File read",
  file_write: "File write",
  memory_read: "Memory read",
  memory_write: "Memory write",
};

export function SpanDetailDrawer({ spanId }: { spanId: string }) {
  const { data: span, isLoading } = useSpan(spanId);
  const setSelected = useCanvasStore((s) => s.setSelected);

  return (
    <div className="drawer">
      <button className="close" onClick={() => setSelected(null)}>
        ×
      </button>
      {isLoading || !span ? (
        <div>Loading…</div>
      ) : (
        <>
          <h2>{span.name}</h2>
          <div style={{ fontSize: 12, color: "var(--text-dim)" }}>{span.kind}</div>
          <div className="kv">
            <span className="k">Status</span>
            <span style={{ color: span.status === "error" ? "var(--error)" : "var(--ok)" }}>
              {span.status}
            </span>
            {span.agent_name && (
              <>
                <span className="k">Agent</span>
                <span>{span.agent_name}</span>
              </>
            )}
            {span.duration_ms != null && (
              <>
                <span className="k">Latency</span>
                <span>{span.duration_ms} ms</span>
              </>
            )}
            {span.cost && (
              <>
                <span className="k">Tokens</span>
                <span>
                  {span.cost.input_tokens} in / {span.cost.output_tokens} out
                </span>
                <span className="k">Cost</span>
                <span>${span.cost.cost_usd.toFixed(6)}</span>
              </>
            )}
          </div>

          {span.error && (
            <div className="io-block">
              <div className="io-head tl-error">Error</div>
              <pre className="tl-error">{span.error}</pre>
            </div>
          )}

          {span.io.map((io: SpanIODetail, i: number) => (
            <div className="io-block" key={i}>
              <div className="io-head">
                {IO_LABEL[io.io_type] ?? io.io_type}
                {io.file_path ? ` — ${io.file_path}` : ""}
                {io.truncated ? " (truncated)" : ""}
              </div>
              {io.content_text && <pre>{io.content_text}</pre>}
            </div>
          ))}

          {Object.keys(span.attributes).length > 0 && (
            <div className="io-block">
              <div className="io-head">Attributes</div>
              <pre>{JSON.stringify(span.attributes, null, 2)}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
