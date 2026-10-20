# Contributing to Agent Canvas

Thanks for your interest. Agent Canvas is designed so that **most contributions are
adapters** — a pure function that turns some framework's native trace into our
[Canonical Trace Envelope](docs/canonical-schema.md). If that's what you're here for, jump
to [Writing an adapter](#writing-an-adapter).

## Development setup

```sh
git clone https://github.com/700799/agentic-viewer.git
cd agentic-viewer

# Backend (Python, managed by uv)
make backend-install                 # uv sync --extra dev
make migrate                         # create the SQLite schema
make seed                            # ingest the bundled sample trace

# Frontend (pnpm workspace)
make frontend-install

# Auto-format and lint staged Python before each commit
git config core.hooksPath .githooks
```

Then run the two dev servers in separate shells:

```sh
make backend      # http://localhost:8000  (OpenAPI at /docs)
make frontend     # http://localhost:5173
```

Requires Python 3.11+ (CI tests 3.11 and 3.12) and Node 22+.

## Running tests

```sh
make test                              # the backend suite
cd backend && uv run pytest -q         # same thing directly
cd backend && uv run pytest tests/test_projector.py    # a single file
cd backend && uv run pytest --cov      # with coverage (needs pytest-cov)
```

Markers are registered in `backend/pyproject.toml`: tag anything that takes more than a
couple of seconds `slow`, and anything needing an optional adapter extra `optional`.
Everything runs in CI today; the markers exist so the suite can be split as it grows.

## Linting and formatting

```sh
cd backend && uv run ruff format app tests   # auto-format
cd backend && uv run ruff check app tests    # lint (enforced in CI)
pnpm --filter @agentcanvas/frontend lint     # eslint (enforced in CI)
```

The `.githooks/pre-commit` hook runs ruff format + `--fix` on staged Python files.

## Generated code

`frontend/src/types/canonical.*` is **generated** from the backend Pydantic models, and CI
fails if it drifts. After changing anything in `backend/app/schemas/canonical.py`:

```sh
make gen-types
```

Commit the regenerated files with your change.

## Writing an adapter

An adapter is a pure function `native_trace -> CanonicalEnvelope`. See
[`docs/adapters/`](docs/adapters/) for the per-framework mappings, and
`backend/app/adapters/claude_code.py` for the reference implementation.

1. Read the [canonical schema](docs/canonical-schema.md), or fetch it live from
   `GET /api/v1/schema/canonical`.
2. Map native concepts onto spans (`agent` / `llm` / `tool` / `mcp_tool` / `file_io` /
   `memory`), carry token usage into `cost`, and add `handoff` / `data_flow` edges where
   the parent/child tree alone doesn't capture the relationship.
3. Use `external_*` ids freely — the projector resolves them to internal UUIDs.
4. **Add a fixture-based contract test** (see `backend/tests/test_claude_code_adapter.py`).
   Recorded fixtures are how we defend against upstream trace-format drift.
5. If the adapter needs third-party packages, add an extra in `backend/pyproject.toml` so
   it installs as `pip install agentcanvas[yourframework]`.

Be defensive: real traces vary across versions. Tolerate missing fields and degrade to a
`custom` span rather than failing the whole ingest.

## Pull requests

- Keep each PR to a single logical change.
- Explain **why** in the commit message, not just what.
- Include a test plan: what you ran, and what you observed.
- Update the `[Unreleased]` section of [`CHANGELOG.md`](CHANGELOG.md) for user-visible changes.
- Make sure CI is green (ruff, pytest, schema-sync, eslint, build, serverless import).
- Target `main`.

## Compatibility policy

The canonical envelope is the contract everything else depends on, so it carries a
`schema_version`. Breaking changes to it:

1. Bump `schema_version` and keep the projector able to read the previous version.
2. Because every ingested envelope is retained in `raw_trace`, existing sessions can be
   re-projected rather than re-ingested.
3. Document the change in `CHANGELOG.md` and `docs/canonical-schema.md`.

Public HTTP endpoints under `/api/v1` follow the same spirit: additive changes are fine;
removals get a deprecation note in the changelog first.

## Reporting bugs and requesting features

Open a GitHub issue with enough detail to reproduce — ideally an anonymized trace file.
For security vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of filing a public
issue.
