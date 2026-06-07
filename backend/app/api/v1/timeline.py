"""Timeline + span detail endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from app.db.base import get_db
from app.db.models import Session
from app.schemas.api import SpanDetail, TimelineResponse
from app.services.timeline import build_span_detail, build_timeline

router = APIRouter()


@router.get("/sessions/{session_id}/timeline", response_model=TimelineResponse)
def get_timeline(
    session_id: uuid.UUID,
    from_seq: int = 0,
    limit: int = Query(1000, le=5000),
    db: DbSession = Depends(get_db),
) -> TimelineResponse:
    if db.get(Session, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_timeline(db, session_id, from_seq=from_seq, limit=limit)


@router.get("/spans/{span_id}", response_model=SpanDetail)
def get_span(span_id: uuid.UUID, db: DbSession = Depends(get_db)) -> SpanDetail:
    detail = build_span_detail(db, span_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Span not found")
    return detail
