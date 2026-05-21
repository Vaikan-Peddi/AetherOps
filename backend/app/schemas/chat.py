import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    organization_id: uuid.UUID
    message: str = Field(min_length=1)
    conversation_id: uuid.UUID | None = None
    provider: str | None = None
    model: str | None = None
    task_type: str = "CHAT"


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    conversation_id: uuid.UUID | None = None
