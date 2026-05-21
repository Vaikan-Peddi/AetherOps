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
  celery_task_id?: string | null;
  progress_percent: number;
  current_step?: string | null;
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

export type Conversation = {
  id: string;
  organization_id: string;
  title: string;
  summary?: string | null;
  created_at: string;
  updated_at: string;
};

export type ConversationMessage = {
  id: string;
  conversation_id: string;
  role: "SYSTEM" | "USER" | "ASSISTANT" | "TOOL";
  content: string;
  provider?: string | null;
  model?: string | null;
  token_count: number;
  created_at: string;
};

export type WorkflowStepInput = {
  name: string;
  action_type: "RAG_QUERY" | "SUMMARIZE" | "SUMMARIZE_TEXT" | "CHAT" | "WEBHOOK" | "SEND_WEBHOOK_PLACEHOLDER" | "CONDITION" | "DELAY" | "HUMAN_APPROVAL";
  config: Record<string, unknown>;
};

export type WorkflowRun = {
  id: string;
  workflow_id: string;
  organization_id: string;
  celery_task_id?: string | null;
  status: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  progress_percent: number;
  current_step?: string | null;
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
  avg_latency_ms: number;
  total_tokens: number;
  provider_usage: Record<string, number>;
  model_distribution: Record<string, number>;
  workflow_status: Record<string, number>;
};

export type ProviderHealth = {
  ok: boolean;
  provider: string;
  model: string;
  latency_ms?: number | null;
  error?: string | null;
};

export type ConnectorInfo = {
  name: string;
  oauth_scopes: string[];
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

  async streamRequest(
    path: string,
    payload: unknown,
    onEvent: (event: { type: string; token?: string; error?: string; provider?: string; model?: string; conversation_id?: string }) => void
  ) {
    const headers = new Headers({ "Content-Type": "application/json" });
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload)
    });
    if (!response.ok || !response.body) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `Stream failed with ${response.status}`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const event of events) {
        const line = event.split("\n").find((item) => item.startsWith("data: "));
        if (line) onEvent(JSON.parse(line.slice(6)));
      }
    }
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

  streamChat(payload: {
    organization_id: string;
    message: string;
    conversation_id?: string;
    task_type?: string;
    provider?: string;
    model?: string;
  }, onEvent: Parameters<ApiClient["streamRequest"]>[2]) {
    return this.streamRequest("/chat/stream", payload, onEvent);
  }

  conversations(organizationId: string) {
    return this.request<Conversation[]>(`/conversations?organization_id=${organizationId}`);
  }

  createConversation(organizationId: string, title = "New conversation") {
    return this.request<Conversation>("/conversations", {
      method: "POST",
      body: JSON.stringify({ organization_id: organizationId, title })
    });
  }

  messages(organizationId: string, conversationId: string) {
    return this.request<ConversationMessage[]>(`/conversations/${conversationId}/messages?organization_id=${organizationId}`);
  }

  workflows(organizationId: string) {
    return this.request<Workflow[]>(`/workflows?organization_id=${organizationId}`);
  }

  createWorkflow(organizationId: string, name: string, steps: WorkflowStepInput[], graphJson: Record<string, unknown> = {}) {
    return this.request<Workflow>("/workflows", {
      method: "POST",
      body: JSON.stringify({
        organization_id: organizationId,
        name,
        description: "Phase 1 workflow",
        steps,
        graph_json: graphJson
      })
    });
  }

  runEvaluation(payload: { organization_id: string; question: string; answer: string; contexts: string[] }) {
    return this.request<{ metrics: Record<string, number> }>("/evaluation/run", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  aiRoutes() {
    return this.request<Record<string, { provider: string; model: string }>>("/ai/routes");
  }

  providerHealth() {
    return this.request<{ providers: ProviderHealth[]; enabled: string[] }>("/ai/providers/health");
  }

  connectors() {
    return this.request<{ connectors: ConnectorInfo[] }>("/connectors");
  }

  taskStatus(taskId: string) {
    return this.request<{ task_id: string; state: string; ready: boolean; successful: boolean; failed: boolean }>(`/tasks/${taskId}`);
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
