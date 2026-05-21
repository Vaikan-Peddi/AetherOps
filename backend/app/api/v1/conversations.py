import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.user import User
from app.schemas.conversations import ConversationCreate, ConversationResponse, MessageResponse
from app.services.conversation_memory import conversation_memory

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership(db, current_user.id, payload.organization_id)
    return conversation_memory.create_conversation(
        db,
        organization_id=payload.organization_id,
        user_id=current_user.id,
        title=payload.title,
    )


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership(db, current_user.id, organization_id)
    return conversation_memory.list_conversations(db, organization_id=organization_id, user_id=current_user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership(db, current_user.id, organization_id)
    return conversation_memory.messages(db, conversation_id=conversation_id, organization_id=organization_id)
