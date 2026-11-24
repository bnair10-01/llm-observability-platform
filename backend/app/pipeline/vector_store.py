"""
In-memory vector store backed by sentence-transformers.
Documents are embedded once at startup; queries use cosine similarity.
"""
from __future__ import annotations
import numpy as np

DOCUMENTS = [
    "Retrieval-Augmented Generation (RAG) combines a retrieval system with a generative language model.",
    "OpenTelemetry provides a vendor-neutral observability framework for distributed tracing.",
    "LLM evaluation frameworks assess model outputs for faithfulness, relevance, and groundedness.",
    "PostgreSQL supports JSONB columns for flexible schema-less attribute storage.",
    "FastAPI is a modern Python web framework built on Starlette and Pydantic.",
    "Sentence-transformers produce dense vector embeddings for semantic similarity search.",
    "Docker Compose orchestrates multi-service applications with a single YAML file.",
    "Prompt versioning enables A/B testing and regression detection across LLM deployments.",
    "Cosine similarity measures the angle between two vectors, ranging from -1 to 1.",
    "SQLAlchemy ORM maps Python classes to database tables using declarative syntax.",
    "Recharts is a composable charting library built on React and D3.",
    "React Query manages server state, caching, and background refetching in React apps.",
    "Tailwind CSS is a utility-first framework for rapidly building custom interfaces.",
    "Span processors intercept completed spans before they are exported to a backend.",
    "W3C Trace Context defines HTTP headers for distributed trace propagation.",
    "Token-based pricing for GPT-4o-mini is $0.15 per million input tokens and $0.60 per million output tokens.",
    "Batch evaluations run LLM-as-judge scoring across an entire prompt version's history.",
    "Regression detection flags prompt versions whose average eval score drops by more than 0.5 points.",
    "Citation verification ensures that claims in LLM responses are grounded in retrieved sources.",
    "Health checks in Docker Compose prevent dependent services from starting before dependencies are ready.",
]

_embeddings: np.ndarray | None = None
_model = None


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_embeddings() -> np.ndarray:
    global _embeddings
    if _embeddings is None:
        model = _load_model()
        _embeddings = model.encode(DOCUMENTS, normalize_embeddings=True)
    return _embeddings


def search(query: str, top_k: int = 5) -> list[dict]:
    model = _load_model()
    embs = _get_embeddings()
    q_vec = model.encode([query], normalize_embeddings=True)[0]
    scores = (embs @ q_vec).tolist()
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        {"index": idx, "text": DOCUMENTS[idx], "score": round(score, 4)}
        for idx, score in ranked
    ]
