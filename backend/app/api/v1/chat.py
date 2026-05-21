import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.audit_log import AIUsageLog
from app.models.conversation import MessageRole
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_gateway import AITaskType, ai_gateway
from app.services.conversation_memory import conversation_memory
from app.services.observability.metrics import metrics

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    get_membership(db, current_user.id, payload.organization_id)
    conversation = conversation_memory.get_or_create(
        db,
        organization_id=payload.organization_id,
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        title=payload.message[:80],
    )
    conversation_memory.add_message(
        db,
        conversation_id=conversation.id,
        organization_id=payload.organization_id,
        role=MessageRole.USER,
        content=payload.message,
    )
    context = conversation_memory.build_context(db, conversation_id=conversation.id, organization_id=payload.organization_id)
    prompt = f"Recent conversation:\n{context}\n\nUser: {payload.message}\nAssistant:"
    response, route, latency_ms = await ai_gateway.generate(
        prompt,
        task_type=AITaskType(payload.task_type),
        provider_name=payload.provider,
        model=payload.model,
    )
    conversation_memory.add_message(
        db,
        conversation_id=conversation.id,
        organization_id=payload.organization_id,
        role=MessageRole.ASSISTANT,
        content=response,
        provider=route.provider,
        model=route.model,
    )
    db.add(
        AIUsageLog(
            user_id=current_user.id,
            organization_id=payload.organization_id,
            action="chat.generate",
            endpoint="/api/v1/chat",
            latency_ms=latency_ms,
            token_count=len(payload.message.split()) + len(response.split()),
            model_name=route.model,
            metadata_json={"provider": route.provider, "task_type": route.task_type.value},
        )
    )
    db.commit()
    return ChatResponse(response=response, provider=route.provider, model=route.model, conversation_id=conversation.id)


@router.post("/stream")
async def stream_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership(db, current_user.id, payload.organization_id)
    conversation = conversation_memory.get_or_create(
        db,
        organization_id=payload.organization_id,
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        title=payload.message[:80],
    )
    conversation_memory.add_message(
        db,
        conversation_id=conversation.id,
        organization_id=payload.organization_id,
        role=MessageRole.USER,
        content=payload.message,
    )
    context = conversation_memory.build_context(db, conversation_id=conversation.id, organization_id=payload.organization_id)
    prompt = f"Recent conversation:\n{context}\n\nUser: {payload.message}\nAssistant:"
    route, stream = await ai_gateway.stream(
        prompt,
        task_type=AITaskType(payload.task_type),
        provider_name=payload.provider,
        model=payload.model,
    )

    async def event_generator():
        started = time.perf_counter()
        chunks: list[str] = []
        yield f"data: {json.dumps({'type': 'meta', 'provider': route.provider, 'model': route.model, 'conversation_id': str(conversation.id)})}\n\n"
        try:
            async for chunk in stream:
                chunks.append(chunk)
                yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"
            response = "".join(chunks)
            conversation_memory.add_message(
                db,
                conversation_id=conversation.id,
                organization_id=payload.organization_id,
                role=MessageRole.ASSISTANT,
                content=response,
                provider=route.provider,
                model=route.model,
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            metrics.observe_latency("aetherops_streaming_duration", latency_ms, {"provider": route.provider, "model": route.model})
            db.add(
                AIUsageLog(
                    user_id=current_user.id,
                    organization_id=payload.organization_id,
                    action="chat.stream",
                    endpoint="/api/v1/chat/stream",
                    latency_ms=latency_ms,
                    token_count=len(payload.message.split()) + len(response.split()),
                    model_name=route.model,
                    metadata_json={"provider": route.provider, "task_type": route.task_type.value},
                )
            )
            db.commit()
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
