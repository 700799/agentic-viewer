"""DAG graph endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from app.db.base import get_db
from app.db.models import Session
from app.schemas.api import GraphResponse
from app.services.graph_builder import build_graph

router = APIRouter()


@router.get("/sessions/{session_id}/graph", response_model=GraphResponse)
def get_graph(
    session_id: uuid.UUID,
    include_files: bool = True,
    include_memory: bool = True,
    db: DbSession = Depends(get_db),
) -> GraphResponse:
    if db.get(Session, session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_graph(db, session_id, include_files=include_files, include_memory=include_memory)
