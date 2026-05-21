import uuid

from app.services.rag.retrieval import RetrievalResult, retrieve


class RetrievalAgent:
    def retrieve(self, *, organization_id: uuid.UUID, query: str, top_k: int = 5) -> list[RetrievalResult]:
        results, _ = retrieve(organization_id=organization_id, query=query, top_k=top_k)
        return results
