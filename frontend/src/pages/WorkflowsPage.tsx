import { Play, Plus } from "lucide-react";
import React, { useEffect, useState } from "react";
import { api, type Workflow, type WorkflowRun } from "../api/client";
import { Panel } from "../components/Panel";

export function WorkflowsPage({ organizationId }: { organizationId: string }) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [name, setName] = useState("Document answer workflow");
  const [query, setQuery] = useState("Summarize the most important operational risk.");
  const [message, setMessage] = useState("");
  const [lastRun, setLastRun] = useState<WorkflowRun | null>(null);

  async function load() {
    if (!organizationId) return;
    setWorkflows(await api.workflows(organizationId));
  }

  useEffect(() => {
    load().catch((err) => setMessage(err instanceof Error ? err.message : "Could not load workflows"));
  }, [organizationId]);

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await api.createWorkflow(organizationId, name, query);
      setMessage("Workflow created");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not create workflow");
    }
  }

  async function run(workflow: Workflow) {
    setMessage("Workflow run queued");
    try {
      const runResult = await api.runWorkflow(workflow.id, { query });
      setLastRun(runResult);
      setTimeout(async () => {
        const refreshed = await api.getRun(runResult.id);
        setLastRun(refreshed);
      }, 2500);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not run workflow");
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
      <Panel title="Create Workflow">
        <form onSubmit={create} className="grid gap-3">
          <input className="h-10 rounded-md border border-slate-300 px-3 text-sm" value={name} onChange={(event) => setName(event.target.value)} />
          <textarea className="min-h-24 rounded-md border border-slate-300 p-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} />
          <button title="Create workflow" className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-900 px-3 text-sm font-semibold text-white">
            <Plus size={16} />
            Create Workflow
          </button>
        </form>
        {message ? <p className="mt-3 text-sm text-slate-600">{message}</p> : null}
      </Panel>
      <Panel title="Workflow Runs">
        <div className="grid gap-3">
          {workflows.map((workflow) => (
            <article key={workflow.id} className="rounded-lg border border-slate-200 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h4 className="font-semibold text-slate-950">{workflow.name}</h4>
                  <p className="text-sm text-slate-500">{workflow.steps.length} step workflow</p>
                </div>
                <button onClick={() => run(workflow)} title="Run workflow" className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-medium hover:bg-slate-100">
                  <Play size={16} />
                  Run
                </button>
              </div>
            </article>
          ))}
          {!workflows.length ? <p className="text-sm text-slate-500">No workflows yet.</p> : null}
        </div>
        {lastRun ? (
          <div className="mt-5 rounded-lg bg-slate-900 p-4 text-sm text-white">
            <p className="font-semibold">Last run: {lastRun.status}</p>
            <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs text-slate-200">{JSON.stringify(lastRun.outputs || lastRun, null, 2)}</pre>
          </div>
        ) : null}
      </Panel>
    </div>
  );
}
