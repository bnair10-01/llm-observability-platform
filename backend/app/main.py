"""
FastAPI application entry point.
Sets up OpenTelemetry with a custom PostgreSQL span exporter,
registers all routers, and exposes the /query and /health endpoints.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import openai
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from sqlalchemy.orm import Session

from .db import get_db, SessionLocal, engine
from .models import Span as SpanModel
from .schemas import QueryRequest, QueryResponse
from .routers import traces, eval, versions, alerts

# ── Custom span exporter ───────────────────────────────────────────────────────

class DbSpanExporter(SpanExporter):
    """Persists completed OTel spans to PostgreSQL."""

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        db = SessionLocal()
        try:
            for s in spans:
                ctx = s.get_span_context()
                parent_id = None
                if s.parent and s.parent.span_id:
                    parent_id = format(s.parent.span_id, "016x")

                attrs = dict(s.attributes or {})
                version_id = attrs.pop("version_id", None) or None

                row = SpanModel(
                    trace_id=format(ctx.trace_id, "032x"),
                    span_id=format(ctx.span_id, "016x"),
                    parent_span_id=parent_id,
                    name=s.name,
                    start_time=datetime.fromtimestamp(s.start_time / 1e9, tz=timezone.utc),
                    end_time=datetime.fromtimestamp(s.end_time / 1e9, tz=timezone.utc) if s.end_time else None,
                    attributes=attrs,
                    status=s.status.status_code.name,
                    version_id=version_id if version_id else None,
                )
                db.merge(row)
            db.commit()
        except Exception:
            db.rollback()
            return SpanExportResult.FAILURE
        finally:
            db.close()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


# ── OTel setup ─────────────────────────────────────────────────────────────────

from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(DbSpanExporter()))
trace.set_tracer_provider(provider)

RequestsInstrumentor().instrument()

# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(title="LLM Observability Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

app.include_router(traces.router)
app.include_router(eval.router)
app.include_router(versions.router)
app.include_router(alerts.router)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)):
    from .pipeline.rag import run_pipeline

    # Resolve active prompt version
    from .models import PromptVersion
    if req.version_id:
        pv = db.query(PromptVersion).get(req.version_id)
    else:
        pv = db.query(PromptVersion).filter(PromptVersion.is_active == True).first()  # noqa: E712

    default_prompt = (
        "You are a helpful assistant. Answer based on the provided documents. "
        "Cite your sources using [Source: N] notation."
    )
    prompt_text = pv.prompt_text if pv else default_prompt
    version_id  = str(pv.version_id) if pv else None

    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    result = run_pipeline(
        question=req.question,
        version_id=version_id,
        prompt_text=prompt_text,
        openai_client=client,
    )
    return QueryResponse(**{k: result[k] for k in QueryResponse.model_fields})


# ── Overview stats endpoint ────────────────────────────────────────────────────

@app.get("/overview")
def overview(db: Session = Depends(get_db)):
    from sqlalchemy import func, text
    from .models import Evaluation

    # Latency distribution from root spans
    latencies = (
        db.query(
            SpanModel.attributes["total_latency_ms"].astext.cast(
                __import__("sqlalchemy").Float
            ).label("lat")
        )
        .filter(SpanModel.name == "response_complete")
        .order_by(SpanModel.start_time.desc())
        .limit(500)
        .all()
    )
    lats = sorted([r.lat for r in latencies if r.lat])
    p = lambda pct: lats[int(len(lats) * pct / 100) - 1] if lats else 0

    eval_row = db.query(
        func.avg(Evaluation.faithfulness).label("f"),
        func.avg(Evaluation.relevance).label("r"),
        func.avg(Evaluation.groundedness).label("g"),
    ).one()

    costs = (
        db.query(
            SpanModel.attributes["total_cost_usd"].astext.cast(
                __import__("sqlalchemy").Float
            ).label("cost")
        )
        .filter(SpanModel.name == "response_complete")
        .order_by(SpanModel.start_time.desc())
        .limit(500)
        .all()
    )
    avg_cost = sum(r.cost for r in costs if r.cost) / max(len(costs), 1)

    return {
        "p50_latency_ms":   round(p(50), 1),
        "p95_latency_ms":   round(p(95), 1),
        "p99_latency_ms":   round(p(99), 1),
        "avg_cost_usd":     round(avg_cost, 6),
        "avg_faithfulness": round(float(eval_row.f or 0), 2),
        "avg_relevance":    round(float(eval_row.r or 0), 2),
        "avg_groundedness": round(float(eval_row.g or 0), 2),
        "total_traces":     len(lats),
    }


@app.get("/quality-trends")
def quality_trends(days: int = 7, db: Session = Depends(get_db)):
    from sqlalchemy import func, cast, Date
    from .models import Evaluation

    rows = (
        db.query(
            cast(Evaluation.eval_timestamp, Date).label("day"),
            func.avg(Evaluation.faithfulness).label("faithfulness"),
            func.avg(Evaluation.relevance).label("relevance"),
            func.avg(Evaluation.groundedness).label("groundedness"),
            func.count(Evaluation.id).label("count"),
        )
        .group_by("day")
        .order_by("day")
        .limit(days)
        .all()
    )
    return [
        {
            "day": str(r.day),
            "faithfulness":  round(float(r.faithfulness or 0), 2),
            "relevance":     round(float(r.relevance or 0), 2),
            "groundedness":  round(float(r.groundedness or 0), 2),
            "count":         r.count,
        }
        for r in rows
    ]
