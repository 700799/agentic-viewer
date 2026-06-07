# Adapter: LangGraph (planned — V1 Phase 3)

LangGraph runs on LangChain's callback system plus its own graph/state semantics, so the
adapter is a callback handler that knows about nodes and edges.

## Source

A `BaseCallbackHandler` (LangChain) receives `on_chain_start/end`, `on_llm_end`,
`on_tool_start/end`, `on_chain_error`, etc., each with a `run_id`/`parent_run_id`. Wrap
the compiled graph so node names and conditional-edge transitions are observable.

## Mapping

| LangGraph / LangChain | Canonical |
|---|---|
| graph invocation | `session` (+ `session_root` span) |
| each node execution | a `chain` (or `agent`) span; parent = the graph/run |
| `on_llm_end` token usage | an `llm` span + `cost` |
| `on_tool_start/end` | a `tool` span; input/output → IO |
| conditional / state-transition edges | `edge` (`data_flow`) between node spans |
| state channel read/write | `memory_read` / `memory_write` IO |
| `run_id` / `parent_run_id` | `external_span_id` / `parent_external_span_id` |

## Implementation sketch

A `CanonicalTraceCallback(BaseCallbackHandler)` accumulates spans keyed by `run_id`; a
thin graph wrapper records node→node transitions as `data_flow` edges. On completion, emit
the envelope to the ingest endpoint. Lives as `packages/adapters/langgraph/` (Python).
