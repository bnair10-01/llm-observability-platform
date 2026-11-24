from __future__ import annotations
import asyncio
import os
from typing import Optional
from uuid import UUID

import openai
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Evaluation, Span
from ..schemas import EvalRequest, EvalOut
from ..eval.runner import score_response
from ..eval.regression import check_regression

router = APIRouter(prefix="/eval", tags=["eval"])


def _get_client() -> openai.OpenAI:
    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@router.post("", response_model=EvalOut)
def run_eval(req: EvalRequest, db: Session = Depends(get_db)):
    span = db.query(Span).filter(Span.span_id == req.span_id).first()
    if not span:
        raise HTTPException(404, "span not found")

    result = score_response(
        response_text=req.response_text,
        user_question=req.user_question,
        retrieved_context=req.retrieved_context,
        client=_get_client(),
    )
    ev = Evaluation(span_id=req.span_id, **result)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


@router.post("/batch")
def batch_eval(
    version_id: UUID,
    baseline_version_id: Optional[UUID] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    spans = (
        db.query(Span)
        .filter(Span.version_id == version_id, Span.name == "response_complete")
        .all()
    )
    if not spans:
        raise HTTPException(404, "no spans found for this version")

    span_data = [
        {
            "span_id": s.span_id,
            "response_text": s.attributes.get("answer", ""),
            "user_question": s.attributes.get("user_question", ""),
            "retrieved_context": s.attributes.get("retrieved_context", ""),
        }
        for s in spans
    ]

    def _run():
        client = _get_client()
        db2 = next(get_db.__wrapped__()) if hasattr(get_db, "__wrapped__") else None
        from ..db import SessionLocal
        db2 = SessionLocal()
        try:
            for item in span_data:
                existing = db2.query(Evaluation).filter(
                    Evaluation.span_id == item["span_id"]
                ).first()
                if existing:
                    continue
                result = score_response(
                    client=client,
                    response_text=item["response_text"],
                    user_question=item["user_question"],
                    retrieved_context=item["retrieved_context"],
                )
                db2.add(Evaluation(span_id=item["span_id"], **result))
            db2.commit()
            if baseline_version_id:
                check_regression(
                    db2,
                    baseline_version_id=str(baseline_version_id),
                    candidate_version_id=str(version_id),
                )
        finally:
            db2.close()

    background_tasks.add_task(_run)
    return {"status": "queued", "span_count": len(spans)}
