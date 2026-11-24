import { useState } from "react";
import { Activity, GitBranch, TrendingUp, AlertTriangle, LayoutDashboard } from "lucide-react";
import Overview from "./views/Overview";
import Traces from "./views/Traces";
import QualityTrends from "./views/QualityTrends";
import PromptVersions from "./views/PromptVersions";
import RegressionAlerts from "./views/RegressionAlerts";

const TABS = [
  { id: "overview",  label: "Overview",         Icon: LayoutDashboard },
  { id: "traces",    label: "Traces",            Icon: Activity },
  { id: "trends",    label: "Quality Trends",    Icon: TrendingUp },
  { id: "versions",  label: "Prompt Versions",   Icon: GitBranch },
  { id: "alerts",    label: "Regression Alerts", Icon: AlertTriangle },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const [active, setActive] = useState<TabId>("overview");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-white text-lg">LLM Observability</span>
          </div>
          <span className="text-xs text-gray-600">Self-Hosted · OpenTelemetry</span>
        </div>
        {/* Tab bar */}
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex gap-1 -mb-px overflow-x-auto">
            {TABS.map(({ id, label, Icon }) => (
              <button
                key={id}
                onClick={() => setActive(id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm border-b-2 transition whitespace-nowrap ${
                  active === id
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-gray-500 hover:text-gray-300"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {active === "overview"  && <Overview />}
        {active === "traces"    && <Traces />}
        {active === "trends"    && <QualityTrends />}
        {active === "versions"  && <PromptVersions />}
        {active === "alerts"    && <RegressionAlerts />}
      </main>
    </div>
  );
}
