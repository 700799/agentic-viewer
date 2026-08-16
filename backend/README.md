# Agent Canvas — Backend

FastAPI service for trace ingestion, storage, and the query API. See the
[repository README](../README.md) and [docs/](../docs/) for the full picture.

```bash
uv sync                 # install
uv run alembic upgrade head
uv run agentcanvas ingest app/seed/sample_claude_code.jsonl
uv run uvicorn app.main:app --reload --port 8000
```
