import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.organization import Organization, OrganizationMembership, Role
from app.models.user import User
from app.schemas.organizations import MembershipCreate, MembershipResponse, OrganizationCreate, OrganizationResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse)
def create_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Organization:
    organization = Organization(name=payload.name)
    db.add(organization)
    db.flush()
    db.add(OrganizationMembership(organization_id=organization.id, user_id=current_user.id, role=Role.OWNER))
    db.commit()
    db.refresh(organization)
    return organization


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Organization]:
    return list(
        db.scalars(
            select(Organization)
            .join(OrganizationMembership)
            .where(OrganizationMembership.user_id == current_user.id)
            .order_by(Organization.created_at.asc())
        )
    )


@router.get("/{organization_id}/members", response_model=list[MembershipResponse])
def list_members(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MembershipResponse]:
    require_roles(db, current_user.id, organization_id, [Role.OWNER])
    rows = db.execute(
        select(OrganizationMembership, User.email)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(OrganizationMembership.organization_id == organization_id)
    ).all()
    return [
        MembershipResponse(
            id=membership.id,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            role=membership.role,
            email=email,
        )
        for membership, email in rows
    ]


@router.post("/{organization_id}/members", response_model=MembershipResponse)
def add_member(
    organization_id: uuid.UUID,
    payload: MembershipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MembershipResponse:
    require_roles(db, current_user.id, organization_id, [Role.OWNER])
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if existing:
        existing.role = payload.role
        membership = existing
    else:
        membership = OrganizationMembership(organization_id=organization_id, user_id=user.id, role=payload.role)
        db.add(membership)
    db.commit()
    db.refresh(membership)
    return MembershipResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        role=membership.role,
        email=user.email,
    )
