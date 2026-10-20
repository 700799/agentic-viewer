"""Snapshot the query API as static JSON files, for the GitHub Pages demo.

GitHub Pages serves static files only, so the hosted demo pre-bakes every API
response the frontend needs: this script stands up a throwaway SQLite database,
ingests the bundled sample trace, then walks the real FastAPI app with a test
client and writes each response to disk. The frontend's static mode
(``VITE_STATIC_API``) rewrites its fetch paths to match these files — see
``frontend/src/api/client.ts``; the two mappings must stay in lockstep.

File layout (query strings become dotted suffixes, everything gets ``.json``)::

    api/v1/sessions.json
    api/v1/sessions/<id>.json
    api/v1/sessions/<id>/{graph,timeline,cost}.json
    api/v1/sessions/<id>/diagram.<type>.json
    api/v1/spans/<span_id>.json

Usage: ``python -m app.export.static_api <out_dir>``
Requires the ``httpx2`` package for Starlette's TestClient.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

DIAGRAM_TYPES = ("flowchart", "sequence", "dependency", "architecture")


def main(out_dir: str) -> None:
    # Point the app at a throwaway database BEFORE importing it (config reads
    # the environment at import time).
    tmp = tempfile.mkdtemp(prefix="agentcanvas-static-")
    os.environ["AGENTCANVAS_DATABASE_URL"] = f"sqlite:///{tmp}/static.db"

    from fastapi.testclient import TestClient

    from app.adapters.claude_code import parse_jsonl
    from app.db.base import Base, SessionLocal, engine
    from app.ingest.projector import ingest_envelope
    from app.main import app

    Base.metadata.create_all(bind=engine)
    seed = Path(__file__).resolve().parents[1] / "seed" / "sample_claude_code.jsonl"
    db = SessionLocal()
    try:
        session_id, _, _ = ingest_envelope(db, parse_jsonl(seed))
    finally:
        db.close()

    client = TestClient(app)
    out = Path(out_dir)
    written = 0

    def snap(request_path: str, file_path: str) -> dict | list:
        nonlocal written
        res = client.get(request_path)
        res.raise_for_status()
        target = out / file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(res.json()))
        written += 1
        return res.json()

    sid = str(session_id)
    snap("/api/v1/sessions", "api/v1/sessions.json")
    snap(f"/api/v1/sessions/{sid}", f"api/v1/sessions/{sid}.json")
    snap(f"/api/v1/sessions/{sid}/graph", f"api/v1/sessions/{sid}/graph.json")
    timeline = snap(f"/api/v1/sessions/{sid}/timeline", f"api/v1/sessions/{sid}/timeline.json")
    snap(f"/api/v1/sessions/{sid}/cost", f"api/v1/sessions/{sid}/cost.json")
    for dtype in DIAGRAM_TYPES:
        snap(
            f"/api/v1/sessions/{sid}/diagram?type={dtype}",
            f"api/v1/sessions/{sid}/diagram.{dtype}.json",
        )
    for event in timeline["items"]:
        span_id = event["span_id"]
        snap(f"/api/v1/spans/{span_id}", f"api/v1/spans/{span_id}.json")

    print(f"Wrote {written} static API files to {out} (session {sid}).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m app.export.static_api <out_dir>")
    main(sys.argv[1])
