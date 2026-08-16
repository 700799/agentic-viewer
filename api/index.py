"""Vercel serverless entrypoint for the Agent Canvas API.

Vercel's Python runtime serves this module's ``app`` (ASGI) for every request
rewritten to /api/*. The serverless filesystem is read-only except /tmp, so on
cold start we point SQLite at /tmp and self-seed the demo database from the
bundled sample Claude Code trace. Writes don't persist across instances — fine
for a read-mostly demo.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

DB_PATH = "/tmp/agentcanvas.db"
os.environ.setdefault("AGENTCANVAS_DATABASE_URL", f"sqlite:///{DB_PATH}")

from app.db.base import Base, SessionLocal, engine  # noqa: E402
from app.main import app as app  # noqa: E402  (re-exported for Vercel)


def _seed_if_empty() -> None:
    Base.metadata.create_all(bind=engine)
    from app.adapters.claude_code import parse_jsonl
    from app.db.models import Session
    from app.ingest.projector import ingest_envelope

    db = SessionLocal()
    try:
        if db.query(Session).count() == 0:
            sample = ROOT / "backend" / "app" / "seed" / "sample_claude_code.jsonl"
            if sample.exists():
                ingest_envelope(db, parse_jsonl(sample))
    finally:
        db.close()


_seed_if_empty()
