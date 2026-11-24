"""Drive llm-observability through its public HTTP API and collect metrics."""
import os
OUT = os.environ.get("BENCH_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
os.makedirs(OUT, exist_ok=True)
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
import json, re, statistics, sys, time, requests
import numpy as np
from fastembed import TextEmbedding

B = BASE_URL
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
QS = ["What is retrieval-augmented generation?", "How does OpenTelemetry help with tracing?",
      "What does cosine similarity measure?", "How is regression detected for prompt versions?",
      "What is FastAPI built on?", "Why use Docker Compose health checks?",
      "How does GPT-4o-mini pricing work?", "What are sentence-transformers used for?",
      "What does citation verification do?", "What is JSONB in PostgreSQL?"]

src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "app", "pipeline", "vector_store.py")).read()
DOCS = re.findall(r'^    "(.*)",$', src, re.M)
assert len(DOCS) == 20, len(DOCS)
emb = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
D = np.array(list(emb.embed(DOCS))); D /= np.linalg.norm(D, axis=1, keepdims=True)

def context_for(q):
    v = np.array(list(emb.embed([q]))[0]); v /= np.linalg.norm(v)
    top = np.argsort(-(D @ v))[:5]
    return "\n\n".join(f"[Source: {i}] {DOCS[i]}" for i in top)

def post(p, **kw):
    r = requests.post(B + p, timeout=300, **kw); r.raise_for_status(); return r.json()
def get(p, **kw):
    r = requests.get(B + p, timeout=60, **kw); r.raise_for_status(); return r.json()

v1 = post("/prompt-versions", json={"prompt_text": "You are a helpful assistant. Answer ONLY from the provided documents and cite every claim as [Source: N].", "label": "v1-grounded", "is_active": True})
v2 = post("/prompt-versions", json={"prompt_text": "Answer in one short sentence from your own general knowledge. Do not mention the documents and never cite sources.", "label": "v2-ungrounded"})

rows = []
for label, v in (("v1", v1), ("v2", v2)):
    for i in range(N):
        q = QS[i % len(QS)]
        t = time.time()
        r = post("/query", json={"question": q, "version_id": v["version_id"]})
        rows.append({"v": label, "vid": v["version_id"], "q": q, "context": context_for(q), "wall_ms": (time.time() - t) * 1000, **r})
        print(f"{label} {i+1}/{N} pipeline={r['latency_ms']:.0f}ms cites={r['citations']} cost=${r['total_cost_usd']}", flush=True)

time.sleep(8)  # BatchSpanProcessor flush
by_run = {}
for root in get("/traces", params={"limit": 500}):
    for s in get(f"/traces/{root['trace_id']}"):
        if s["name"] == "response_complete":
            by_run[s["attributes"].get("trace.id")] = s
missing = [r for r in rows if r["trace_id"] not in by_run]
print("spans found:", len(rows) - len(missing), "of", len(rows))

ev_ms = []
for r in rows:
    s = by_run.get(r["trace_id"])
    if not s:
        continue
    t = time.time()
    e = post("/eval", json={"span_id": s["span_id"], "response_text": r["answer"], "user_question": r["q"], "retrieved_context": r["context"]})
    ev_ms.append((time.time() - t) * 1000)
    r.update(span_id=s["span_id"], faithfulness=e["faithfulness"], relevance=e["relevance"], groundedness=e["groundedness"])
    print(f"eval {r['v']} f={e['faithfulness']} r={e['relevance']} g={e['groundedness']}", flush=True)

stats = {k: get(f"/prompt-versions/{v['version_id']}/stats") for k, v in (("v1", v1), ("v2", v2))}
batch = requests.post(f"{B}/eval/batch", params={"version_id": v2["version_id"], "baseline_version_id": v1["version_id"]}, timeout=120).json()
time.sleep(5)
alerts = get("/regression-alerts")

def pct(xs, p): xs = sorted(xs); return xs[max(0, int(len(xs) * p / 100 + 0.5) - 1)]
summary = {"n_per_version": N, "versions": {"v1": v1["version_id"], "v2": v2["version_id"]}, "stats": stats, "batch": batch,
           "alerts": alerts, "overview": get("/overview"), "eval_ms_p50": statistics.median(ev_ms) if ev_ms else None}
for k in ("v1", "v2"):
    L = [r["latency_ms"] for r in rows if r["v"] == k]
    summary[f"{k}_latency"] = {"p50": statistics.median(L), "p95": pct(L, 95), "max": max(L)}
    summary[f"{k}_valid_citation_rate"] = sum(1 for r in rows if r["v"] == k and r["citations"]) / N
json.dump({"summary": summary, "rows": rows}, open(f"{OUT}/obs_results.json", "w"), indent=1, default=str)
print(json.dumps(summary, indent=1, default=str))
