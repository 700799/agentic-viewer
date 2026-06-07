"""Run comparison endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from app.db.base import get_db
from app.schemas.api import CompareReport
from app.services.comparator import compare as compare_service

router = APIRouter()


@router.get("/compare", response_model=CompareReport)
def compare(a: uuid.UUID, b: uuid.UUID, db: DbSession = Depends(get_db)) -> CompareReport:
    report = compare_service(db, a, b)
    if report is None:
        raise HTTPException(status_code=404, detail="One or both sessions not found")
    return report
