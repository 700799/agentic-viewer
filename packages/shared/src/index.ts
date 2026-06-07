// @agentcanvas/shared — the canonical trace contract for adapter authors.
//
// The authoritative schema is the backend Pydantic model
// (backend/app/schemas/canonical.py), exported as JSON Schema at
// GET /api/v1/schema/canonical and committed to
// frontend/src/types/canonical.schema.json. Run `make gen-types` to regenerate the
// TypeScript types from that schema.
//
// These hand-mirrored types let TypeScript adapters (e.g. OpenAI Agents, browser-side
// Claude Code) build envelopes with type safety without depending on the frontend build.

export type Source =
  | "claude_code"
  | "openai_agents"
  | "langgraph"
  | "crewai"
  | "autogen"
  | "custom";

export type SpanKind =
  | "session_root"
  | "agent"
  | "llm"
  | "tool"
  | "mcp_tool"
  | "file_io"
  | "memory"
  | "handoff"
  | "chain"
  | "retrieval"
  | "custom";

export type IOType =
  | "prompt"
  | "response"
  | "tool_input"
  | "tool_output"
  | "file_read"
  | "file_write"
  | "memory_read"
  | "memory_write";

export type EdgeKind =
  | "call"
  | "handoff"
  | "data_flow"
  | "mcp_link"
  | "file_dep"
  | "memory_dep";

export interface IORecord {
  io_type: IOType;
  role?: string | null;
  content_text?: string | null;
  file_path?: string | null;
  byte_size?: number | null;
  meta?: Record<string, unknown>;
}

export interface CostRecord {
  model?: string | null;
  input_tokens?: number;
  output_tokens?: number;
  cache_read_tokens?: number;
  cache_write_tokens?: number;
  cost_usd?: number | null;
}

export interface SpanInput {
  external_span_id: string;
  parent_external_span_id?: string | null;
  kind: SpanKind;
  name: string;
  agent_external_id?: string | null;
  mcp_server_external_id?: string | null;
  status?: string;
  start_time?: string | null;
  end_time?: string | null;
  attributes?: Record<string, unknown>;
  io?: IORecord[];
  cost?: CostRecord | null;
  error?: { error_type?: string; message?: string; stack?: string } | null;
}

export interface EdgeInput {
  source_external_span_id: string;
  target_external_span_id: string;
  kind?: EdgeKind;
  label?: string | null;
  meta?: Record<string, unknown>;
}

export interface CanonicalEnvelope {
  schema_version?: string;
  source: Source;
  session: {
    external_id: string;
    title?: string | null;
    started_at?: string | null;
    ended_at?: string | null;
    status?: string;
    meta?: Record<string, unknown>;
  };
  agents?: { external_id: string; name: string; role?: string | null; model?: string | null }[];
  mcp_servers?: {
    external_id: string;
    name: string;
    transport?: string | null;
    url?: string | null;
    tools?: string[];
  }[];
  spans?: SpanInput[];
  edges?: EdgeInput[];
}
