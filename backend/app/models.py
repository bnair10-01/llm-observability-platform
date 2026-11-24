import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, SmallInteger,
    Numeric, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP

TIMESTAMPTZ = TIMESTAMP(timezone=True)
from sqlalchemy.orm import relationship
from .db import Base


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    version_id  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_text = Column(Text, nullable=False)
    created_at  = Column(TIMESTAMPTZ, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_active   = Column(Boolean, nullable=False, default=False)
    label       = Column(Text)

    spans  = relationship("Span", back_populates="version")
    alerts = relationship("RegressionAlert", back_populates="version")


class Span(Base):
    __tablename__ = "spans"
    __table_args__ = (
        Index("idx_spans_trace_id", "trace_id"),
        Index("idx_spans_created",  "start_time", "name"),
    )

    id             = Column(Integer, primary_key=True)
    trace_id       = Column(String, nullable=False)
    span_id        = Column(String, nullable=False, unique=True)
    parent_span_id = Column(String)
    name           = Column(String, nullable=False)
    start_time     = Column(TIMESTAMPTZ, nullable=False)
    end_time       = Column(TIMESTAMPTZ)
    attributes     = Column(JSONB, nullable=False, default=dict)
    status         = Column(String, nullable=False, default="OK")
    version_id     = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.version_id"))

    version     = relationship("PromptVersion", back_populates="spans")
    evaluations = relationship("Evaluation", back_populates="span")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id             = Column(Integer, primary_key=True)
    span_id        = Column(String, ForeignKey("spans.span_id"), nullable=False)
    faithfulness   = Column(SmallInteger)
    relevance      = Column(SmallInteger)
    groundedness   = Column(SmallInteger)
    reasoning      = Column(Text)
    model_version  = Column(Text)
    eval_timestamp = Column(TIMESTAMPTZ, nullable=False, default=lambda: datetime.now(timezone.utc))

    span = relationship("Span", back_populates="evaluations")


class RegressionAlert(Base):
    __tablename__ = "regression_alerts"

    id             = Column(Integer, primary_key=True)
    version_id     = Column(UUID(as_uuid=True), ForeignKey("prompt_versions.version_id"), nullable=False)
    metric         = Column(String, nullable=False)
    baseline_score = Column(Numeric(4, 2), nullable=False)
    current_score  = Column(Numeric(4, 2), nullable=False)
    threshold      = Column(Numeric(4, 2), nullable=False, default=0.5)
    flagged_at     = Column(TIMESTAMPTZ, nullable=False, default=lambda: datetime.now(timezone.utc))

    version = relationship("PromptVersion", back_populates="alerts")
