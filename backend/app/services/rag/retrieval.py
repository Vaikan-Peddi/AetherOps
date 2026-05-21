import time
import uuid
from dataclasses import dataclass

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
) -> tuple[list[RetrievalResult], int]:
    started = time.perf_counter()
    cache_key = cache.key("retrieval", {"org": str(organization_id), "query": query, "top_k": top_k, "filter": metadata_filter})
    cached = cache.get_json(cache_key)
    if cached:
        return ([RetrievalResult(document_id=uuid.UUID(item["document_id"]), **{k: v for k, v in item.items() if k != "document_id"}) for item in cached], 0)

    query_vector = embed_query(query)
    points = qdrant_service.search(organization_id, query_vector, limit=top_k)
    results: list[RetrievalResult] = []
    for point in points:
        payload = point.payload or {}
        if metadata_filter:
            if any(str(payload.get(key)) != str(value) for key, value in metadata_filter.items() if value is not None):
                continue
        results.append(
            RetrievalResult(
                document_id=uuid.UUID(payload["document_id"]),
                filename=payload.get("filename", "unknown"),
                chunk_text=payload.get("chunk_text", ""),
                score=float(point.score or 0),
                page_number=payload.get("page_number"),
                chunk_index=payload.get("chunk_index"),
            )
        )
    cache.set_json(cache_key, [result.__dict__ | {"document_id": str(result.document_id)} for result in results], ttl_seconds=120)
    return results, int((time.perf_counter() - started) * 1000)
