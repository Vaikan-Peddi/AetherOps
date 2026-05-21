import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type Summary } from "../api/client";
import { Panel } from "../components/Panel";

export function ObservabilityPage({ organizationId }: { organizationId: string }) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      setSummary(await api.summary(organizationId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load summary");
    }
  }

  useEffect(() => {
    load();
  }, [organizationId]);

  return (
    <Panel title="Operational Summary">
      <button onClick={load} title="Refresh summary" className="mb-4 inline-flex h-10 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-medium hover:bg-slate-100">
        <RefreshCw size={16} />
        Refresh
      </button>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryTile label="Documents" value={summary?.total_documents ?? 0} />
        <SummaryTile label="AI queries" value={summary?.total_queries ?? 0} />
        <SummaryTile label="Workflows" value={summary?.total_workflows ?? 0} />
        <SummaryTile label="Workflow runs" value={summary?.total_workflow_runs ?? 0} />
        <SummaryTile label="Avg latency ms" value={summary?.avg_latency_ms ?? 0} />
        <SummaryTile label="Tokens" value={summary?.total_tokens ?? 0} />
      </div>
      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        <Distribution title="Provider usage" values={summary?.provider_usage ?? {}} />
        <Distribution title="Model distribution" values={summary?.model_distribution ?? {}} />
        <Distribution title="Workflow status" values={summary?.workflow_status ?? {}} />
      </div>
    </Panel>
  );
}

function SummaryTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function Distribution({ title, values }: { title: string; values: Record<string, number> }) {
  const entries = Object.entries(values);
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <h3 className="font-semibold text-slate-950">{title}</h3>
      <div className="mt-3 grid gap-2">
        {entries.map(([label, value]) => (
          <div key={label} className="flex items-center justify-between text-sm">
            <span className="text-slate-600">{label}</span>
            <span className="font-semibold text-slate-950">{value}</span>
          </div>
        ))}
        {!entries.length ? <p className="text-sm text-slate-500">No data yet.</p> : null}
      </div>
    </div>
  );
}
