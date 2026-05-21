import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.workflow import WorkflowActionType, WorkflowRunStatus


class WorkflowStepCreate(BaseModel):
    name: str
    action_type: WorkflowActionType
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowCreate(BaseModel):
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    steps: list[WorkflowStepCreate] = Field(default_factory=list)


class WorkflowStepResponse(BaseModel):
    id: uuid.UUID
    order_index: int
    name: str
    action_type: WorkflowActionType
    config: dict[str, Any]

    model_config = {"from_attributes": True}


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    steps: list[WorkflowStepResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowRunCreate(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    organization_id: uuid.UUID
    status: WorkflowRunStatus
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
