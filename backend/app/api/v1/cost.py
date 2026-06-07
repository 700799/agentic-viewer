"""Cost report endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from app.db.base import get_db
from app.db.models import Session
from app.schemas.api import CostReport
from app.services.cost_aggregator import build_cost_report

router = APIRouter()


@router.get("/sessions/{session_id}/cost", response_model=CostReport)
def get_cost(session_id: uuid.UUID, db: DbSession = Depends(get_db)) -> CostReport:
    if db.get(Session, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_cost_report(db, session_id)
