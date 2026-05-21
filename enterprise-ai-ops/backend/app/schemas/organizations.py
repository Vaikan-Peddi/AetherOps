import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.organization import Role


class OrganizationCreate(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: Role
    email: str | None = None

    model_config = {"from_attributes": True}


class MembershipCreate(BaseModel):
    email: str
    role: Role = Role.MEMBER
