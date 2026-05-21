import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership, require_roles
from app.core.config import get_settings
from app.core.database import get_db
from app.models.document import Document
from app.models.organization import Role
from app.models.user import User
from app.schemas.documents import DocumentResponse
from app.services.document_service import create_queued_document
from app.workers.tasks import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    organization_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    require_roles(db, current_user.id, organization_id, [Role.OWNER, Role.ADMIN])
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported")

    file_bytes = await file.read()
    settings = get_settings()
    upload_dir = Path(settings.STORAGE_DIR) / "uploads" / str(organization_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "uploaded.pdf").name
    stored_path = upload_dir / f"{uuid.uuid4()}-{safe_name}"
    stored_path.write_bytes(file_bytes)

    document = create_queued_document(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
        filename=safe_name,
        content_type=file.content_type or "application/pdf",
        file_path=str(stored_path),
    )
    ingest_document_task.delay(str(document.id))
    return document


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
