import { useTrends } from "../api/client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";

export default function QualityTrends() {
  const { data, isLoading } = useTrends();

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
      <h2 className="text-sm font-medium text-gray-400 uppercase tracking-widest">
        Quality Trends — 7-Day Rolling Window
      </h2>
      {isLoading && <p className="text-gray-500 text-sm">Loading…</p>}
      {!isLoading && !data?.length && (
        <p className="text-gray-500 text-sm">
          No evaluation data yet. Run queries and trigger evals from the Prompt Versions tab.
        </p>
      )}
      {!!data?.length && (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="day" stroke="#6b7280" tick={{ fontSize: 11 }} />
            <YAxis domain={[1, 5]} stroke="#6b7280" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
              labelStyle={{ color: "#e5e7eb" }}
              formatter={(value: number, name: string, props) => [
                `${value} (n=${props.payload.count})`,
                name,
              ]}
            />
            <Legend />
            <Line type="monotone" dataKey="faithfulness" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="relevance"    stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="groundedness" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
