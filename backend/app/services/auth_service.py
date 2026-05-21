from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.organization import Organization, OrganizationMembership, Role
from app.models.user import User
from app.schemas.auth import RegisterRequest


def register_user(db: Session, payload: RegisterRequest) -> tuple[User, Organization, str]:
    existing_user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
    )
    organization = Organization(name=payload.organization_name or f"{payload.email.split('@')[0]}'s Organization")
    db.add_all([user, organization])
    db.flush()

    membership = OrganizationMembership(organization_id=organization.id, user_id=user.id, role=Role.OWNER)
    db.add(membership)
    db.commit()
    db.refresh(user)
    db.refresh(organization)
    return user, organization, create_access_token(str(user.id))


def authenticate_user(db: Session, email: str, password: str) -> tuple[User, str]:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    return user, create_access_token(str(user.id))
