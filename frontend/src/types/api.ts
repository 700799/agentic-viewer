// API read-model types (mirror backend app/schemas/api.py).
// The canonical ingestion types live in canonical.ts (generated from JSON Schema).

export interface SessionSummary {
  id: string;
  external_id: string;
  source: string;
  title: string | null;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  span_count: number;
  meta: Record<string, unknown>;
}

export interface SessionList {
  items: SessionSummary[];
  next_cursor: string | null;
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  parent_id: string | null;
  group: string | null;
  data: {
    kind?: string;
    status?: string;
    sequence?: number;
    durationMs?: number | null;
    agentName?: string | null;
    model?: string | null;
    costUsd?: number | null;
    inputTokens?: number | null;
    outputTokens?: number | null;
    path?: string;
    transport?: string | null;
    tools?: string[];
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label: string | null;
}

export interface GroupInfo {
  id: string;
  label: string;
  node_ids: string[];
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  groups: GroupInfo[];
}

export interface TimelinePreview {
  prompt?: string | null;
  response?: string | null;
  tool_input?: string | null;
  tool_output?: string | null;
  error?: string | null;
}

export interface TimelineCost {
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

export interface TimelineEvent {
  span_id: string;
  sequence: number;
  kind: string;
  name: string;
  agent_name: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_ms: number | null;
  status: string;
  preview: TimelinePreview;
  cost: TimelineCost | null;
}

export interface TimelineResponse {
  items: TimelineEvent[];
}

export interface SpanIODetail {
  io_type: string;
  role: string | null;
  content_text: string | null;
  file_path: string | null;
  byte_size: number | null;
  truncated: boolean;
}

export interface SpanDetail {
  id: string;
  external_span_id: string;
  kind: string;
  name: string;
  agent_name: string | null;
  status: string;
  start_time: string | null;
  end_time: string | null;
  duration_ms: number | null;
  attributes: Record<string, unknown>;
  io: SpanIODetail[];
  cost: TimelineCost | null;
  error: string | null;
}

export interface CostReport {
  total: {
    input_tokens: number;
    output_tokens: number;
    cache_read_tokens: number;
    cache_write_tokens: number;
    cost_usd: number;
  };
  per_agent: { agent_id: string | null; name: string; cost_usd: number; input_tokens: number; output_tokens: number }[];
  per_model: { model: string; cost_usd: number; input_tokens: number; output_tokens: number }[];
  per_step: { span_id: string; name: string; sequence: number; cost_usd: number }[];
  timeline: { sequence: number; cumulative_cost_usd: number }[];
}

export interface DiagramResponse {
  type: string;
  mermaid: string;
}

export interface CompareReport {
  summary: { cost_delta_usd: number; duration_delta_ms: number; span_count_delta: number };
  aligned_spans: {
    signature: string;
    status: string;
    a_cost_usd: number | null;
    b_cost_usd: number | null;
    a_duration_ms: number | null;
    b_duration_ms: number | null;
  }[];
  cost_by_agent: { name: string; a_usd: number; b_usd: number; delta_usd: number }[];
}
