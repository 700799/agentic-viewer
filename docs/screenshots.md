# Sample Screenshots (described)

Deliverable **#7**. Detailed descriptions of each view as implemented, using the bundled
`demo-refactor-auth` session ("Refactor the auth module to use JWT and add tests"). The UI
is a dark theme (GitHub-dark palette) with a fixed 280px left sidebar and a tabbed main
area.

## Global layout

```
┌────────────┬──────────────────────────────────────────────────────────────┐
│ ▦ Agent    │  [DAG] [Timeline] [Cost] [Architecture] [Compare]   ● legend  │
│   Canvas   │ ┌──────────────────────────────────────────────────────────┐ │
│            │ │                                                          │ │
│ ▸ Refactor │ │                  active view renders here                │ │
│   the auth │ │                                                          │ │
│   [claude] │ │                                                          │ │
│   12 spans │ └──────────────────────────────────────────────────────────┘ │
│   $0.6279  │                                                              │
└────────────┴──────────────────────────────────────────────────────────────┘
```

The sidebar lists sessions; each row shows the title, a source badge (`claude_code`),
span count, and total cost. The active session has a blue left-border. A color legend
(Agent / LLM / Tool / MCP / File / Memory) sits top-right of every view.

## 1. DAG view

An infinite, pannable React Flow canvas (Airflow-style top-to-bottom flow). For the demo
run you see, from the top:

- A **`main` agent** node (amber border) as the root.
- Six **LLM** nodes (purple) in sequence — one per assistant turn — each showing the model
  `claude-opus-4-8`, latency (e.g. `3.5s`), and cost (e.g. `$0.0611`).
- Branching off the LLM turns: **Tool** nodes (green, `Read`, `Write`, `Bash`), an
  **MCP tool** node (orange, `mcp__library-docs__lookup`) linked by an orange edge to an
  **MCP server** node (`library-docs`), an **agent/subagent** node (`test-writer`, reached
  by a dashed amber *handoff* edge), and **File** nodes (cyan, `auth.ts`) connected by
  dashed *data* edges labeled `read` / `write`.
- Edge styles encode relationship: solid grey animated = `call`, dashed amber = `handoff`,
  dashed cyan = `data`, solid orange = `mcp`. Arrowheads show direction / execution order.

Controls: bottom-left zoom/fit controls; a **minimap** bottom-right (nodes colored by
kind, viewport mask). Top-left a **search box** — typing `auth` outlines matching nodes in
amber. Clicking any node opens the **span detail drawer** (right): status, agent, latency,
token usage, cost, and each IO block (prompt / response / tool input / tool output / file
path / error) plus the raw attributes JSON.

A **replay bar** spans the bottom: a "▶ Replay" toggle and a slider ("step 4 / 11"); as
you scrub, nodes beyond the cursor dim to 25% opacity so you watch execution build up.

## 2. Timeline view

A vertical, scrollable list of every span ordered by `sequence`. Each row is a 4-column
grid:

```
#1   LLM        claude-opus-4-8 · @main                       3500 ms
                response: I'll start by reading the current…   $0.0611
                                                               1850/420 tok
#2   TOOL       Read                                            600 ms
                input: {"file_path":"src/auth.ts"}
#3   MCP_TOOL   mcp__library-docs__lookup                       …
                output: jwt.sign(payload, secret, …)
```

Column 1 = sequence; column 2 = kind (color-coded); column 3 = name + agent + the most
relevant truncated snippet (prompt/response/tool I/O, errors in red); column 4 = latency,
cost, and token counts. The replay cursor from the DAG view dims future rows here too.
Clicking a row opens the same detail drawer.

## 3. Cost view

Top: four **summary cards** — Total cost (`$0.6279`), Input tokens, Output tokens, Cache
read tokens.

Below, a **cumulative-cost sparkline** (filled purple area chart) showing cost
accumulating across execution steps.

Then three horizontal **bar-chart sections**, each bar normalized to the max:
- **Cost per agent** (`main` …).
- **Cost per model** (`claude-opus-4-8` …).
- **Cost per step** (`#1 claude-opus-4-8`, `#3 …`), with the dollar value on the right.

## 4. Architecture view

A type switcher (Flowchart / Sequence / Dependencies / System) and a "Copy Mermaid"
button. The selected diagram renders (Mermaid dark theme) inside a bordered panel, and the
**generated Mermaid source** is shown below in a code block:

- **Flowchart** — the span tree (agents `[[…]]`, LLMs `(…)`, tools `([…])`, MCP `{{…}}`).
- **Sequence** — agents/MCP servers as participants with call→result messages.
- **Dependencies** — files ⇄ agents derived from file reads/writes.
- **System** — agents and MCP servers grouped in subgraphs with usage links.

## 5. Compare view

Base run (A) is the selected session; a dropdown picks run B. Three **delta cards**
(Cost Δ, Duration Δ, Span count Δ) color regressions red and improvements green. Below:
a **Cost-by-agent** table (A $, B $, Δ) and a **Structural diff** table listing aligned
span signatures with status (`added`/`removed`/`changed`/`same`) and per-run latencies.
