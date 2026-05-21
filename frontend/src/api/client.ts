const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type User = {
  id: string;
  email: string;
  full_name?: string | null;
};

export type Organization = {
  id: string;
  name: string;
  created_at: string;
};

export type DocumentRecord = {
  id: string;
  organization_id: string;
  filename: string;
  status: string;
  page_count: number;
  chunk_count: number;
  created_at: string;
  error_message?: string | null;
};

export type Workflow = {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  created_at: string;
  steps: Array<{
    id: string;
    order_index: number;
    name: string;
    action_type: string;
    config: Record<string, unknown>;
  }>;
};

export type WorkflowStepInput = {
  name: string;
  action_type: "RAG_QUERY" | "SUMMARIZE_TEXT" | "SEND_WEBHOOK_PLACEHOLDER";
  config: Record<string, unknown>;
};

export type WorkflowRun = {
  id: string;
  workflow_id: string;
  organization_id: string;
  status: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
};

export type Summary = {
  total_documents: number;
  total_queries: number;
  total_workflows: number;
  total_workflow_runs: number;
};

class ApiClient {
  token: string | null = localStorage.getItem("eaio_token");

  setToken(token: string | null) {
    this.token = token;
    if (token) localStorage.setItem("eaio_token", token);
    else localStorage.removeItem("eaio_token");
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);
    if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed with ${response.status}`);
    }
    return response.json();
  }

  register(payload: { email: string; password: string; full_name?: string; organization_name?: string }) {
    return this.request<{ access_token: string; user: User; organization_id?: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  login(payload: { email: string; password: string }) {
    return this.request<{ access_token: string; user: User; organization_id?: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  me() {
    return this.request<User>("/auth/me");
  }

  organizations() {
    return this.request<Organization[]>("/organizations");
  }

  createOrganization(name: string) {
    return this.request<Organization>("/organizations", { method: "POST", body: JSON.stringify({ name }) });
  }

  documents(organizationId: string) {
    return this.request<DocumentRecord[]>(`/documents?organization_id=${organizationId}`);
  }

  uploadDocument(organizationId: string, file: File) {
    const form = new FormData();
    form.append("organization_id", organizationId);
    form.append("file", file);
    return this.request<DocumentRecord>("/documents/upload", { method: "POST", body: form });
  }

  ragQuery(organizationId: string, query: string) {
    return this.request<{ answer: string; sources: Array<{ filename: string; chunk_text: string; score: number }> }>(
      "/rag/query",
      { method: "POST", body: JSON.stringify({ organization_id: organizationId, query }) }
    );
  }

  workflows(organizationId: string) {
    return this.request<Workflow[]>(`/workflows?organization_id=${organizationId}`);
  }

  createWorkflow(organizationId: string, name: string, steps: WorkflowStepInput[]) {
    return this.request<Workflow>("/workflows", {
      method: "POST",
      body: JSON.stringify({
        organization_id: organizationId,
        name,
        description: "Phase 1 workflow",
        steps
      })
    });
  }

  runWorkflow(workflowId: string, inputs: Record<string, unknown>) {
    return this.request<WorkflowRun>(`/workflows/${workflowId}/run`, {
      method: "POST",
      body: JSON.stringify({ inputs })
    });
  }

  getRun(runId: string) {
    return this.request<WorkflowRun>(`/workflows/runs/${runId}`);
  }

  workflowRuns(organizationId: string) {
    return this.request<WorkflowRun[]>(`/workflows/runs?organization_id=${organizationId}`);
  }

  summary(organizationId: string) {
    return this.request<Summary>(`/observability/summary?organization_id=${organizationId}`);
  }
}

export const api = new ApiClient();
