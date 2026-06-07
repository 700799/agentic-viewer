.PHONY: help backend-install migrate seed backend test frontend-install frontend gen-types build

help:
	@echo "Agent Canvas — make targets"
	@echo "  backend-install   Install Python deps with uv"
	@echo "  migrate           Create/upgrade the database schema (alembic)"
	@echo "  seed              Ingest the bundled sample Claude Code trace"
	@echo "  backend           Run the FastAPI dev server (:8000)"
	@echo "  test              Run backend tests (pytest)"
	@echo "  gen-types         Export JSON Schema + generate frontend TS types"
	@echo "  frontend-install  Install frontend deps (pnpm)"
	@echo "  frontend          Run the Vite dev server (:5173)"

# ---- Backend ----
backend-install:
	cd backend && uv sync

migrate:
	cd backend && uv run alembic upgrade head

seed: migrate
	cd backend && uv run agentcanvas ingest app/seed/sample_claude_code.jsonl

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

test:
	cd backend && uv run pytest -q

gen-types:
	cd backend && uv run python -m app.export.jsonschema > ../frontend/src/types/canonical.schema.json
	cd frontend && pnpm run gen-types

# ---- Frontend ----
frontend-install:
	cd frontend && pnpm install

frontend:
	cd frontend && pnpm dev

build:
	cd frontend && pnpm build
