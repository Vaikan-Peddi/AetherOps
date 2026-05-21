import time
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.audit_log import AIUsageLog
from app.services.embedding_service import embed_query
from app.services.llm_provider import get_llm_provider
from app.services.qdrant_service import qdrant_service


@dataclass
class RetrievedSource:
    document_id: uuid.UUID
    filename: str
    chunk_text: str
    score: float


def _source_from_point(point) -> RetrievedSource:
    payload = point.payload or {}
    return RetrievedSource(
        document_id=uuid.UUID(payload["document_id"]),
        filename=payload.get("filename", "unknown"),
        chunk_text=payload.get("chunk_text", ""),
        score=float(point.score or 0),
    )


async def query_rag(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID | None,
    query: str,
    limit: int = 5,
    workflow_run_id: uuid.UUID | None = None,
) -> tuple[str, list[RetrievedSource]]:
    started = time.perf_counter()
    query_vector = embed_query(query)
    points = qdrant_service.search(organization_id, query_vector, limit=limit)
    sources = [_source_from_point(point) for point in points]
    context = "\n\n".join(f"Source {idx + 1}: {source.chunk_text}" for idx, source in enumerate(sources))
    provider = get_llm_provider()
    prompt = (
        "You are an enterprise AI assistant. Answer using only the supplied context. "
        "If the context is insufficient, say what is missing.\n\n"
        f"Question: {query}\n\nContext:\n{context}"
    )

    try:
        answer = await provider.generate(prompt)
    except Exception:
        if sources:
            answer = (
                "Ollama is not reachable yet, but these are the most relevant retrieved passages: "
                + " ".join(source.chunk_text[:280] for source in sources[:2])
            )
        else:
            answer = "No relevant document chunks were found for this organization."

    latency_ms = int((time.perf_counter() - started) * 1000)
    db.add(
        AIUsageLog(
            user_id=user_id,
            organization_id=organization_id,
            action="rag.query",
            endpoint="/api/v1/rag/query",
            latency_ms=latency_ms,
            token_count=len(query.split()) + sum(len(source.chunk_text.split()) for source in sources),
            model_name=getattr(provider, "model_name", None),
            workflow_run_id=workflow_run_id,
        )
    )
    db.commit()
    return answer, sources
