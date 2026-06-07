# Agent Canvas

> A visual, Airflow-style canvas for observing Claude Code and AI-agent workflows.

Agent Canvas ingests execution traces from agent frameworks, normalizes them into a
single canonical span model, and renders them as an interactive DAG, a step-by-step
timeline, a cost breakdown, and auto-generated architecture diagrams.

## Why

Agentic runs are hard to observe. A Claude Code session fans out into subagents, tool
calls, MCP servers, file reads/writes, and memory operations — each with its own latency
and token cost. Logs flatten all of that into a scroll. **Agent Canvas turns a run into a
graph you can zoom, replay, and cost out.**

## Features

| View | What it shows |
|------|---------------|
| **DAG** | Agents as nodes, tool calls as child nodes, MCP servers as connected services, files read/written, memory ops, execution order. Infinite zoom, pan/drag, grouping, collapse, search. |
| **Timeline** | Step-by-step replay: prompts, tool invocations, outputs, errors, latency. |
| **Cost** | Token usage, cost per step, cost per agent, total session cost. |
| **Architecture** | Auto-generated Mermaid flowchart / sequence / dependency / system diagrams. |
| **Compare** | Diff two runs by structure, cost, and latency. |

## Architecture at a glance

```
[Agent run] → [Adapter] → Canonical Trace Envelope (JSON)
   → POST /api/v1/traces:ingest → [Projector] → SQLite/Postgres
   → Query API (/graph /timeline /cost /diagram /compare)
   → React + React Flow + Mermaid frontend
```

The keystone is an **OpenTelemetry-GenAI-inspired span model**: every agent, LLM call,
tool call, file I/O, and memory op is a `span` with a `span_kind`. Every framework
adapter reduces to "emit spans," so the rest of the system is framework-agnostic.

See [`docs/architecture.md`](docs/architecture.md) for the full design.

## Quick start

```bash
# 1. Backend (FastAPI + SQLite)
make backend-install
make migrate          # create the SQLite schema
make seed             # ingest the bundled sample Claude Code trace
make backend          # http://localhost:8000  (OpenAPI at /docs)

# 2. Frontend (Vite + React)
make frontend-install
make frontend         # http://localhost:5173
```

Or ingest your own Claude Code session:

```bash
cd backend
uv run agentcanvas ingest ~/.claude/projects/<project>/<session>.jsonl
```

## Integrations

First-class: **Claude Code** (JSONL transcripts). Documented adapter mappings for
**OpenAI Agents SDK**, **LangGraph**, **CrewAI**, and **AutoGen** — see
[`docs/adapters/`](docs/adapters/).

## Repository layout

```
backend/    FastAPI app, SQLAlchemy models, projector, Claude Code adapter, CLI
frontend/   React + TypeScript + React Flow + Mermaid
packages/   shared canonical types (TS) + adapter stubs
docs/        architecture, schema, API, roadmaps, screenshots, examples
```

## Documentation

- [Architecture](docs/architecture.md)
- [Canonical trace schema](docs/canonical-schema.md)
- [Database schema](docs/database.md)
- [API specification](docs/api.md)
- [Roadmap (MVP + V1)](docs/roadmap.md)
- [Screenshots (described)](docs/screenshots.md)
- [Example trace](docs/examples/example-trace.json) · [Example DAG](docs/examples/example-dag.md)
- [License rationale](docs/license.md)

## License

[Apache-2.0](LICENSE).
