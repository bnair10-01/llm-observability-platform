from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Span
from ..schemas import SpanOut

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("", response_model=list[SpanOut])
def list_traces(
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Span).filter(Span.name == "response_complete")  # one row per RAG query
    if search:
        q = q.filter(Span.attributes["user_question"].astext.ilike(f"%{search}%"))
    return q.order_by(Span.start_time.desc()).limit(limit).all()


@router.get("/{trace_id}", response_model=list[SpanOut])
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Span)
        .filter(Span.trace_id == trace_id)
        .order_by(Span.start_time)
        .all()
    )
