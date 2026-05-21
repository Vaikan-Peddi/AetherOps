import { ArrowDown, ArrowUp, Play, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { Background, Controls, ReactFlow, addEdge, useEdgesState, useNodesState, type Connection, type Edge, type Node } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api, type Workflow, type WorkflowRun, type WorkflowStepInput } from "../api/client";
import { Panel } from "../components/Panel";

type StepDraft = WorkflowStepInput & {
  id: string;
};

const actionLabels: Record<StepDraft["action_type"], string> = {
  RAG_QUERY: "RAG query",
  SUMMARIZE: "Summarize",
  SUMMARIZE_TEXT: "Summarize text",
  CHAT: "Chat",
  WEBHOOK: "Webhook",
  SEND_WEBHOOK_PLACEHOLDER: "Webhook placeholder",
  CONDITION: "Condition",
  DELAY: "Delay",
  HUMAN_APPROVAL: "Human approval"
};

function defaultStep(actionType: StepDraft["action_type"] = "RAG_QUERY"): StepDraft {
  const id = crypto.randomUUID();
  if (actionType === "SUMMARIZE" || actionType === "SUMMARIZE_TEXT") {
    return {
      id,
      name: "Summarize retrieved answer",
      action_type: "SUMMARIZE",
      config: { text: "" }
    };
  }
  if (actionType === "WEBHOOK" || actionType === "SEND_WEBHOOK_PLACEHOLDER") {
    return {
      id,
      name: "Notify downstream system",
      action_type: "WEBHOOK",
      config: { url: "" }
    };
  }
  if (actionType === "CHAT") {
    return { id, name: "Ask model", action_type: "CHAT", config: { message: "" } };
  }
  if (actionType === "CONDITION") {
    return { id, name: "Check condition", action_type: "CONDITION", config: { contains: "" } };
  }
  if (actionType === "DELAY") {
    return { id, name: "Delay", action_type: "DELAY", config: { seconds: "5" } };
  }
  if (actionType === "HUMAN_APPROVAL") {
    return { id, name: "Human approval", action_type: "HUMAN_APPROVAL", config: {} };
  }
  return {
    id,
    name: "Ask documents",
    action_type: "RAG_QUERY",
    config: { query: "Summarize the most important parts of the book." }
  };
}

export function WorkflowsPage({ organizationId }: { organizationId: string }) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [name, setName] = useState("Book summary workflow");
  const [steps, setSteps] = useState<StepDraft[]>([
    defaultStep("RAG_QUERY"),
    defaultStep("SUMMARIZE")
  ]);
  const [message, setMessage] = useState("");
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const initialNodes: Node[] = steps.map((step, index) => ({
    id: step.id,
    position: { x: index * 220, y: 40 },
    data: { label: `${index + 1}. ${step.name}` },
    type: "default"
  }));
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  async function load() {
    if (!organizationId) return;
    const [nextWorkflows, nextRuns] = await Promise.all([
      api.workflows(organizationId),
      api.workflowRuns(organizationId)
    ]);
    setWorkflows(nextWorkflows);
    setRuns(nextRuns);
  }

  useEffect(() => {
    load().catch((err) => setMessage(err instanceof Error ? err.message : "Could not load workflows"));
  }, [organizationId]);

  useEffect(() => {
    const hasActiveRun = runs.some((run) => ["QUEUED", "RUNNING"].includes(run.status));
    if (!hasActiveRun) return;
    const timer = window.setInterval(() => {
      load().catch((err) => setMessage(err instanceof Error ? err.message : "Could not refresh workflow runs"));
    }, 3000);
    return () => window.clearInterval(timer);
  }, [runs, organizationId]);

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const payloadSteps = steps.map(({ id: _id, ...step }) => step);
      await api.createWorkflow(organizationId, name, payloadSteps, { nodes, edges });
      setMessage("Workflow created");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not create workflow");
    }
  }

  async function run(workflow: Workflow) {
    setMessage("Workflow run queued");
    try {
      const firstRagStep = workflow.steps.find((step) => step.action_type === "RAG_QUERY");
      await api.runWorkflow(workflow.id, { query: firstRagStep?.config.query ?? "" });
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not run workflow");
    }
  }

  function updateStep(id: string, patch: Partial<StepDraft>) {
    setSteps((current) => current.map((step) => (step.id === id ? { ...step, ...patch } : step)));
    if (patch.name) {
      setNodes((current) => current.map((node) => (node.id === id ? { ...node, data: { ...node.data, label: patch.name } } : node)));
    }
  }

  function updateStepConfig(id: string, key: string, value: string) {
    setSteps((current) =>
      current.map((step) =>
        step.id === id ? { ...step, config: { ...step.config, [key]: value } } : step
      )
    );
  }

  function changeActionType(id: string, actionType: StepDraft["action_type"]) {
    setSteps((current) => current.map((step) => (step.id === id ? { ...defaultStep(actionType), id } : step)));
  }

  function addStep(actionType: StepDraft["action_type"]) {
    const step = defaultStep(actionType);
    setSteps((current) => [...current, step]);
    setNodes((current) => [
      ...current,
      {
        id: step.id,
        position: { x: current.length * 220, y: 40 },
        data: { label: step.name },
        type: "default"
      }
    ]);
  }

  function removeStep(id: string) {
    setSteps((current) => current.filter((item) => item.id !== id));
    setNodes((current) => current.filter((node) => node.id !== id));
    setEdges((current) => current.filter((edge) => edge.source !== id && edge.target !== id));
  }

  function onConnect(connection: Connection) {
    setEdges((current) => addEdge(connection, current));
  }

  function moveStep(index: number, direction: -1 | 1) {
    setSteps((current) => {
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= current.length) return current;
      const next = [...current];
      const [item] = next.splice(index, 1);
      next.splice(nextIndex, 0, item);
      return next;
    });
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <Panel title="Create Workflow">
        <form onSubmit={create} className="grid gap-4">
          <label className="grid gap-1 text-sm font-medium text-slate-700">
            Workflow name
            <input
              className="h-10 rounded-md border border-slate-300 px-3 text-sm font-normal"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>

          <div className="grid gap-3">
            {steps.map((step, index) => (
              <section key={step.id} className="rounded-lg border border-slate-200 p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-950">Step {index + 1}</p>
                  <div className="flex items-center gap-1">
                    <button type="button" title="Move step up" onClick={() => moveStep(index, -1)} className="rounded-md border border-slate-300 p-2 hover:bg-slate-100">
                      <ArrowUp size={15} />
                    </button>
                    <button type="button" title="Move step down" onClick={() => moveStep(index, 1)} className="rounded-md border border-slate-300 p-2 hover:bg-slate-100">
                      <ArrowDown size={15} />
                    </button>
                    <button
                      type="button"
                      title="Remove step"
                      onClick={() => removeStep(step.id)}
                      className="rounded-md border border-slate-300 p-2 text-red-700 hover:bg-red-50"
                      disabled={steps.length === 1}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                <div className="grid gap-3">
                  <input
                    className="h-10 rounded-md border border-slate-300 px-3 text-sm"
                    value={step.name}
                    onChange={(event) => updateStep(step.id, { name: event.target.value })}
                  />
                  <select
                    className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
                    value={step.action_type}
                    onChange={(event) => changeActionType(step.id, event.target.value as StepDraft["action_type"])}
                  >
                    {Object.entries(actionLabels).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <StepConfigEditor step={step} onChange={updateStepConfig} />
                </div>
              </section>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => addStep("RAG_QUERY")} className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-medium hover:bg-slate-100">
              <Plus size={16} />
              RAG Step
            </button>
            <button type="button" onClick={() => addStep("SUMMARIZE")} className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-medium hover:bg-slate-100">
              <Plus size={16} />
              Summary Step
            </button>
            <button type="button" onClick={() => addStep("WEBHOOK")} className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-medium hover:bg-slate-100">
              <Plus size={16} />
              Webhook Step
            </button>
          </div>

          <button title="Create workflow" className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-900 px-3 text-sm font-semibold text-white">
            <Plus size={16} />
            Create Workflow
          </button>
        </form>
        {message ? <p className="mt-3 text-sm text-slate-600">{message}</p> : null}
        <div className="mt-5 h-80 overflow-hidden rounded-lg border border-slate-200">
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
            <Background />
            <Controls />
          </ReactFlow>
        </div>
      </Panel>

      <Panel title="Workflow Runs">
        <div className="grid gap-3">
          {workflows.map((workflow) => (
            <article key={workflow.id} className="rounded-lg border border-slate-200 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h4 className="font-semibold text-slate-950">{workflow.name}</h4>
                  <p className="text-sm text-slate-500">{workflow.steps.length} step workflow</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {workflow.steps.map((step) => actionLabels[step.action_type as StepDraft["action_type"]] ?? step.action_type).join(" -> ")}
                  </p>
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

        <div className="mt-5 grid gap-3">
          {runs.map((run) => (
            <article key={run.id} className="rounded-lg border border-slate-200 p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-slate-950">Run {run.id.slice(0, 8)}</p>
                  <p className="text-xs text-slate-500">{new Date(run.created_at).toLocaleString()}</p>
                </div>
                <span className={`w-fit rounded-md px-2 py-1 text-xs font-semibold ${runStatusClass(run.status)}`}>
                  {run.status}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{run.progress_percent}% {run.current_step}</p>
              {run.celery_task_id ? <p className="mt-1 text-xs text-slate-400">Task {run.celery_task_id.slice(0, 8)}</p> : null}
              {run.error_message ? <p className="mt-3 text-sm text-red-700">{run.error_message}</p> : null}
              {Object.keys(run.outputs || {}).length ? (
                <pre className="mt-3 max-h-72 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-200">
                  {JSON.stringify(run.outputs, null, 2)}
                </pre>
              ) : null}
            </article>
          ))}
          {!runs.length ? <p className="text-sm text-slate-500">No workflow runs yet.</p> : null}
        </div>
      </Panel>
    </div>
  );
}

function StepConfigEditor({
  step,
  onChange
}: {
  step: StepDraft;
  onChange: (id: string, key: string, value: string) => void;
}) {
  if (step.action_type === "RAG_QUERY") {
    return (
      <textarea
        className="min-h-24 rounded-md border border-slate-300 p-3 text-sm"
        value={String(step.config.query ?? "")}
        onChange={(event) => onChange(step.id, "query", event.target.value)}
        placeholder="Question to ask against organization documents"
      />
    );
  }
  if (step.action_type === "CHAT") {
    return (
      <textarea
        className="min-h-24 rounded-md border border-slate-300 p-3 text-sm"
        value={String(step.config.message ?? "")}
        onChange={(event) => onChange(step.id, "message", event.target.value)}
        placeholder="Message to send to the routed chat model. Leave blank to use previous output."
      />
    );
  }
  if (step.action_type === "SUMMARIZE" || step.action_type === "SUMMARIZE_TEXT") {
    return (
      <textarea
        className="min-h-24 rounded-md border border-slate-300 p-3 text-sm"
        value={String(step.config.text ?? "")}
        onChange={(event) => onChange(step.id, "text", event.target.value)}
        placeholder="Optional text. Leave blank to summarize the previous step output."
      />
    );
  }
  if (step.action_type === "CONDITION") {
    return (
      <input
        className="h-10 rounded-md border border-slate-300 px-3 text-sm"
        value={String(step.config.contains ?? "")}
        onChange={(event) => onChange(step.id, "contains", event.target.value)}
        placeholder="Continue marker text"
      />
    );
  }
  if (step.action_type === "DELAY") {
    return (
      <input
        className="h-10 rounded-md border border-slate-300 px-3 text-sm"
        value={String(step.config.seconds ?? "")}
        onChange={(event) => onChange(step.id, "seconds", event.target.value)}
        placeholder="Delay seconds"
      />
    );
  }
  if (step.action_type === "HUMAN_APPROVAL") {
    return <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">Placeholder node for future approval queues.</p>;
  }
  return (
    <input
      className="h-10 rounded-md border border-slate-300 px-3 text-sm"
      value={String(step.config.url ?? "")}
      onChange={(event) => onChange(step.id, "url", event.target.value)}
      placeholder="https://example.com/webhook"
    />
  );
}

function runStatusClass(status: string) {
  if (status === "COMPLETED") return "bg-emerald-100 text-emerald-800";
  if (status === "FAILED") return "bg-red-100 text-red-800";
  if (status === "RUNNING") return "bg-sky-100 text-sky-800";
  return "bg-amber-100 text-amber-800";
}
