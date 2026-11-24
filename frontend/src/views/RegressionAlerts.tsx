import { useAlerts } from "../api/client";
import { AlertTriangle } from "lucide-react";

export default function RegressionAlerts() {
  const { data: alerts, isLoading } = useAlerts();

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-medium text-gray-400 uppercase tracking-widest">Regression Alerts</h2>
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[1fr_100px_100px_80px_160px] text-xs text-gray-500 uppercase px-5 py-3 border-b border-gray-800">
          <span>Version</span>
          <span>Metric</span>
          <span>Baseline</span>
          <span>Current</span>
          <span>Flagged At</span>
        </div>
        {isLoading && <p className="text-gray-500 text-sm p-5">Loading…</p>}
        {!isLoading && !alerts?.length && (
          <div className="flex items-center gap-3 p-5 text-gray-500 text-sm">
            <AlertTriangle className="w-4 h-4 text-green-500" />
            No regressions detected. All versions are on par with baseline.
          </div>
        )}
        {alerts?.map((a) => {
          const delta = a.current_score - a.baseline_score;
          return (
            <div
              key={a.id}
              className="grid grid-cols-[1fr_100px_100px_80px_160px] items-center px-5 py-3 border-b border-gray-800 hover:bg-gray-800/40"
            >
              <span className="text-xs font-mono text-gray-400 truncate">{a.version_id.slice(0, 12)}…</span>
              <span className="text-sm capitalize text-white">{a.metric}</span>
              <span className="text-sm text-gray-300">{a.baseline_score.toFixed(2)}</span>
              <span className="text-sm font-semibold text-red-400">{a.current_score.toFixed(2)}</span>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                <span className="text-xs text-gray-500">
                  {new Date(a.flagged_at).toLocaleString()}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
