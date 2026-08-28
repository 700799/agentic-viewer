# Database Schema

Deliverable **#3**. Implemented in
[`backend/app/db/models/entities.py`](https://github.com/700799/agentic-viewer/blob/main/backend/app/db/models/entities.py); the baseline
Alembic migration lives in `backend/alembic/versions/`.

The spine is the **`span`** table. Dimension tables (`agent`, `mcp_server`) and side
tables (`span_io`, `cost`, `error`, `edge`) reference it. `raw_trace` keeps the original
envelope; `model_price` is reference data.

## Entity-relationship overview

```
session 1───* span ───┐
   │                   ├─1 cost
   │                   ├─0..1 error
   │                   └─* span_io
   ├───* agent  ◄──────┘ (span.agent_id)
   ├───* mcp_server ◄── (span.mcp_server_id)
   ├───* edge (source_span_id, target_span_id → span)
   └───* raw_trace
model_price (reference, keyed by model)
```

## Tables

### `session`
`id` (UUID PK) · `external_id` · `source` · `title` · `status` · `started_at` ·
`ended_at` · `total_cost_usd` (Numeric) · `total_input_tokens` · `total_output_tokens` ·
`span_count` · `meta` (JSON) · `created_at`.
**Indexes:** unique `(source, external_id)`; `(started_at)`.
Rollup columns are denormalized for fast session-list rendering.

### `span` — the spine
`id` (UUID PK) · `session_id` (FK→session, CASCADE) · `external_span_id` ·
`parent_span_id` (FK→span, CASCADE) · `span_kind` · `name` · `agent_id` (FK→agent) ·
`mcp_server_id` (FK→mcp_server) · `status` · `start_time` · `end_time` · `duration_ms` ·
`sequence` (global order) · `depth` (tree level) · `attributes` (JSON).
**Indexes:** unique `(session_id, external_span_id)`; `(session_id, sequence)`;
`(session_id, span_kind)`; `(parent_span_id)`; `(agent_id)`.

### `agent`
`id` · `session_id` (FK) · `external_id` · `name` · `role` · `model` · `meta`.
Unique `(session_id, name)`.

### `mcp_server`
`id` · `session_id` (FK) · `external_id` · `name` · `transport` (stdio/http/sse) · `url`
· `tools` (JSON) · `meta`. Unique `(session_id, name)`.

### `span_io` — prompts, responses, tool I/O, file I/O, memory ops
`id` · `span_id` (FK, CASCADE) · `io_type` · `role` · `content_text` ·
`content_ref` (object-store key, V1) · `file_path` · `byte_size` · `truncated` · `meta`.
**Indexes:** `(span_id, io_type)`; `(file_path)` — answers "which spans touched this file".
Text payloads live here (not on `span`) so they can be lazy-loaded.

### `cost`
`id` · `span_id` (FK) · `session_id` (FK, denormalized) · `agent_id` (FK, denormalized) ·
`model` · `input_tokens` · `output_tokens` · `cache_read_tokens` · `cache_write_tokens` ·
`cost_usd` (Numeric) · `estimated` (bool).
**Indexes:** `(session_id)`; `(agent_id)`; `(model)`. Denormalized FKs make rollups single
-table `GROUP BY`s.

### `error`
`id` · `span_id` (FK) · `session_id` (FK) · `error_type` · `message` · `stack` · `meta`.
Index `(session_id)`.

### `edge` — explicit relationships beyond parent/child
`id` · `session_id` (FK) · `source_span_id` (FK) · `target_span_id` (FK) · `edge_kind`
(call/handoff/data_flow/mcp_link/file_dep/memory_dep) · `label` · `meta`.
**Indexes:** `(session_id, edge_kind)`; `(source_span_id)`; `(target_span_id)`.

### `raw_trace` — append-only re-projection source
`id` · `session_id` (FK) · `source` · `schema_version` · `payload` (JSON) · `received_at`.

### `model_price` — reference
`model` (PK) · `input_per_mtok` · `output_per_mtok` · `cache_read_per_mtok` ·
`cache_write_per_mtok`. (USD per million tokens.)

## Portability notes

`Uuid` → native UUID (Postgres) / CHAR(32) (SQLite). `JSON` → JSONB (Postgres) / text
(SQLite). `Numeric` for money; `DateTime(timezone=True)` for timestamps. Query-critical
fields are real columns so identical indexes/queries serve both engines. Switch databases
by changing `AGENTCANVAS_DATABASE_URL`; migrations are engine-portable.
