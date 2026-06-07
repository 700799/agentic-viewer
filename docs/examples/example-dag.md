# Example Airflow-style DAG Rendering

Deliverable **#9**. This is the bundled `demo-refactor-auth` run rendered as a DAG. In the
app it appears on the React Flow canvas (top-to-bottom, Airflow-style); here we show the
equivalent auto-generated Mermaid (from `GET /sessions/{id}/diagram`). The Mermaid below
is the real generator output with span ids replaced by readable labels for the doc.

## Flowchart (execution DAG)

```mermaid
flowchart TD
  main[["main (agent)"]]
  llm1("LLM #1 · opus-4-8")
  read(["Read src/auth.ts"])
  llm2("LLM #2 · opus-4-8")
  mcp{{"mcp__library-docs__lookup"}}
  llm3("LLM #3 · opus-4-8")
  write(["Write src/auth.ts"])
  llm4("LLM #4 · opus-4-8")
  subagent[["test-writer (subagent)"]]
  llm5("LLM #5 · opus-4-8")
  bash(["Bash vitest"])
  llm6("LLM #6 · opus-4-8")

  main --> llm1 --> read
  main --> llm2 --> mcp
  main --> llm3 --> write
  main --> llm4 -.handoff.-> subagent
  main --> llm5 --> bash
  main --> llm6
```

The real canvas additionally renders:
- the **`library-docs` MCP server** as a service node, linked from the `mcp__…__lookup`
  tool by an orange `mcp` edge;
- a **`src/auth.ts` file node**, with a cyan `read` edge into the Read tool and a `write`
  edge out of the Write tool (data lineage);
- per-node **latency and cost badges**, and dimming of nodes past the replay cursor.

## Sequence diagram (`type=sequence`, verbatim generator output)

```mermaid
sequenceDiagram
  participant main as main
  participant test_writer as test-writer
  main->>Read: call
  Read-->>main: result
  main->>mcp__library_docs__lookup: call
  mcp__library_docs__lookup-->>main: result
  main->>Write: call
  Write-->>main: result
  main->>Bash: call
  Bash-->>main: result
```

## Dependency graph (`type=dependency`, verbatim)

```mermaid
graph LR
  f_src_auth_ts[/"src/auth.ts"/]
  main([main])
  f_src_auth_ts -->|read| main
  main -->|write| f_src_auth_ts
```

## System diagram (`type=architecture`, verbatim)

```mermaid
flowchart TB
  subgraph Agents
    a_main[["main"]]
    a_test_writer[["test-writer"]]
  end
  subgraph MCP_Servers
    s_library_docs{{"library-docs"}}
  end
  a_main --> s_library_docs
```

The source trace for this rendering is [`example-trace.json`](example-trace.json).
