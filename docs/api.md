# API Specification

Deliverable **#4**. Base path `/api/v1`. JSON in/out. Interactive OpenAPI docs are served
at `/docs` when the backend is running. DTOs are defined in
[`backend/app/schemas/api.py`](../backend/app/schemas/api.py).

| Method | Path | Purpose | Status |
|---|---|---|---|
| GET | `/healthz` | Liveness | ✅ MVP |
| GET | `/api/v1/schema/canonical` | Canonical envelope JSON Schema (for adapter authors) | ✅ MVP |
| POST | `/api/v1/traces:ingest` | Ingest a Canonical Trace Envelope | ✅ MVP |
| GET | `/api/v1/sessions` | List sessions (`?source=&status=&limit=`) | ✅ MVP |
| GET | `/api/v1/sessions/{id}` | Session summary + rollups | ✅ MVP |
| PATCH | `/api/v1/sessions/{id}` | Update title/status | ✅ MVP |
| DELETE | `/api/v1/sessions/{id}` | Cascade delete | ✅ MVP |
| GET | `/api/v1/sessions/{id}/graph` | DAG nodes/edges/groups (`?include_files=&include_memory=`) | ✅ MVP |
| GET | `/api/v1/sessions/{id}/timeline` | Ordered events (`?from_seq=&limit=`) | ✅ MVP |
| GET | `/api/v1/spans/{id}` | Full span detail (lazy-loaded bodies) | ✅ MVP |
| GET | `/api/v1/sessions/{id}/cost` | Cost report (total/per-agent/per-model/per-step/timeline) | ✅ MVP |
| GET | `/api/v1/sessions/{id}/diagram` | Auto Mermaid (`?type=flowchart\|sequence\|dependency\|architecture`) | ✅ MVP |
| GET | `/api/v1/compare` | Diff two runs (`?a=&b=`) | ✅ MVP |
| POST | `/api/v1/sessions/{id}/spans:append` | Streaming append for live runs | 🔜 V1 |

## Key payloads

### `POST /traces:ingest`
Request body = [Canonical Trace Envelope](canonical-schema.md). Response:
```json
{ "session_id": "uuid", "spans_ingested": 12, "edges_ingested": 12 }
```

### `GET /sessions/{id}/graph`
```jsonc
{
  "nodes": [
    { "id": "span:<uuid>", "type": "llm", "label": "claude-opus-4-8",
      "parent_id": "group:<agent-uuid>", "group": "group:<agent-uuid>",
      "data": { "kind": "llm", "status": "ok", "sequence": 1, "durationMs": 3500,
                "agentName": "main", "model": "claude-opus-4-8",
                "costUsd": 0.061, "inputTokens": 1850, "outputTokens": 420 } }
  ],
  "edges": [ { "id": "e:1", "source": "span:a", "target": "span:b", "type": "call", "label": null } ],
  "groups": [ { "id": "group:<agent-uuid>", "label": "main", "node_ids": ["span:..."] } ]
}
```
Node `type`: `agent | llm | tool | mcpTool | mcpServer | file | memory`.
Edge `type`: `call | handoff | data | mcp`. Layout (x/y) is computed client-side.

### `GET /sessions/{id}/timeline`
```jsonc
{ "items": [
  { "span_id": "uuid", "sequence": 1, "kind": "llm", "name": "claude-opus-4-8",
    "agent_name": "main", "start_time": "…", "end_time": "…", "duration_ms": 3500,
    "status": "ok",
    "preview": { "prompt": "…", "response": "…", "tool_input": null, "tool_output": null, "error": null },
    "cost": { "input_tokens": 1850, "output_tokens": 420, "cost_usd": 0.0611 } }
] }
```

### `GET /sessions/{id}/cost`
```jsonc
{
  "total": { "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0, "cost_usd": 0 },
  "per_agent": [ { "agent_id": "uuid", "name": "main", "cost_usd": 0.62, "input_tokens": 0, "output_tokens": 0 } ],
  "per_model": [ { "model": "claude-opus-4-8", "cost_usd": 0.62, "input_tokens": 0, "output_tokens": 0 } ],
  "per_step":  [ { "span_id": "uuid", "name": "…", "sequence": 1, "cost_usd": 0.06 } ],
  "timeline":  [ { "sequence": 1, "cumulative_cost_usd": 0.06 } ]
}
```

### `GET /compare?a=&b=`
```jsonc
{
  "summary": { "cost_delta_usd": -0.12, "duration_delta_ms": -3400, "span_count_delta": 0 },
  "aligned_spans": [ { "signature": "tool:2:Read", "status": "changed",
                       "a_cost_usd": null, "b_cost_usd": null, "a_duration_ms": 600, "b_duration_ms": 410 } ],
  "cost_by_agent": [ { "name": "main", "a_usd": 0.62, "b_usd": 0.50, "delta_usd": -0.12 } ]
}
```
Span alignment signature = `kind:depth:name` (run-id independent). `status` ∈
`added | removed | changed | same`.

## Errors

Standard FastAPI error envelope (`{"detail": "..."}`) with appropriate HTTP status; 404
for unknown session/span ids. RFC-7807 problem-details is a V1 polish item.
