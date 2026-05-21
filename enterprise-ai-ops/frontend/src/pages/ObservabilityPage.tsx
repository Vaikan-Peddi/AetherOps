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
