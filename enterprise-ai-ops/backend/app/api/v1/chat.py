from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.audit_log import AIUsageLog
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_provider import get_llm_provider

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    get_membership(db, current_user.id, payload.organization_id)
    provider = get_llm_provider()
    response = await provider.generate(payload.message)
    db.add(
        AIUsageLog(
            user_id=current_user.id,
            organization_id=payload.organization_id,
            action="chat.generate",
            endpoint="/api/v1/chat",
            token_count=len(payload.message.split()) + len(response.split()),
            model_name=provider.model_name,
        )
    )
    db.commit()
    return ChatResponse(response=response, provider=provider.provider_name, model=provider.model_name)
