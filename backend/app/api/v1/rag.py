from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.user import User
from app.schemas.rag import RagQueryRequest, RagQueryResponse, RagSource
from app.services.conversation_memory import conversation_memory
from app.services.rag_service import query_rag

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RagQueryResponse)
async def query(
    payload: RagQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RagQueryResponse:
    get_membership(db, current_user.id, payload.organization_id)
    conversation_context = None
    if payload.conversation_id:
        conversation_context = conversation_memory.build_context(
            db,
            conversation_id=payload.conversation_id,
            organization_id=payload.organization_id,
        )
    answer, sources = await query_rag(
        db,
        organization_id=payload.organization_id,
        user_id=current_user.id,
        query=payload.query,
        limit=payload.limit,
        conversation_context=conversation_context,
        metadata_filter=payload.metadata_filter,
    )
    return RagQueryResponse(
        answer=answer,
        sources=[
            RagSource(
                document_id=source.document_id,
                filename=source.filename,
                chunk_text=source.chunk_text,
                score=source.score,
                citation=source.filename,
            )
            for source in sources
        ],
    )
