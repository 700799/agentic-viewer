# Adapters

Framework adapters convert a native execution trace into a
[Canonical Trace Envelope](../../docs/canonical-schema.md) and POST it to
`/api/v1/traces:ingest`. An adapter is a pure function `native_trace → CanonicalEnvelope`.

## Status

| Adapter | Status | Location | Docs |
|---|---|---|---|
| Claude Code | ✅ implemented | [`backend/app/adapters/claude_code.py`](../../backend/app/adapters/claude_code.py) | [claude-code.md](../../docs/adapters/claude-code.md) |
| OpenAI Agents SDK | 🔜 V1 P3 | `packages/adapters/openai-agents/` | [openai-agents.md](../../docs/adapters/openai-agents.md) |
| LangGraph | 🔜 V1 P3 | `packages/adapters/langgraph/` | [langgraph.md](../../docs/adapters/langgraph.md) |
| CrewAI | 🔜 V1 P3 | `packages/adapters/crewai/` | [crewai.md](../../docs/adapters/crewai.md) |
| AutoGen | 🔜 V1 P3 | `packages/adapters/autogen/` | [autogen.md](../../docs/adapters/autogen.md) |

## Contract testing

Every adapter ships with recorded native-trace fixtures and asserts the produced envelope
against a snapshot (see `backend/tests/test_claude_code_adapter.py` for the pattern). This
is how we defend against framework trace-format drift.

## Authoring a new adapter

1. Read the canonical schema (`GET /api/v1/schema/canonical`) or
   [`@agentcanvas/shared`](../shared/src/index.ts).
2. Map native concepts onto spans (`agent`/`llm`/`tool`/`mcp_tool`/`file_io`/`memory`),
   carry token usage into `cost`, and add `handoff`/`data_flow` edges where the tree alone
   is insufficient.
3. Use `external_*` ids freely — the projector resolves them.
4. POST the envelope; re-posting the same `(source, session.external_id)` is idempotent.
