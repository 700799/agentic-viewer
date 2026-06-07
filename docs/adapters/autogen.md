# Adapter: AutoGen (planned — V1 Phase 3)

AutoGen (AG2 / `autogen-agentchat`) is message-centric: agents converse in a group chat
and the message log is the trace.

## Source

A conversation between participating agents (e.g. `AssistantAgent`, `UserProxyAgent`,
`GroupChatManager`). Observe via message hooks / a custom `runtime` or by reading the chat
result's message history. Model-client usage is available per turn.

## Mapping

| AutoGen | Canonical |
|---|---|
| chat session / `run()` | `session` (+ `session_root` span) |
| each participating `Agent` | an `agent` span (+ `agent` entry) |
| each message turn | an `llm` span under the speaking agent; `model_client` usage → `cost` |
| tool / function execution | a `tool` span; args/result → IO |
| message routing between agents | `edge` (`handoff` / `data_flow`) |
| termination / errors | span `status` + `error` |

## Implementation sketch

Walk the message history (or subscribe to the runtime's message events), creating one LLM
span per turn attributed to the sender and tool spans for function executions, with
`data_flow`/`handoff` edges for routing. Emit the envelope when the chat ends. Lives as
`packages/adapters/autogen/` (Python).
