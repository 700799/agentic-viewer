# Adapter: Claude Code (first-class)

Implemented in [`backend/app/adapters/claude_code.py`](https://github.com/700799/agentic-viewer/blob/main/backend/app/adapters/claude_code.py)
and exercised by the CLI: `agentcanvas ingest <session>.jsonl`.

## Source

Claude Code writes one JSON object per line to
`~/.claude/projects/<project>/<session-uuid>.jsonl`. Each line is a message with
`type` (`user`/`assistant`), `uuid`, `parentUuid`, `timestamp`, `sessionId`, `cwd`, and a
`message` object containing `role`, `model`, `usage`, and a `content` array of blocks
(`text`, `tool_use`, `tool_result`).

## Mapping to the canonical model

| Claude Code | Canonical |
|---|---|
| The run | `session` + a `session_root` span (`main` agent) |
| `sessionId` | `session.external_id` |
| First user text | `session.title` + the first LLM span's `prompt` IO |
| Each `assistant` turn | an `llm` span (parent = root), `attributes.model` |
| Assistant `usage` | the span's `cost` (`input_tokens`, `output_tokens`, `cache_read_input_tokens`→`cache_read_tokens`, `cache_creation_input_tokens`→`cache_write_tokens`) |
| `tool_use` block | a `tool` span (or `mcp_tool` if the name matches `mcp__<server>__<tool>`) |
| `tool_result` block | the matching tool span's `tool_output` IO + `end_time` (+ `error` if `is_error`) |
| `Read`/`NotebookRead` | a `file_read` IO with `file_path` |
| `Write`/`Edit`/`MultiEdit`/`NotebookEdit` | a `file_write` IO with `file_path` |
| `Task` tool | a child **subagent** (`agent` span) reached by a `handoff` edge |
| `mcp__<server>__<tool>` prefix | an `mcp_server` entry + `mcp_link` edge |

## Notes & limitations

- The adapter is **defensive**: every field access tolerates absence, and unknown shapes
  degrade to `custom` rather than failing the ingest.
- Tool calls are matched to their results via `tool_use.id` ↔ `tool_result.tool_use_id`.
- Subagent-internal spans are not expanded in the MVP (the `Task` result is summarized);
  expanding nested subagent transcripts is a V1 item.
