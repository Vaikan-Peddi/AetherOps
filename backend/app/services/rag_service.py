import time
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.audit_log import AIUsageLog
from app.services.ai_gateway import AITaskType, ai_gateway
from app.services.rag.citation_builder import append_citation_instruction, build_context_with_citations
from app.services.rag.reranker import rerank
from app.services.rag.retrieval import retrieve


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
    conversation_context: str | None = None,
    metadata_filter: dict | None = None,
) -> tuple[str, list[RetrievedSource]]:
    started = time.perf_counter()
    retrieved, retrieval_latency_ms = retrieve(
        organization_id=organization_id,
        query=query,
        top_k=max(limit * 2, limit),
        metadata_filter=metadata_filter,
    )
    reranked = rerank(query, retrieved, top_k=limit)
    sources = [
        RetrievedSource(
            document_id=result.document_id,
            filename=result.filename,
            chunk_text=result.chunk_text,
            score=result.score,
        )
        for result in reranked
    ]
    context = build_context_with_citations(reranked)
    memory = f"\n\nRecent conversation:\n{conversation_context}" if conversation_context else ""
    prompt = append_citation_instruction(
        "You are an enterprise AI assistant. Answer using only the supplied context. "
        "If the context is insufficient, say what is missing.\n\n"
        f"Question: {query}{memory}\n\nContext:\n{context}"
    )

    try:
        answer, route, model_latency_ms = await ai_gateway.generate(prompt, task_type=AITaskType.RAG)
    except Exception:
        route = ai_gateway.route(AITaskType.RAG)
        model_latency_ms = 0
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
            model_name=route.model,
            workflow_run_id=workflow_run_id,
            metadata_json={
                "provider": route.provider,
                "task_type": route.task_type.value,
                "retrieval_latency_ms": retrieval_latency_ms,
                "model_latency_ms": model_latency_ms,
            },
        )
    )
    db.commit()
    return answer, sources
