import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Types ──────────────────────────────────────────────────────────────────────

export interface SpanRow {
  id: number;
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  name: string;
  start_time: string;
  end_time: string | null;
  attributes: Record<string, unknown>;
  status: string;
  version_id: string | null;
}

export interface Overview {
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  avg_cost_usd: number;
  avg_faithfulness: number;
  avg_relevance: number;
  avg_groundedness: number;
  total_traces: number;
}

export interface TrendPoint {
  day: string;
  faithfulness: number;
  relevance: number;
  groundedness: number;
  count: number;
}

export interface PromptVersion {
  version_id: string;
  prompt_text: string;
  label: string | null;
  created_at: string;
  is_active: boolean;
}

export interface VersionStats {
  version_id: string;
  faithfulness: number;
  relevance: number;
  groundedness: number;
  eval_count: number;
}

export interface RegressionAlert {
  id: number;
  version_id: string;
  metric: string;
  baseline_score: number;
  current_score: number;
  threshold: number;
  flagged_at: string;
}

export interface QueryResponse {
  trace_id: string;
  answer: string;
  citations: number[];
  total_cost_usd: number;
  latency_ms: number;
}

// ── Hooks ──────────────────────────────────────────────────────────────────────

export const useOverview = () =>
  useQuery<Overview>({
    queryKey: ["overview"],
    queryFn: () => get("/overview"),
    refetchInterval: 30_000,
  });

export const useTraces = (search?: string) =>
  useQuery<SpanRow[]>({
    queryKey: ["traces", search],
    queryFn: () => get(`/traces${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  });

export const useTrace = (traceId: string) =>
  useQuery<SpanRow[]>({
    queryKey: ["trace", traceId],
    queryFn: () => get(`/traces/${traceId}`),
    enabled: !!traceId,
  });

export const useTrends = () =>
  useQuery<TrendPoint[]>({
    queryKey: ["trends"],
    queryFn: () => get("/quality-trends?days=7"),
  });

export const useVersions = () =>
  useQuery<PromptVersion[]>({
    queryKey: ["versions"],
    queryFn: () => get("/prompt-versions"),
  });

export const useVersionStats = (versionId: string) =>
  useQuery<VersionStats>({
    queryKey: ["version-stats", versionId],
    queryFn: () => get(`/prompt-versions/${versionId}/stats`),
    enabled: !!versionId,
  });

export const useAlerts = () =>
  useQuery<RegressionAlert[]>({
    queryKey: ["alerts"],
    queryFn: () => get("/regression-alerts"),
    refetchInterval: 30_000,
  });

export const useRunQuery = () => {
  const qc = useQueryClient();
  return useMutation<QueryResponse, Error, { question: string; version_id?: string }>({
    mutationFn: (body) => post("/query", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["traces"] }),
  });
};

export const useCreateVersion = () => {
  const qc = useQueryClient();
  return useMutation<PromptVersion, Error, { prompt_text: string; label?: string; is_active?: boolean }>({
    mutationFn: (body) => post("/prompt-versions", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["versions"] }),
  });
};

export const useBatchEval = () =>
  useMutation<unknown, Error, { version_id: string; baseline_version_id?: string }>({
    mutationFn: ({ version_id, baseline_version_id }) =>
      post(
        `/eval/batch?version_id=${version_id}${baseline_version_id ? `&baseline_version_id=${baseline_version_id}` : ""}`,
        {}
      ),
  });
