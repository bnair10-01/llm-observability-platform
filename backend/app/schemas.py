from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class SpanOut(BaseModel):
    id: int
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: datetime
    end_time: Optional[datetime]
    attributes: dict[str, Any]
    status: str
    version_id: Optional[UUID]

    model_config = {"from_attributes": True}


class EvalRequest(BaseModel):
    span_id: str
    response_text: str
    user_question: str
    retrieved_context: str


class EvalOut(BaseModel):
    id: int
    span_id: str
    faithfulness: Optional[int]
    relevance: Optional[int]
    groundedness: Optional[int]
    reasoning: Optional[str]
    model_version: Optional[str]
    eval_timestamp: datetime

    model_config = {"from_attributes": True}


class PromptVersionIn(BaseModel):
    prompt_text: str
    label: Optional[str] = None
    is_active: bool = False


class PromptVersionOut(BaseModel):
    version_id: UUID
    prompt_text: str
    label: Optional[str]
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class RegressionAlertOut(BaseModel):
    id: int
    version_id: UUID
    metric: str
    baseline_score: float
    current_score: float
    threshold: float
    flagged_at: datetime

    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    question: str
    version_id: Optional[UUID] = None


class QueryResponse(BaseModel):
    trace_id: str
    answer: str
    citations: list[int]
    total_cost_usd: float
    latency_ms: float
