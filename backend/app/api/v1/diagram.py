"""Architecture-view diagram endpoint (auto-generated Mermaid)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from app.db.base import get_db
from app.db.models import Session
from app.schemas.api import DiagramResponse
from app.services.mermaid import generate

router = APIRouter()

_VALID = {"flowchart", "sequence", "dependency", "architecture"}


@router.get("/sessions/{session_id}/diagram", response_model=DiagramResponse)
def get_diagram(
    session_id: uuid.UUID,
    type: str = Query("flowchart"),
    db: DbSession = Depends(get_db),
) -> DiagramResponse:
    if db.get(Session, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    diagram_type = type if type in _VALID else "flowchart"
    return DiagramResponse(type=diagram_type, mermaid=generate(db, session_id, diagram_type))
