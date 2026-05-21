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

AetherOps is a production-grade Phase 1 foundation for Forward Deployed AI work. It provides the core building blocks for an enterprise AI operations platform: tenant-aware authentication, RBAC, document ingestion, vector search, RAG, workflow execution, LLM provider abstraction, and observability.

This is intentionally not a toy demo. Phase 1 focuses on clean architecture and runnable infrastructure so future phases can add connectors, advanced agents, streaming UX, enterprise identity, and production deployment hardening without rewriting the system.

## What You Can Do Today

- Register and log in with JWT authentication.
- Create and access organizations.
- Enforce organization-level isolation across documents, workflows, queries, and logs.
- Upload PDF documents and ingest them in the background.
- Extract text with PyMuPDF.
- Chunk and embed document text with `sentence-transformers/all-MiniLM-L6-v2`.
- Store vectors and metadata in Qdrant.
- Ask RAG questions over uploaded documents.
- Chat with a local Ollama model through a provider abstraction.
- Create and run simple async workflows.
- View a tenant-scoped observability summary.
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
│   ├── LLM provider abstraction
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

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend API | Python 3.11, FastAPI, Pydantic v2 |
| Database | PostgreSQL, SQLAlchemy 2.0, Alembic |
| Auth | JWT, passlib, bcrypt |
| RAG | PyMuPDF, sentence-transformers, Qdrant |
| LLM | Ollama by default, provider abstraction for OpenAI, Anthropic, Groq, vLLM |
| Async Workflows | Celery, Redis |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
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
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Frontend API base URL |

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

OpenAI and Anthropic are intentionally stubbed in Phase 1. The structure is ready for OpenAI, Anthropic, Groq, local vLLM, or internal inference gateways.

## Workflow Automation

Phase 1 workflows run through Celery and support three action types:

- `RAG_QUERY`
- `SUMMARIZE_TEXT`
- `SEND_WEBHOOK_PLACEHOLDER`

Workflow APIs create a workflow definition, enqueue a run, and let the worker execute steps in order. This establishes the execution model without overbuilding a visual workflow engine too early.

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

### Workflows

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/workflows` | Create workflow |
| `GET` | `/api/v1/workflows?organization_id=...` | List workflows |
| `POST` | `/api/v1/workflows/{id}/run` | Enqueue workflow run |
| `GET` | `/api/v1/workflows/runs/{run_id}` | Inspect workflow run |

### Observability

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/observability/summary?organization_id=...` | Tenant summary metrics |

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

## Phase 1 Limitations

- Background ingestion is implemented, but progress reporting is status-based rather than event-based.
- The frontend does not yet expose full membership management.
- OpenAI and Anthropic providers are placeholder implementations.
- RAG prompting is intentionally minimal.
- Token counting is approximate.
- Workflow execution is sequential and has basic error handling.
- No SSO, SCIM, audit export, rate limiting, or production secrets manager yet.
- No connector runtime has been implemented yet.

## Roadmap

- Background document ingestion with progress updates.
- Streaming RAG and chat responses in the frontend.
- OpenAI, Anthropic, Groq, and vLLM provider implementations.
- Connector framework for SharePoint, Google Drive, Slack, Jira, GitHub, Confluence, S3, and databases.
- Visual workflow builder with retries, schedules, approvals, and branching.
- Agent orchestration with tool permissions and run traces.
- Fine-grained policy engine for RBAC and data access.
- SSO/SAML/OIDC, invitations, SCIM provisioning.
- Model cost tracking, trace export, dashboards, and alerting.
- Production deployment profiles for Kubernetes and managed cloud services.

## License

No license has been selected yet. Add a license before distributing or using AetherOps outside your organization.
