import { useState } from "react";
import { useTraces, useTrace, SpanRow } from "../api/client";
import { Search, ChevronRight } from "lucide-react";

function latencyMs(s: SpanRow) {
  if (!s.end_time) return "—";
  return Math.round(
    (new Date(s.end_time).getTime() - new Date(s.start_time).getTime())
  ) + " ms";
}

function WaterfallBar({ span, minMs, rangeMs }: { span: SpanRow; minMs: number; rangeMs: number }) {
  const start = new Date(span.start_time).getTime();
  const end = span.end_time ? new Date(span.end_time).getTime() : start;
  const left = rangeMs ? ((start - minMs) / rangeMs) * 100 : 0;
  const width = rangeMs ? Math.max(((end - start) / rangeMs) * 100, 1) : 2;

  const colours: Record<string, string> = {
    question_received: "bg-blue-500",
    retrieval_step: "bg-green-500",
    llm_call: "bg-purple-500",
    citation_check: "bg-yellow-500",
    response_complete: "bg-indigo-500",
  };
  const colour = colours[span.name] ?? "bg-gray-500";

  return (
    <div className="relative h-5 bg-gray-800 rounded overflow-hidden">
      <div
        className={`absolute top-0 h-full ${colour} rounded opacity-80`}
        style={{ left: `${left}%`, width: `${width}%` }}
      />
    </div>
  );
}

function TraceDetail({ traceId }: { traceId: string }) {
  const { data: spans } = useTrace(traceId);
  if (!spans?.length) return <p className="text-gray-500 text-sm p-4">Loading…</p>;

  const times = spans.flatMap((s) => [
    new Date(s.start_time).getTime(),
    s.end_time ? new Date(s.end_time).getTime() : new Date(s.start_time).getTime(),
  ]);
  const minMs = Math.min(...times);
  const rangeMs = Math.max(...times) - minMs;

  return (
    <div className="mt-3 bg-gray-950 border border-gray-800 rounded-lg overflow-hidden">
      <div className="grid grid-cols-[180px_1fr_80px] text-xs text-gray-500 uppercase px-4 py-2 border-b border-gray-800">
        <span>Span</span><span>Timeline</span><span className="text-right">Duration</span>
      </div>
      {spans.map((s) => (
        <div
          key={s.span_id}
          className="grid grid-cols-[180px_1fr_80px] items-center px-4 py-2 border-b border-gray-900 hover:bg-gray-900/40"
        >
          <span className="text-xs text-gray-300 truncate pr-2">{s.name}</span>
          <WaterfallBar span={s} minMs={minMs} rangeMs={rangeMs} />
          <span className="text-xs text-gray-400 text-right">{latencyMs(s)}</span>
        </div>
      ))}
      <div className="p-4 space-y-1">
        {spans.filter(s => s.name === "response_complete").map(s => (
          <details key={s.span_id} className="text-xs">
            <summary className="text-indigo-400 cursor-pointer">Attributes</summary>
            <pre className="mt-2 bg-gray-900 p-3 rounded text-gray-300 overflow-x-auto">
              {JSON.stringify(s.attributes, null, 2)}
            </pre>
          </details>
        ))}
      </div>
    </div>
  );
}

export default function Traces() {
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const { data: traces, isLoading } = useTraces(search);

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
        <input
          className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Search by question…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[1fr_140px_100px_80px] text-xs text-gray-500 uppercase px-5 py-3 border-b border-gray-800">
          <span>Question</span><span>Trace ID</span><span>Latency</span><span>Status</span>
        </div>
        {isLoading && (
          <p className="text-gray-500 text-sm p-5">Loading traces…</p>
        )}
        {traces?.map((t) => (
          <div key={t.trace_id}>
            <button
              onClick={() => setExpanded(expanded === t.trace_id ? null : t.trace_id)}
              className="w-full grid grid-cols-[1fr_140px_100px_80px] items-center px-5 py-3 border-b border-gray-800 hover:bg-gray-800/50 text-left"
            >
              <span className="text-sm text-gray-200 truncate pr-3">
                {(t.attributes.user_question as string) ?? t.trace_id}
              </span>
              <span className="text-xs text-gray-500 font-mono truncate">{t.trace_id.slice(0, 12)}…</span>
              <span className="text-xs text-gray-400">{latencyMs(t)}</span>
              <span className={`text-xs font-medium ${t.status === "ERROR" ? "text-red-400" : "text-green-400"}`}>
                {t.status}
              </span>
            </button>
            {expanded === t.trace_id && (
              <div className="px-5 pb-4">
                <TraceDetail traceId={t.trace_id} />
              </div>
            )}
          </div>
        ))}
        {!isLoading && !traces?.length && (
          <p className="text-gray-500 text-sm p-5">No traces yet. Run a query from the Overview tab.</p>
        )}
      </div>
    </div>
  );
}
