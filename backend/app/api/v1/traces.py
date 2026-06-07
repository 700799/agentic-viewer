"""Trace ingestion endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.db.base import get_db
from app.ingest.projector import ingest_envelope
from app.schemas.api import IngestResult
from app.schemas.canonical import CanonicalEnvelope

router = APIRouter()


@router.post("/traces:ingest", response_model=IngestResult)
def ingest(envelope: CanonicalEnvelope, db: DbSession = Depends(get_db)) -> IngestResult:
    session_id, spans, edges = ingest_envelope(db, envelope)
    return IngestResult(session_id=session_id, spans_ingested=spans, edges_ingested=edges)
