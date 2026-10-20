# Roadmap

Deliverables **#5 (MVP)** and **#6 (V1)**.

## MVP — smallest end-to-end vertical slice ✅ (this repo)

Goal: drop in a Claude Code trace and explore it as a DAG, timeline, and cost breakdown.

- [x] Monorepo scaffold (pnpm workspace + uv backend), Apache-2.0 license, Makefile.
- [x] Canonical Trace Envelope (Pydantic) — the contract.
- [x] SQLAlchemy models (`session/span/span_io/cost/error/edge/agent/mcp_server/raw_trace/model_price`) + Alembic baseline.
- [x] Idempotent projector with cost computation from a seeded price table.
- [x] **Claude Code adapter** (JSONL → envelope) + `agentcanvas ingest` CLI.
- [x] Query API: `sessions`, `traces:ingest`, `graph`, `timeline`, `spans/{id}`, `cost`, `diagram`, `compare`, `schema/canonical`.
- [x] Frontend: session sidebar, React Flow **DAG** (dagre layout, unified node, minimap, replay scrubber, search, detail drawer), **Timeline**, **Cost** (cards + bars + cumulative sparkline), **Architecture** (Mermaid, 4 types), **Compare** (deltas + structural diff).
- [x] JSON-Schema → TypeScript type generation (`make gen-types`).
- [x] Backend test suite (adapter contract, projector idempotency, services).

**Exit criterion (met):** `make seed && make backend && make frontend` → browse the bundled
run across all five views.

## V1 — phased

### Phase 1 — Canvas depth
- ELK hierarchical layout in a web worker (nested agent groups).
- Group-by-agent **collapse/expand** with edge bundling to the group node.
- Fuse.js ranked search (replace substring match); pan-to-match.
- First-class MCP/file/memory node rendering with richer affordances.
- Replay scrubber polish: play/pause, speed, keyboard stepping.

### Phase 2 — Diagrams & Compare polish
- Architecture view: Mermaid `architecture-beta` system diagrams; per-diagram options.
- Comparison: align by full path signature, highlight regressions, side-by-side canvases.
- Saved views, annotations, and shareable deep links.

### Phase 3 — More adapters
Priority by mapping ease: **OpenAI Agents SDK** (near 1:1 with the canonical spans) →
**LangGraph** (callback handler) → **CrewAI** (event bus) → **AutoGen** (message log).
Each ships with fixture-based contract tests. See [`adapters/`](adapters/claude-code.md).

### Phase 4 — Live & scale
- Streaming `POST /sessions/{id}/spans:append` + SSE/WebSocket push for live runs.
- Object store for large IO payloads (`content_ref`).
- **PostgreSQL** with JSONB indexes; verify migrations on both engines in CI.
- Auth / multi-user / projects; retention policies.
