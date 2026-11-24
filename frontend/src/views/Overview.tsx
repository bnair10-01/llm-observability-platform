import { useOverview, useRunQuery } from "../api/client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { useState } from "react";
import { Zap, DollarSign, Star, Activity } from "lucide-react";

function KpiCard({ label, value, icon: Icon }: { label: string; value: string; icon: React.ElementType }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 flex items-center gap-4 border border-gray-800">
      <div className="p-3 bg-indigo-900/40 rounded-lg">
        <Icon className="w-5 h-5 text-indigo-400" />
      </div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-widest">{label}</p>
        <p className="text-2xl font-semibold text-white mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export default function Overview() {
  const { data, isLoading } = useOverview();
  const runQuery = useRunQuery();
  const [question, setQuestion] = useState("");
  const [lastResult, setLastResult] = useState<string | null>(null);

  const latencyData = data
    ? [
        { label: "p50", value: data.p50_latency_ms },
        { label: "p95", value: data.p95_latency_ms },
        { label: "p99", value: data.p99_latency_ms },
      ]
    : [];

  const avgQuality = data
    ? ((data.avg_faithfulness + data.avg_relevance + data.avg_groundedness) / 3).toFixed(2)
    : "—";

  async function handleQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    const result = await runQuery.mutateAsync({ question });
    setLastResult(result.answer);
    setQuestion("");
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Total Traces" value={isLoading ? "…" : String(data?.total_traces ?? 0)} icon={Activity} />
        <KpiCard label="Avg Quality" value={isLoading ? "…" : avgQuality} icon={Star} />
        <KpiCard label="Avg Cost" value={isLoading ? "…" : `$${data?.avg_cost_usd.toFixed(5) ?? "0"}`} icon={DollarSign} />
        <KpiCard label="p95 Latency" value={isLoading ? "…" : `${data?.p95_latency_ms ?? 0} ms`} icon={Zap} />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-widest">Latency Distribution</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={latencyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="label" stroke="#6b7280" />
            <YAxis stroke="#6b7280" unit=" ms" />
            <Tooltip
              contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
              labelStyle={{ color: "#e5e7eb" }}
            />
            <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-widest">Run a Query</h2>
        <form onSubmit={handleQuery} className="flex gap-3">
          <input
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Ask a question…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            type="submit"
            disabled={runQuery.isPending}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-lg transition"
          >
            {runQuery.isPending ? "Running…" : "Run"}
          </button>
        </form>
        {lastResult && (
          <div className="mt-4 p-4 bg-gray-800 rounded-lg text-sm text-gray-200 whitespace-pre-wrap">
            {lastResult}
          </div>
        )}
      </div>
    </div>
  );
}
