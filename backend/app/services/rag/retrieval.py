import time
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services.cache_service import cache
from app.services.embedding_service import embed_query
from app.services.qdrant_service import qdrant_service


@dataclass(frozen=True)
class RetrievalResult:
    document_id: uuid.UUID
    filename: str
    chunk_text: str
    score: float
    page_number: int | None = None
    chunk_index: int | None = None


def retrieve(
    *,
    organization_id: uuid.UUID,
    query: str,
    top_k: int,
    metadata_filter: dict | None = None,
    db: Session | None = None,
    hybrid: bool = True,
) -> tuple[list[RetrievalResult], int]:
    started = time.perf_counter()
    cache_key = cache.key(
        "retrieval",
        {"org": str(organization_id), "query": query, "top_k": top_k, "filter": metadata_filter, "hybrid": hybrid},
    )
    cached = cache.get_json(cache_key)
    if cached:
        return ([RetrievalResult(document_id=uuid.UUID(item["document_id"]), **{k: v for k, v in item.items() if k != "document_id"}) for item in cached], 0)

    query_vector = embed_query(query)
    points = qdrant_service.search(organization_id, query_vector, limit=top_k)
    results_by_key: dict[tuple[uuid.UUID, int | None], RetrievalResult] = {}
    for point in points:
        payload = point.payload or {}
        if metadata_filter:
            if any(str(payload.get(key)) != str(value) for key, value in metadata_filter.items() if value is not None):
                continue
        result = RetrievalResult(
            document_id=uuid.UUID(payload["document_id"]),
            filename=payload.get("filename", "unknown"),
            chunk_text=payload.get("chunk_text", ""),
            score=float(point.score or 0),
            page_number=payload.get("page_number"),
            chunk_index=payload.get("chunk_index"),
        )
        results_by_key[(result.document_id, result.chunk_index)] = result

    if hybrid and db is not None:
        lexical_terms = [term for term in query.split() if len(term) > 3][:6]
        if lexical_terms:
            conditions = [DocumentChunk.text.ilike(f"%{term}%") for term in lexical_terms]
            rows = db.execute(
                select(DocumentChunk, Document.filename)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(DocumentChunk.organization_id == organization_id)
                .where(*conditions)
                .limit(top_k)
            ).all()
            for chunk, filename in rows:
                lexical_score = 0.15 + (0.02 * sum(1 for term in lexical_terms if term.lower() in chunk.text.lower()))
                key = (chunk.document_id, chunk.chunk_index)
                if key in results_by_key:
                    existing = results_by_key[key]
                    results_by_key[key] = RetrievalResult(
                        document_id=existing.document_id,
                        filename=existing.filename,
                        chunk_text=existing.chunk_text,
                        score=existing.score + lexical_score,
                        page_number=existing.page_number,
                        chunk_index=existing.chunk_index,
                    )
                    continue
                results_by_key[key] = RetrievalResult(
                    document_id=chunk.document_id,
                    filename=filename,
                    chunk_text=chunk.text,
                    score=lexical_score,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                )

    results = sorted(results_by_key.values(), key=lambda result: result.score, reverse=True)[:top_k]
    cache.set_json(
        cache_key,
        [result.__dict__ | {"document_id": str(result.document_id)} for result in results],
        ttl_seconds=120,
    )
    return results, int((time.perf_counter() - started) * 1000)
