import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership, require_roles
from app.core.database import get_db
from app.models.document import Document
from app.models.organization import Role
from app.models.user import User
from app.schemas.documents import DocumentResponse
from app.services.document_service import ingest_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    organization_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    require_roles(db, current_user.id, organization_id, [Role.OWNER, Role.ADMIN])
    file_bytes = await file.read()
    return ingest_pdf(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
        upload=file,
        file_bytes=file_bytes,
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    get_membership(db, current_user.id, organization_id)
    return list(
        db.scalars(
            select(Document)
            .where(Document.organization_id == organization_id)
            .order_by(Document.created_at.desc())
        )
    )
