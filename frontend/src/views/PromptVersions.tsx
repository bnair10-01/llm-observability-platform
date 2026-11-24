import { useState } from "react";
import {
  useVersions, useVersionStats, useCreateVersion, useBatchEval,
  PromptVersion,
} from "../api/client";
import { Plus, Play, ChevronDown, ChevronUp } from "lucide-react";

function ScoreBadge({ value }: { value: number }) {
  const colour =
    value >= 4 ? "text-green-400" : value >= 3 ? "text-yellow-400" : "text-red-400";
  return <span className={`font-semibold ${colour}`}>{value.toFixed(2)}</span>;
}

function VersionRow({
  v,
  versions,
}: {
  v: PromptVersion;
  versions: PromptVersion[];
}) {
  const [open, setOpen] = useState(false);
  const [baseline, setBaseline] = useState<string>("");
  const { data: stats } = useVersionStats(v.version_id);
  const batchEval = useBatchEval();

  return (
    <div className="border-b border-gray-800 last:border-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-800/40 text-left"
      >
        <div className="flex items-center gap-3">
          {v.is_active && (
            <span className="text-xs bg-green-900/50 text-green-400 border border-green-800 rounded px-2 py-0.5">
              Active
            </span>
          )}
          <span className="text-sm text-white font-medium">{v.label ?? v.version_id.slice(0, 8)}</span>
          <span className="text-xs text-gray-500">{new Date(v.created_at).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-6 text-sm">
          {stats ? (
            <>
              <span className="text-gray-500 text-xs">
                F: <ScoreBadge value={stats.faithfulness} /> R: <ScoreBadge value={stats.relevance} /> G: <ScoreBadge value={stats.groundedness} />
              </span>
              <span className="text-xs text-gray-600">({stats.eval_count} evals)</span>
            </>
          ) : (
            <span className="text-xs text-gray-600">no evals</span>
          )}
          {open ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-4">
          <pre className="bg-gray-950 border border-gray-800 rounded-lg p-4 text-sm text-gray-300 whitespace-pre-wrap">
            {v.prompt_text}
          </pre>
          <div className="flex items-center gap-3">
            <select
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white flex-1"
              value={baseline}
              onChange={(e) => setBaseline(e.target.value)}
            >
              <option value="">Compare vs baseline (optional)</option>
              {versions
                .filter((vv) => vv.version_id !== v.version_id)
                .map((vv) => (
                  <option key={vv.version_id} value={vv.version_id}>
                    {vv.label ?? vv.version_id.slice(0, 8)}
                  </option>
                ))}
            </select>
            <button
              onClick={() =>
                batchEval.mutate({
                  version_id: v.version_id,
                  baseline_version_id: baseline || undefined,
                })
              }
              disabled={batchEval.isPending}
              className="flex items-center gap-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-lg transition"
            >
              <Play className="w-3.5 h-3.5" />
              {batchEval.isPending ? "Queuing…" : "Run Batch Eval"}
            </button>
          </div>
          {batchEval.isSuccess && (
            <p className="text-xs text-green-400">Batch eval queued. Refresh quality trends in a moment.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function PromptVersions() {
  const { data: versions } = useVersions();
  const createVersion = useCreateVersion();
  const [showForm, setShowForm] = useState(false);
  const [label, setLabel] = useState("");
  const [text, setText] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await createVersion.mutateAsync({ prompt_text: text, label: label || undefined });
    setLabel("");
    setText("");
    setShowForm(false);
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-sm font-medium text-gray-400 uppercase tracking-widest">Prompt Versions</h2>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-2 px-4 py-1.5 bg-gray-800 hover:bg-gray-700 text-white text-sm rounded-lg border border-gray-700 transition"
        >
          <Plus className="w-3.5 h-3.5" /> New Version
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Label (optional)"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
          <textarea
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 h-32 resize-none"
            placeholder="System prompt text…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
          />
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={() => setShowForm(false)} className="text-sm text-gray-500 hover:text-gray-300">
              Cancel
            </button>
            <button
              type="submit"
              disabled={createVersion.isPending}
              className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded-lg"
            >
              {createVersion.isPending ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {!versions?.length && (
          <p className="text-gray-500 text-sm p-5">No versions yet. Create one above.</p>
        )}
        {versions?.map((v) => (
          <VersionRow key={v.version_id} v={v} versions={versions} />
        ))}
      </div>
    </div>
  );
}
