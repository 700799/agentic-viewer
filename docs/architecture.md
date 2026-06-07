# Agent Canvas — Architecture

Agent Canvas is an observability and replay tool for agentic runs. It ingests execution
traces from agent frameworks, normalizes them into one canonical span model, persists
them, and renders DAG / Timeline / Cost / Architecture / Compare views.

This document is deliverable **#1 (Complete architecture)**.

## 1. Design stance

| Decision | Choice | Why |
|---|---|---|
| Canonical model | OpenTelemetry-GenAI-inspired **span** with a `span_kind` | Every framework reduces to "emit spans"; the rest of the system is framework-agnostic |
| Storage | Raw envelope **+** projected tables | Re-project when the schema evolves without re-ingesting |
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic | Portable generic column types run on SQLite (MVP) and Postgres (later) unchanged |
| Frontend state | **Zustand** (canvas/replay) + **TanStack Query** (server) | Fast transient interaction state vs. cached server state, cleanly separated |
| Layout | **dagre** (MVP, flat) → **ELK** (V1, nested/grouped) | dagre is fast for first paint; ELK does hierarchical grouping |
| Type contract | Pydantic → JSON Schema → generated TS | Single source of truth; backend and frontend never drift |

## 2. Data flow

```
[Agent run]
  │  native trace (Claude Code JSONL, OpenAI Agents spans, LangGraph callbacks, …)
  ▼
[Adapter]  pure function: native_trace -> CanonicalEnvelope
  │
  ▼
POST /api/v1/traces:ingest   (or the `agentcanvas ingest` CLI)
  │
  ▼
[Projector]  validate (Pydantic) → resolve external ids → write rows (one txn)
  │            • idempotent on (session_id, external_span_id)
  │            • computes sequence, depth, duration_ms, cost_usd
  ▼
[Storage]  SQLite / Postgres
  │   raw_trace (append-only)  +  session / span / span_io / cost / error / edge / agent / mcp_server
  ▼
[Query API]  /sessions  /graph  /timeline  /cost  /diagram  /compare
  │   graph_builder · cost_aggregator · timeline · mermaid · comparator
  ▼
[Frontend]  React + React Flow + Mermaid
      DAG │ Timeline │ Cost │ Architecture │ Compare
```

## 3. Backend components

- **Adapters** (`app/adapters/`) — one per framework. Pure, unit-tested against recorded
  fixtures. The Claude Code adapter (`claude_code.py`) is first-class; the others are
  documented in [`docs/adapters/`](adapters/).
- **Projector** (`app/ingest/projector.py`) — the only writer of projected tables.
  Idempotent: re-ingesting an envelope replaces the session's projection rather than
  duplicating it. Resolves `external_*` ids to internal UUIDs, computes `sequence`
  (global order), `depth` (tree level), `duration_ms`, and `cost_usd`.
- **Pricing** (`app/ingest/pricing.py`) — `model_price` table seed + cost computation;
  flags `estimated=True` when a model price is unknown.
- **Services** (`app/services/`):
  - `graph_builder` — spans+edges+IO → logical DAG (`{nodes, edges, groups}`); layout is
    computed client-side, so the backend stays layout-agnostic. Derives file/memory nodes
    from span IO.
  - `cost_aggregator` — SQL `GROUP BY` rollups: total, per-agent, per-model, per-step,
    cumulative timeline.
  - `timeline` — ordered events with truncated previews + full span detail (lazy-loaded).
  - `mermaid` — deterministic span-tree → Mermaid (flowchart / sequence / dependency /
    architecture). No LLM required.
  - `comparator` — aligns two runs by structural span signature and diffs cost/latency.

## 4. Why raw + projected

Adapters and framework trace formats change often. Storing the original envelope in
`raw_trace` (with a `schema_version`) means a schema upgrade is "add a migration + replay
the projector," not "re-run every agent." The projected tables are denormalized and
indexed for fast reads; the raw table is the durable source of truth.

## 5. Frontend structure

```
src/
  api/        TanStack Query hooks + fetch client (stable query keys)
  store/      Zustand: selectedSpanId, replayCursor, highlightIds, collapsedGroups
  features/
    dag/         React Flow canvas, unified CanvasNode, dagre layout, replay scrubber
    timeline/    ordered event list synced to the same replay cursor
    cost/        cards + bar charts + cumulative sparkline (dependency-free SVG)
    architecture/ Mermaid render + type switch + copy-source
    compare/     two-run picker, summary deltas, structural diff table
    sessions/    session sidebar
  components/  SpanDetailDrawer, SearchBar (shared across DAG + Timeline)
  types/       api.ts (read DTOs) + canonical.ts (generated from JSON Schema)
```

The **DAG and Timeline share one replay cursor** in Zustand: scrubbing the timeline dims
not-yet-reached nodes on the canvas and vice-versa.

## 6. Portability (SQLite → Postgres)

Models use SQLAlchemy generic types: `Uuid` (native UUID on PG, CHAR on SQLite), `JSON`
(JSONB on PG), `Numeric` for money, timezone-aware `DateTime`. Query-critical attributes
(`span_kind`, `agent_id`, cost columns, `file_path`) are **real columns**, not JSON keys,
so the same indexes and queries work on both engines. Alembic migrations target both;
`render_as_batch=True` enables SQLite ALTERs.

## 7. Key risks & mitigations

| Risk | Mitigation |
|---|---|
| Adapter drift (formats change) | `raw_trace` + `schema_version` + fixture contract tests per adapter |
| Token/cost accuracy varies | `model_price` table with compute-at-ingest; `estimated` flag when unknown |
| Large traces / payloads | Truncate inline text (`max_inline_content_chars`), `content_ref` for blobs (V1), paginated timeline, lazy span detail |
| Layout quality vs. perf | dagre flat (MVP) → ELK hierarchical in a worker (V1); collapse-by-default for big graphs |
| Canonical model leakage | `attributes` JSON escape hatch + `kind:custom`; `raw_trace` never drops data |
| Pydantic ↔ TS drift | TS generated from Pydantic JSON Schema (`make gen-types`) |

See also: [canonical schema](canonical-schema.md) · [database](database.md) ·
[API](api.md) · [roadmap](roadmap.md).
