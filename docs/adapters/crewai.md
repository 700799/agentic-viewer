# Adapter: CrewAI (planned — V1 Phase 3)

CrewAI exposes task/agent callbacks and an event bus; the adapter subscribes to these.

## Source

`Crew.kickoff()` runs `Agent`s executing `Task`s, optionally with delegation between
agents and tool usage. Hook points: `task_callback`, `step_callback`, and CrewAI's event
bus (`@crewai_event_bus.on(...)`) for task/agent/tool/LLM events.

## Mapping

| CrewAI | Canonical |
|---|---|
| `Crew.kickoff()` | `session` (+ `session_root` span) |
| each `Agent` | an `agent` span (+ `agent` entry, `role`, `model`) |
| each `Task` | a `chain` span under its owning agent |
| tool usage | a `tool` span; input/output → IO |
| delegation between agents | a `handoff` edge (and span) |
| LLM calls | an `llm` span; usage → `cost` |

## Implementation sketch

Register event-bus listeners that build spans as tasks/tools/LLM calls fire, tracking the
active agent/task to set parents. Emit a `CanonicalEnvelope` at crew completion. Lives as
`packages/adapters/crewai/` (Python).
