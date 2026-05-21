import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    organization_id: uuid.UUID
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    contexts: list[str] = Field(default_factory=list)


class EvaluationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    question: str
    answer: str
    metrics: dict
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
