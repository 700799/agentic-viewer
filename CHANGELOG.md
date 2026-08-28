# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Vercel deployment: static frontend plus the FastAPI backend as a Python serverless
  function that self-seeds a demo trace on cold start.
- PyPI packaging metadata and per-framework adapter extras, so adapters install as
  `pip install agentcanvas[langgraph]`.
- Release workflow publishing to PyPI via Trusted Publishing (OIDC) on `v*` tags.
- Documentation site built with MkDocs Material and deployed to GitHub Pages.
- Project scaffolding: `CONTRIBUTING.md`, `SECURITY.md`, `NOTICE`, a pre-commit hook
  under `.githooks/`, and Dependabot configuration.
- CI: a `serverless` job that imports the Vercel entrypoint from a clean install of
  `requirements.txt`, an eslint step, and a Python 3.11/3.12 matrix.

### Fixed
- `AppShell` set state inside an effect to pick a default session, causing a cascading
  re-render on load; the value is now derived.
- The frontend `lint` script invoked eslint, which was never a dependency — so it failed
  on every run. ESLint and a flat config are now installed and enforced in CI.
- Removed an `any` cast in the DAG minimap and a ternary-as-statement in the canvas store.
- `backend/pyproject.toml` pointed `readme` at `../README.md`, which broke builds outside
  the repository root.

## [0.1.0] — 2026-06-07

Initial release: the MVP vertical slice.

### Added
- Canonical Trace Envelope — an OpenTelemetry-GenAI-inspired span model that every
  framework adapter targets.
- SQLite/PostgreSQL-portable schema with an append-only `raw_trace` table, enabling
  re-projection when the schema evolves.
- Idempotent projector with cost computation from a model price table.
- Claude Code adapter (JSONL transcripts) and the `agentcanvas` CLI.
- Query API: sessions, trace ingestion, DAG graph, timeline, span detail, cost report,
  Mermaid diagram generation, and run comparison.
- React frontend with DAG, Timeline, Cost, Architecture, and Compare views.
- Documentation covering architecture, schema, API, roadmap, and adapter mappings.

[Unreleased]: https://github.com/700799/agentic-viewer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/700799/agentic-viewer/releases/tag/v0.1.0
