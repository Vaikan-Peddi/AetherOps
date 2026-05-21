import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, chat, documents, observability, organizations, rag, workflows
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
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
    started = time.perf_counter()
    response = await call_next(request)
    if request.url.path.startswith(settings.API_V1_PREFIX):
        latency_ms = int((time.perf_counter() - started) * 1000)
        db = SessionLocal()
        try:
            db.add(
                AuditLog(
                    user_id=getattr(request.state, "user_id", None),
                    organization_id=getattr(request.state, "organization_id", None),
                    action=f"{request.method} {request.url.path}",
                    endpoint=request.url.path,
                    latency_ms=latency_ms,
                    metadata_json={"status_code": response.status_code},
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
app.include_router(organizations.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(rag.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(workflows.router, prefix=settings.API_V1_PREFIX)
app.include_router(observability.router, prefix=settings.API_V1_PREFIX)
