"""Session CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.db.base import get_db
from app.db.models import Session
from app.schemas.api import SessionList, SessionPatch, SessionSummary

router = APIRouter()


def _to_summary(s: Session) -> SessionSummary:
    return SessionSummary(
        id=s.id,
        external_id=s.external_id,
        source=s.source,
        title=s.title,
        status=s.status,
        started_at=s.started_at,
        ended_at=s.ended_at,
        total_cost_usd=float(s.total_cost_usd),
        total_input_tokens=s.total_input_tokens,
        total_output_tokens=s.total_output_tokens,
        span_count=s.span_count,
        meta=s.meta or {},
    )


@router.get("/sessions", response_model=SessionList)
def list_sessions(
    source: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=200),
    db: DbSession = Depends(get_db),
) -> SessionList:
    stmt = select(Session).order_by(Session.started_at.desc().nullslast())
    if source:
        stmt = stmt.where(Session.source == source)
    if status:
        stmt = stmt.where(Session.status == status)
    rows = list(db.scalars(stmt.limit(limit)))
    return SessionList(items=[_to_summary(s) for s in rows])


@router.get("/sessions/{session_id}", response_model=SessionSummary)
def get_session(session_id: uuid.UUID, db: DbSession = Depends(get_db)) -> SessionSummary:
    s = db.get(Session, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_summary(s)


@router.patch("/sessions/{session_id}", response_model=SessionSummary)
def patch_session(
    session_id: uuid.UUID, patch: SessionPatch, db: DbSession = Depends(get_db)
) -> SessionSummary:
    s = db.get(Session, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if patch.title is not None:
        s.title = patch.title
    if patch.status is not None:
        s.status = patch.status
    db.commit()
    return _to_summary(s)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: uuid.UUID, db: DbSession = Depends(get_db)) -> None:
    s = db.get(Session, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(s)
    db.commit()
