from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.organization import OrganizationMembership
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user, organization, token = register_user(db, payload)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user), organization_id=organization.id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user, token = authenticate_user(db, payload.email, payload.password)
    membership = db.scalar(
        select(OrganizationMembership).where(OrganizationMembership.user_id == user.id).limit(1)
    )
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
        organization_id=membership.organization_id if membership else None,
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
