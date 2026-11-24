from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PromptVersion, Evaluation, Span
from ..schemas import PromptVersionIn, PromptVersionOut

router = APIRouter(prefix="/prompt-versions", tags=["versions"])


@router.get("", response_model=list[PromptVersionOut])
def list_versions(db: Session = Depends(get_db)):
    return db.query(PromptVersion).order_by(PromptVersion.created_at.desc()).all()


@router.post("", response_model=PromptVersionOut, status_code=201)
def create_version(body: PromptVersionIn, db: Session = Depends(get_db)):
    v = PromptVersion(**body.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.get("/{version_id}/stats")
def version_stats(version_id: UUID, db: Session = Depends(get_db)):
    v = db.query(PromptVersion).get(version_id)
    if not v:
        raise HTTPException(404, "version not found")
    row = (
        db.query(
            func.avg(Evaluation.faithfulness).label("faithfulness"),
            func.avg(Evaluation.relevance).label("relevance"),
            func.avg(Evaluation.groundedness).label("groundedness"),
            func.count(Evaluation.id).label("eval_count"),
        )
        .join(Span, Span.span_id == Evaluation.span_id)
        .filter(Span.version_id == str(version_id))
        .one()
    )
    return {
        "version_id": str(version_id),
        "faithfulness":  round(float(row.faithfulness or 0), 2),
        "relevance":     round(float(row.relevance or 0), 2),
        "groundedness":  round(float(row.groundedness or 0), 2),
        "eval_count":    row.eval_count,
    }
