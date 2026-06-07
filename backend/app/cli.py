"""``agentcanvas`` command-line interface.

Examples::

    agentcanvas ingest session.jsonl              # ingest a Claude Code transcript
    agentcanvas ingest envelope.json --canonical  # ingest a canonical envelope
    agentcanvas init-db                           # create tables (dev shortcut)
    agentcanvas sessions                          # list ingested sessions
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from app.adapters.claude_code import parse_jsonl
from app.db.base import Base, SessionLocal, engine
from app.ingest.projector import ingest_envelope
from app.schemas.canonical import CanonicalEnvelope

app = typer.Typer(help="Agent Canvas CLI")


@app.command()
def init_db() -> None:
    """Create all tables directly (use alembic migrations in production)."""
    Base.metadata.create_all(bind=engine)
    typer.echo("Database initialized.")


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Path to a Claude Code .jsonl or canonical .json"),
    canonical: bool = typer.Option(False, help="Treat the file as a canonical envelope"),
) -> None:
    """Ingest a trace file into the database."""
    if canonical or path.suffix == ".json":
        envelope = CanonicalEnvelope.model_validate(json.loads(path.read_text()))
    else:
        envelope = parse_jsonl(path)

    db = SessionLocal()
    try:
        session_id, spans, edges = ingest_envelope(db, envelope)
    finally:
        db.close()
    typer.echo(f"Ingested session {session_id}: {spans} spans, {edges} edges.")


@app.command()
def sessions() -> None:
    """List ingested sessions."""
    from app.db.models import Session as Sess

    db = SessionLocal()
    try:
        rows = db.query(Sess).order_by(Sess.created_at.desc()).all()
        for s in rows:
            typer.echo(
                f"{s.id}  [{s.source}]  {s.title or s.external_id}  "
                f"spans={s.span_count}  ${float(s.total_cost_usd):.4f}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    app()
