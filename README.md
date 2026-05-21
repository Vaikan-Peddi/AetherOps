<p align="center">
  <img src="assets/aetherops-logo.svg" alt="AetherOps logo" width="560" />
</p>

<p align="center">
  <strong>Multi-tenant AI operations platform for enterprise document intelligence, RAG, workflow automation, and agent-ready orchestration.</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#api-overview">API</a> ·
  <a href="#roadmap">Roadmap</a>
</p>

---

# AetherOps

AetherOps is a production-grade foundation for Forward Deployed AI work. It provides the core building blocks for an enterprise AI operations platform: tenant-aware authentication, RBAC, document ingestion, vector search, advanced RAG, streaming chat, workflow execution, LLM routing, connector scaffolds, evaluation, and observability.

This is intentionally not a toy demo. Phase 2 adds platform primitives that move AetherOps beyond a basic RAG app while preserving the Phase 1 architecture.

## What You Can Do Today

- Register and log in with JWT authentication.
- Create and access organizations.
- Enforce organization-level isolation across documents, workflows, queries, and logs.
- Upload PDF documents and ingest them in the background.
- Extract text with PyMuPDF.
- Chunk and embed document text with `sentence-transformers/all-MiniLM-L6-v2`.
- Store vectors and metadata in Qdrant.
- Ask RAG questions over uploaded documents.
- Stream chat responses from Ollama through the AI Gateway.
- Route tasks to `llama3.1:8b`, `qwen2.5-coder:7b`, or `deepseek-r1:8b`.
- Persist conversations and message memory.
- Create and run agent-style workflows with a React Flow graph foundation.
- View tenant-scoped observability and AI usage analytics.
- Run lightweight RAG evaluation metrics.
- Run the full stack with Docker Compose.

## Architecture

```text
AetherOps
├── frontend
│   └── React + Vite + TypeScript + Tailwind
├── backend
│   ├── FastAPI API
│   ├── SQLAlchemy 2.0 models
│   ├── Alembic migrations
│   ├── service layer
│   ├── AI Gateway + LLM provider registry
│   ├── RAG pipeline modules
│   ├── connector scaffolds
│   ├── evaluation services
│   └── Celery worker
├── postgres
│   └── users, organizations, RBAC, documents, workflows, logs
├── qdrant
│   └── document chunk vectors
├── redis
│   └── Celery broker and result backend
└── ollama
    └── local macOS inference via host.docker.internal
```

### System Flowchart

```mermaid
flowchart TB
  user["Operator / Enterprise User"]

  subgraph frontend["Frontend: React + Vite + TypeScript"]
    shell["App Shell + Sidebar"]
    auth_ui["Login / Register"]
    chat_ui["AI Chat<br/>Streaming Markdown UI"]
    docs_ui["Documents<br/>Upload + Ingestion Progress"]
    rag_ui["RAG Query"]
    workflow_ui["Workflow Builder<br/>React Flow Graph Editor"]
    obs_ui["Observability Dashboard"]
    conv_ui["Conversations"]
    settings_ui["Settings / Routing"]
  end

  subgraph api["Backend API: FastAPI /api/v1"]
    auth_api["Auth API<br/>JWT + Current User"]
    org_api["Organizations API<br/>Tenant + Membership Checks"]
    chat_api["Chat API<br/>/chat + /chat/stream SSE"]
    docs_api["Documents API<br/>PDF Validation + Upload"]
    rag_api["RAG API<br/>Query + Sources"]
    workflow_api["Workflow API<br/>Definitions + Runs"]
    conv_api["Conversations API<br/>History + Messages"]
    eval_api["Evaluation API<br/>Heuristic RAG Eval"]
    obs_api["Observability API<br/>Summary + Metrics"]
  end

  subgraph core["Core Backend Foundations"]
    deps["Dependency Injection<br/>DB Session + Auth Context"]
    rbac["RBAC<br/>OWNER / ADMIN / MEMBER / VIEWER"]
    audit["Audit Middleware<br/>Request ID + Latency + AuditLog"]
    rate_limit["Rate Limiting<br/>Redis-backed per-minute guard"]
  end

  subgraph ai["AI Systems Layer"]
    gateway["AI Gateway<br/>Task Routing + Fallback"]
    registry["LLM Provider Registry"]
    ollama["Ollama Provider<br/>Local HTTP API"]
    openai["OpenAI Provider<br/>Scaffold"]
    anthropic["Anthropic Provider<br/>Scaffold"]
    routing["Model Routing<br/>CHAT/RAG -> llama3.1<br/>CODING -> qwen2.5-coder<br/>REASONING -> deepseek-r1"]
  end

  subgraph rag["Advanced RAG Pipeline"]
    chunking["Chunking<br/>Paragraph-aware overlap"]
    embeddings["Embedding Service<br/>all-MiniLM-L6-v2"]
    retrieval["Retrieval<br/>Qdrant search + metadata filter"]
    reranker["Reranker<br/>Lightweight relevance scoring"]
    citations["Citation Builder<br/>Inline source references"]
    rag_service["RAG Service<br/>Prompt assembly + AI Gateway call"]
  end

  subgraph async["Async Execution"]
    celery["Celery Worker"]
    ingest_task["Document Ingestion Task<br/>Extract -> Chunk -> Embed -> Upsert"]
    workflow_task["Workflow Run Task<br/>Sequential Agent Execution"]
    retries["Retry / Status Foundation<br/>progress_percent + current_step"]
  end

  subgraph agents["Agent Workflow Layer"]
    planner["Planner Agent<br/>Step ordering foundation"]
    retrieval_agent["Retrieval Agent<br/>RAG tool foundation"]
    execution_agent["Execution Agent<br/>Connector/tool execution"]
    node_types["Node Types<br/>RAG_QUERY / SUMMARIZE / CHAT / WEBHOOK<br/>CONDITION / DELAY / HUMAN_APPROVAL"]
  end

  subgraph connectors["Connector Architecture"]
    connector_base["Connector Base<br/>OAuth-ready interface"]
    gmail["Gmail Connector<br/>Scaffold"]
    slack["Slack Connector<br/>Scaffold"]
    github["GitHub Connector<br/>Scaffold"]
  end

  subgraph data["Persistence + Infrastructure"]
    postgres[("PostgreSQL<br/>Users, Orgs, RBAC, Documents,<br/>Conversations, Workflows, Logs, Eval")]
    qdrant[("Qdrant<br/>Vector Collection")]
    redis[("Redis<br/>Celery Broker + Cache + Rate Limit")]
    storage[("Shared Storage Volume<br/>Uploaded PDFs")]
    ollama_host["Host Ollama<br/>http://host.docker.internal:11434"]
  end

  subgraph observability["Observability + Evaluation"]
    usage["AIUsageLog<br/>tokens, model, provider, latency"]
    metrics["Prometheus-style Metrics<br/>/observability/metrics"]
    eval_service["Evaluation Service<br/>faithfulness, relevance,<br/>retrieval precision, hallucination risk"]
  end

  user --> shell
  shell --> auth_ui
  shell --> chat_ui
  shell --> docs_ui
  shell --> rag_ui
  shell --> workflow_ui
  shell --> obs_ui
  shell --> conv_ui
  shell --> settings_ui

  auth_ui --> auth_api
  chat_ui --> chat_api
  docs_ui --> docs_api
  rag_ui --> rag_api
  workflow_ui --> workflow_api
  obs_ui --> obs_api
  conv_ui --> conv_api

  auth_api --> deps
  org_api --> rbac
  chat_api --> deps
  docs_api --> deps
  rag_api --> deps
  workflow_api --> deps
  conv_api --> deps
  eval_api --> deps
  obs_api --> deps
  deps --> rbac
  audit --> postgres
  rate_limit --> redis

  auth_api --> postgres
  org_api --> postgres
  conv_api --> postgres

  chat_api --> gateway
  chat_api --> postgres
  gateway --> routing
  gateway --> registry
  registry --> ollama
  registry --> openai
  registry --> anthropic
  ollama --> ollama_host

  docs_api --> storage
  docs_api --> postgres
  docs_api --> celery
  celery --> ingest_task
  ingest_task --> storage
  ingest_task --> chunking
  chunking --> embeddings
  embeddings --> qdrant
  ingest_task --> postgres

  rag_api --> rag_service
  rag_service --> retrieval
  retrieval --> redis
  retrieval --> embeddings
  retrieval --> qdrant
  retrieval --> reranker
  reranker --> citations
  citations --> gateway
  rag_service --> usage

  workflow_api --> postgres
  workflow_api --> celery
  celery --> workflow_task
  workflow_task --> planner
  planner --> node_types
  workflow_task --> retrieval_agent
  workflow_task --> execution_agent
  retrieval_agent --> rag_service
  execution_agent --> connector_base
  connector_base --> gmail
  connector_base --> slack
  connector_base --> github
  workflow_task --> retries
  workflow_task --> postgres

  eval_api --> eval_service
  eval_service --> postgres
  obs_api --> usage
  obs_api --> metrics
  usage --> postgres
  metrics --> obs_ui
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend API | Python 3.11, FastAPI, Pydantic v2 |
| Database | PostgreSQL, SQLAlchemy 2.0, Alembic |
| Auth | JWT, passlib, bcrypt |
| RAG | PyMuPDF, sentence-transformers, Qdrant |
| LLM | Ollama provider, provider registry, OpenAI/Anthropic scaffolds |
| Async Workflows | Celery, Redis |
| Frontend | React, Vite, TypeScript, Tailwind CSS, React Flow, React Markdown |
| Infra | Docker Compose |

## Repository Structure

```text
.
├── assets/
│   └── aetherops-logo.svg
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── migrations/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── llm/
│   │   └── workers/
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── logo.svg
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── pages/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### 1. Start Ollama on macOS

AetherOps expects Ollama to run on the host machine and exposes it to Docker through `host.docker.internal`.

```bash
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-r1:8b
ollama serve
```

If Ollama is already running as a macOS app or launch service, just pull the model.

### 2. Configure Environment

```bash
cp .env.example .env
```

The Compose file has safe local defaults, so `.env` is optional for first boot. For real usage, change `SECRET_KEY`.

### 3. Run the Stack

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Qdrant dashboard: http://localhost:6333/dashboard

## First Run Workflow

1. Open http://localhost:5173.
2. Register a user.
3. Use the default organization or create a new one.
4. Upload a PDF from the Documents page.
5. Ask a question on the RAG Query page.
6. Create a workflow on the Workflows page.
7. Run the workflow and inspect its status.
8. View tenant metrics on the Observability page.

## Configuration

Important environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PROJECT_NAME` | `AetherOps` | FastAPI project title |
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@postgres:5432/aetherops` | Backend database connection |
| `POSTGRES_DB` | `aetherops` | Local Postgres database |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | Celery result backend |
| `SECRET_KEY` | local placeholder | JWT signing secret |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant service URL |
| `QDRANT_COLLECTION` | `aetherops_document_chunks` | Vector collection |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `DEFAULT_LLM_PROVIDER` | `ollama` | Active LLM provider |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Host Ollama URL from Docker |
| `OLLAMA_MODEL` | `llama3.1:8b` | Default local model |
| `OLLAMA_CODING_MODEL` | `qwen2.5-coder:7b` | Coding task route |
| `OLLAMA_REASONING_MODEL` | `deepseek-r1:8b` | Reasoning task route |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Frontend API base URL |

## AI Gateway and Model Routing

The AI Gateway sits above provider implementations and routes work by task type:

```text
CHAT          -> llama3.1:8b
RAG           -> llama3.1:8b
CODING        -> qwen2.5-coder:7b
REASONING     -> deepseek-r1:8b
SUMMARIZATION -> llama3.1:8b
```

Provider files live in `backend/app/services/llm/`:

- `base.py`: common interface with `generate`, `stream_generate`, `embeddings`, and `health_check`.
- `registry.py`: provider registry and dynamic lookup.
- `ollama_provider.py`: working local provider.
- `openai_provider.py`: cloud provider scaffold.
- `anthropic_provider.py`: cloud provider scaffold.

## Streaming Chat and Conversation Memory

AetherOps supports streaming chat through:

- `POST /api/v1/chat/stream`
- Persistent `Conversation` and `Message` records.
- Organization-isolated memory.
- Frontend incremental rendering with markdown support.

## Phase 2 RAG Pipeline

The RAG implementation is split into modular services:

- `chunking.py`: paragraph-aware chunking foundation.
- `retrieval.py`: Qdrant retrieval with Redis caching and metadata filter hooks.
- `reranker.py`: lightweight overlap-based reranking.
- `citation_builder.py`: source citation formatting.

Retrieval now has a hybrid foundation: Qdrant vector search is combined with tenant-scoped Postgres lexical matching, then merged, deduplicated, reranked, cached, and converted into citations.

## Agent Workflows and Visual Builder

Workflow support now includes agent-oriented node types:

- `RAG_QUERY`
- `SUMMARIZE`
- `CHAT`
- `WEBHOOK`
- `CONDITION`
- `DELAY`
- `HUMAN_APPROVAL`

The frontend includes a React Flow graph foundation and saves `graph_json` with workflow definitions. The execution engine remains sequential in this phase, with placeholders for branching and approval queues.

## Connectors

Connector scaffolds live in `backend/app/connectors/`:

- Gmail
- Slack
- GitHub

They expose an OAuth-ready execution abstraction without implementing provider OAuth yet.

## Evaluation and Observability

Evaluation endpoint:

- `POST /api/v1/evaluation/run`

Initial metrics:

- faithfulness
- answer relevance
- retrieval precision
- retrieval recall placeholder
- hallucination risk placeholder

Observability now tracks request/model/retrieval latency, token counts, model distribution, provider usage, workflow status, and exposes a Prometheus-compatible foundation at `/api/v1/observability/metrics`.

## Screenshots

Add screenshots here as the UI stabilizes:

- AI Chat
- Documents and ingestion progress
- Workflow graph builder
- Observability dashboard

## Multi-Tenant Model

AetherOps uses a tenant-first data model:

- `User`: authenticated platform user.
- `Organization`: tenant boundary.
- `OrganizationMembership`: user-to-organization relationship.
- `Role`: RBAC role for a membership.
- `Document`: uploaded file metadata scoped to an organization.
- `Workflow`: automation definition scoped to an organization.
- `WorkflowRun`: execution record scoped to an organization.
- `AuditLog`: request and action trace.
- `AIUsageLog`: AI/RAG usage trace.

Every document, workflow, workflow run, RAG query, and usage summary is filtered by `organization_id`.

## RBAC

| Role | Capabilities |
| --- | --- |
| `OWNER` | Full organization access, document upload, workflow execution, membership management |
| `ADMIN` | Document upload, workflow creation/execution, read/query access |
| `MEMBER` | RAG query access and workflow creation/execution |
| `VIEWER` | Read/query access |

Phase 1 keeps RBAC intentionally simple but centralized so policy can expand without spreading permission logic across the codebase.

## Document Intelligence and RAG

Upload flow:

1. API receives a PDF through `POST /api/v1/documents/upload`.
2. The file is persisted to shared backend/worker storage.
3. Metadata is stored in Postgres with `PROCESSING` status.
4. A Celery task performs ingestion in the background.
5. PyMuPDF extracts page text.
6. Text is split into overlapping chunks.
7. sentence-transformers generates normalized embeddings.
8. Qdrant stores vectors with metadata:
   - `organization_id`
   - `document_id`
   - `filename`
   - `page_number`
   - `chunk_index`
   - `chunk_text`
9. Document status is updated to `READY` or `FAILED`.

Query flow:

1. API receives `POST /api/v1/rag/query`.
2. Query text is embedded.
3. Qdrant search is filtered by `organization_id`.
4. Retrieved chunks are passed to the active LLM provider.
5. Response includes an answer and source chunks.

## LLM Provider Layer

The default provider is Ollama:

```text
backend/app/services/llm/
├── base.py
├── ollama_provider.py
├── openai_provider.py
└── anthropic_provider.py
```

Provider interface:

- `generate()`
- `stream_generate()`
- `embeddings()`

Ollama is fully wired for local inference. OpenAI and Anthropic are provider scaffolds with the same interface, so Groq, local vLLM, or internal inference gateways can be added without changing the API layer.

## Workflow Automation

Workflows run through Celery and support agent-oriented action types:

- `RAG_QUERY`
- `SUMMARIZE` / `SUMMARIZE_TEXT`
- `CHAT`
- `WEBHOOK` / `SEND_WEBHOOK_PLACEHOLDER`
- `CONDITION`
- `DELAY`
- `HUMAN_APPROVAL`

Workflow APIs create a workflow definition, enqueue a run, persist the Celery task ID, and let the worker execute steps in order. The current executor includes retry-friendly task configuration, progress fields, delay nodes, basic condition-driven skip behavior, and placeholders for human approval queues.

## Observability

AetherOps records:

- Audit events for API requests.
- AI usage events for chat, RAG, and workflow-backed AI calls.
- Latency where available.
- Placeholder token counts.
- Model/provider metadata.
- Optional workflow run linkage.

The summary endpoint reports:

- total documents
- total AI queries
- total workflows
- total workflow runs
- average latency
- token totals
- provider usage
- model distribution
- workflow run status

## API Overview

### Auth

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Register user, create default organization, return JWT |
| `POST` | `/api/v1/auth/login` | Log in and return JWT |
| `GET` | `/api/v1/auth/me` | Return current user |

### Organizations

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/organizations` | Create organization |
| `GET` | `/api/v1/organizations` | List current user's organizations |
| `GET` | `/api/v1/organizations/{organization_id}/members` | List members, owner only |
| `POST` | `/api/v1/organizations/{organization_id}/members` | Add or update member, owner only |

### Documents

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/documents/upload` | Upload and ingest PDF |
| `GET` | `/api/v1/documents?organization_id=...` | List organization documents |

### RAG and Chat

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/rag/query` | Retrieve document chunks and generate answer |
| `POST` | `/api/v1/chat` | Direct Ollama-backed chat |
| `POST` | `/api/v1/chat/stream` | Streaming chat response with SSE-style data frames |

Example RAG request:

```json
{
  "organization_id": "00000000-0000-0000-0000-000000000000",
  "query": "What are the key risks in this document?"
}
```

Example RAG response:

```json
{
  "answer": "The document highlights operational, compliance, and vendor risks...",
  "sources": [
    {
      "document_id": "00000000-0000-0000-0000-000000000000",
      "filename": "policy.pdf",
      "chunk_text": "Relevant source text...",
      "score": 0.87
    }
  ]
}
```

Example chat request:

```json
{
  "organization_id": "00000000-0000-0000-0000-000000000000",
  "message": "Draft a short executive summary of our AI operations posture."
}
```

### Conversations

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/conversations` | Create persistent conversation |
| `GET` | `/api/v1/conversations?organization_id=...` | List organization conversations |
| `GET` | `/api/v1/conversations/{conversation_id}/messages?organization_id=...` | Retrieve conversation messages |

### AI Gateway

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/ai/routes` | Inspect configured task-to-model routing |
| `GET` | `/api/v1/ai/providers/health` | Check enabled provider health |

### Workflows

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/workflows` | Create workflow |
| `GET` | `/api/v1/workflows?organization_id=...` | List workflows |
| `POST` | `/api/v1/workflows/{id}/run` | Enqueue workflow run |
| `GET` | `/api/v1/workflows/runs?organization_id=...` | List workflow runs |
| `GET` | `/api/v1/workflows/runs/{run_id}` | Inspect workflow run |

### Tasks

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/tasks/{task_id}` | Tenant-checked Celery task status for ingestion and workflow runs |

### Observability

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/observability/summary?organization_id=...` | Tenant summary metrics |
| `GET` | `/api/v1/observability/metrics` | Prometheus-style metrics exposition |

### Evaluation

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/evaluation/run` | Run lightweight RAG quality heuristics |

### Connectors

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/connectors` | List registered connector scaffolds and OAuth scopes |
| `POST` | `/api/v1/connectors/{connector_name}/execute` | Execute placeholder connector action through the registry |

## Development

Run backend locally:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run frontend locally:

```bash
cd frontend
npm install
npm run dev
```

Run worker locally:

```bash
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

## Current Limitations

- Background ingestion and workflows are durable Celery jobs, but progress updates are polled rather than pushed over WebSockets/SSE.
- The frontend does not yet expose full membership management.
- OpenAI and Anthropic providers are placeholder implementations.
- RAG uses hybrid retrieval and lightweight reranking, but not BM25 indexes, cross-encoder rerankers, or RAGAS yet.
- Token counting is approximate.
- Workflow execution is sequential with basic branching foundations, not a full DAG scheduler.
- Rate limiting is local Redis-based and intentionally simple.
- No SSO, SCIM, audit export, billing, or production secrets manager yet.
- Connector OAuth and real external API execution are not implemented yet.

## Roadmap

- Push-based ingestion and workflow progress updates.
- Streaming RAG responses with source updates.
- OpenAI, Anthropic, Groq, and vLLM provider implementations.
- Connector framework for SharePoint, Google Drive, Slack, Jira, GitHub, Confluence, S3, and databases.
- Visual workflow builder with full DAG execution, retries, schedules, approvals, and branching.
- Agent orchestration with tool permissions and run traces.
- Fine-grained policy engine for RBAC and data access.
- SSO/SAML/OIDC, invitations, SCIM provisioning.
- Model cost tracking, trace export, dashboards, and alerting.
- Production deployment profiles for Kubernetes and managed cloud services.

## License

No license has been selected yet. Add a license before distributing or using AetherOps outside your organization.
