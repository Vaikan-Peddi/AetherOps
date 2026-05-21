import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import ai, auth, chat, connectors, conversations, documents, evaluation, observability, organizations, rag, tasks, workflows
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
from app.services.cache_service import cache
from app.services.observability.metrics import metrics
from app.services.qdrant_service import qdrant_service

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    client_host = request.client.host if request.client else "unknown"
    rate_key = f"aetherops:rate:{client_host}:{int(time.time() // 60)}"
    try:
        count = cache.client.incr(rate_key)
        cache.client.expire(rate_key, 65)
        if count > settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"detail": "Rate limit exceeded"})
    except Exception:
        pass

    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    if request.url.path.startswith(settings.API_V1_PREFIX):
        latency_ms = int((time.perf_counter() - started) * 1000)
        metrics.increment("aetherops_http_requests", {"method": request.method, "status": str(response.status_code)})
        metrics.observe_latency("aetherops_http_request", latency_ms, {"method": request.method})
        db = SessionLocal()
        try:
            db.add(
                AuditLog(
                    user_id=getattr(request.state, "user_id", None),
                    organization_id=getattr(request.state, "organization_id", None),
                    action=f"{request.method} {request.url.path}",
                    endpoint=request.url.path,
                    latency_ms=latency_ms,
                    metadata_json={"status_code": response.status_code, "request_id": request_id},
                )
            )
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    return response


@app.on_event("startup")
def startup() -> None:
    try:
        qdrant_service.ensure_collection()
    except Exception:
        # Qdrant may still be coming up when Docker starts the API; ingestion/query paths retry.
        pass


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(organizations.router, prefix=settings.API_V1_PREFIX)
app.include_router(connectors.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(rag.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(conversations.router, prefix=settings.API_V1_PREFIX)
app.include_router(workflows.router, prefix=settings.API_V1_PREFIX)
app.include_router(observability.router, prefix=settings.API_V1_PREFIX)
app.include_router(evaluation.router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)
