import uuid

from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    organization_id: uuid.UUID
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=12)
    conversation_id: uuid.UUID | None = None
    metadata_filter: dict | None = None


class RagSource(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_text: str
    score: float
    citation: str | None = None


class RagQueryResponse(BaseModel):
    answer: str
    sources: list[RagSource]
