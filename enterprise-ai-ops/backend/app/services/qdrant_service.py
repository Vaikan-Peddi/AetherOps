import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import get_settings


class QdrantService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.QDRANT_URL)

    def ensure_collection(self) -> None:
        try:
            self.client.get_collection(self.settings.QDRANT_COLLECTION)
        except Exception:
            self.client.create_collection(
                collection_name=self.settings.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=self.settings.EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE,
                ),
            )

    def upsert_chunks(self, chunks: list[dict[str, Any]], vectors: list[list[float]]) -> list[str]:
        self.ensure_collection()
        vector_ids = [str(uuid.uuid4()) for _ in chunks]
        points = [
            models.PointStruct(id=vector_id, vector=vector, payload=chunk)
            for vector_id, vector, chunk in zip(vector_ids, vectors, chunks, strict=True)
        ]
        if points:
            self.client.upsert(collection_name=self.settings.QDRANT_COLLECTION, points=points)
        return vector_ids

    def search(self, organization_id: uuid.UUID, query_vector: list[float], limit: int = 5) -> list[Any]:
        self.ensure_collection()
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="organization_id",
                    match=models.MatchValue(value=str(organization_id)),
                )
            ]
        )
        try:
            return self.client.search(
                collection_name=self.settings.QDRANT_COLLECTION,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
            )
        except AttributeError:
            response = self.client.query_points(
                collection_name=self.settings.QDRANT_COLLECTION,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
            )
            return response.points


qdrant_service = QdrantService()
