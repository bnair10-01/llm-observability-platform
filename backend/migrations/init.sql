CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS prompt_versions (
    version_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_text  TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active    BOOLEAN NOT NULL DEFAULT FALSE,
    label        TEXT
);

CREATE TABLE IF NOT EXISTS spans (
    id              SERIAL PRIMARY KEY,
    trace_id        TEXT NOT NULL,
    span_id         TEXT NOT NULL UNIQUE,
    parent_span_id  TEXT,
    name            TEXT NOT NULL,
    start_time      TIMESTAMPTZ NOT NULL,
    end_time        TIMESTAMPTZ,
    attributes      JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'OK',
    version_id      UUID REFERENCES prompt_versions(version_id)
);

CREATE INDEX IF NOT EXISTS idx_spans_trace_id  ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_span_id   ON spans(span_id);
CREATE INDEX IF NOT EXISTS idx_spans_created   ON spans(start_time, name);

CREATE TABLE IF NOT EXISTS evaluations (
    id             SERIAL PRIMARY KEY,
    span_id        TEXT NOT NULL REFERENCES spans(span_id),
    faithfulness   SMALLINT CHECK (faithfulness BETWEEN 1 AND 5),
    relevance      SMALLINT CHECK (relevance BETWEEN 1 AND 5),
    groundedness   SMALLINT CHECK (groundedness BETWEEN 1 AND 5),
    reasoning      TEXT,
    model_version  TEXT,
    eval_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evals_span_id ON evaluations(span_id);

CREATE TABLE IF NOT EXISTS regression_alerts (
    id              SERIAL PRIMARY KEY,
    version_id      UUID NOT NULL REFERENCES prompt_versions(version_id),
    metric          TEXT NOT NULL,
    baseline_score  NUMERIC(4,2) NOT NULL,
    current_score   NUMERIC(4,2) NOT NULL,
    threshold       NUMERIC(4,2) NOT NULL DEFAULT 0.5,
    flagged_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
