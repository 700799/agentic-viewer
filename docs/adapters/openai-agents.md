# Adapter: OpenAI Agents SDK (planned — V1 Phase 3, highest priority)

The OpenAI Agents SDK already emits a trace/span model very close to ours, so this is the
easiest second adapter (near 1:1).

## Source

The SDK's tracing produces a `Trace` containing `Span`s, each with typed `span_data`:
`AgentSpanData`, `GenerationSpanData`, `FunctionSpanData`, `HandoffSpanData`,
`GuardrailSpanData`, `ResponseSpanData`. Spans nest via parent ids. Consume via a custom
`TracingProcessor`/exporter, or read exported trace JSON.

## Mapping

| OpenAI Agents | Canonical |
|---|---|
| `Trace` | `session` (+ `session_root` span) |
| `AgentSpanData` | `agent` span (+ an `agent` entry) |
| `GenerationSpanData` / `ResponseSpanData` | `llm` span; `usage` → `cost` |
| `FunctionSpanData` | `tool` span; args/result → `tool_input`/`tool_output` IO |
| `HandoffSpanData` | a `handoff` span + `handoff` edge between agents |
| `GuardrailSpanData` | `custom` span (`attributes.guardrail = …`) |
| hosted MCP tool calls | `mcp_tool` span + `mcp_server` entry |
| span parent/child | `parent_external_span_id` |

## Implementation sketch

Write a `TracingProcessor` that buffers spans for a trace and, on trace end, emits a
`CanonicalEnvelope` to `POST /api/v1/traces:ingest`. Token usage comes from the generation
/ response span usage fields. Lives as `packages/adapters/openai-agents/`.
