import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    organization_id: uuid.UUID
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
