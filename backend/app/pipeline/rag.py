"""
Multi-step RAG pipeline with OpenTelemetry instrumentation.
Each step is wrapped in a child span; all spans are flushed to Postgres
via the custom DbSpanExporter registered in main.py.
"""
from __future__ import annotations
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from opentelemetry import trace

from . import vector_store

tracer = trace.get_tracer(__name__)

# GPT-4o-mini pricing (per token)
_INPUT_COST_PER_TOKEN  = 0.15 / 1_000_000
_OUTPUT_COST_PER_TOKEN = 0.60 / 1_000_000


def _build_prompt(version_prompt: str, question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source: {c['index']}] {c['text']}" for c in chunks
    )
    return f"{version_prompt}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"


def run_pipeline(
    question: str,
    version_id: Optional[str],
    prompt_text: str,
    openai_client,
) -> dict:
    import openai  # noqa: F401 — referenced via openai_client

    pipeline_start = time.time()
    run_trace_id = str(uuid.uuid4()).replace("-", "")

    with tracer.start_as_current_span(
        "response_complete",
        attributes={"trace.id": run_trace_id},
    ) as root_span:
        # ── step 1: question_received ──────────────────────────────────────
        with tracer.start_as_current_span("question_received") as s:
            s.set_attribute("user_question", question)
            s.set_attribute("version_id", str(version_id) if version_id else "")

        # ── step 2: retrieval_step ─────────────────────────────────────────
        t0 = time.time()
        with tracer.start_as_current_span("retrieval_step") as s:
            chunks = vector_store.search(question, top_k=5)
            avg_sim = round(sum(c["score"] for c in chunks) / len(chunks), 4)
            s.set_attribute("chunk_count", len(chunks))
            s.set_attribute("avg_similarity_score", avg_sim)
            s.set_attribute("latency_ms", round((time.time() - t0) * 1000, 2))

        # ── step 3: llm_call ───────────────────────────────────────────────
        full_prompt = _build_prompt(prompt_text, question, chunks)
        t1 = time.time()
        with tracer.start_as_current_span("llm_call") as s:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.2,
            )
            llm_latency = round((time.time() - t1) * 1000, 2)
            usage = response.usage
            cost = (
                usage.prompt_tokens * _INPUT_COST_PER_TOKEN
                + usage.completion_tokens * _OUTPUT_COST_PER_TOKEN
            )
            answer = response.choices[0].message.content.strip()
            s.set_attribute("model", "gpt-4o-mini")
            s.set_attribute("prompt_tokens", usage.prompt_tokens)
            s.set_attribute("completion_tokens", usage.completion_tokens)
            s.set_attribute("latency_ms", llm_latency)
            s.set_attribute("cost_usd", round(cost, 6))

        # ── step 4: citation_check ─────────────────────────────────────────
        with tracer.start_as_current_span("citation_check") as s:
            cited_indices = [int(n) for n in re.findall(r"\[Source:\s*(\d+)\]", answer)]
            retrieved_indices = [c["index"] for c in chunks]
            valid = [i for i in cited_indices if i in retrieved_indices]
            s.set_attribute("cited_indices", str(cited_indices))
            s.set_attribute("valid_citations", len(valid))
            s.set_attribute("invalid_citations", len(cited_indices) - len(valid))

        # ── root span attributes ───────────────────────────────────────────
        total_latency = round((time.time() - pipeline_start) * 1000, 2)
        # Stored on the root span so the Traces tab and /eval/batch can read them.
        root_span.set_attribute("user_question", question)
        root_span.set_attribute("answer", answer)
        root_span.set_attribute(
            "retrieved_context",
            "\n\n".join(f"[Source: {c['index']}] {c['text']}" for c in chunks),
        )
        root_span.set_attribute("total_latency_ms", total_latency)
        root_span.set_attribute("total_cost_usd", round(cost, 6))
        root_span.set_attribute("version_id", str(version_id) if version_id else "")

    return {
        "trace_id": run_trace_id,
        "answer": answer,
        "citations": cited_indices,
        "total_cost_usd": round(cost, 6),
        "latency_ms": total_latency,
        "chunks": chunks,
        "question": question,
    }
