import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.conversation import MessageRole


class ConversationCreate(BaseModel):
    organization_id: uuid.UUID
    title: str = Field(default="New conversation", max_length=255)


class ConversationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    provider: str | None = None
    model: str | None = None
    token_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
