from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.ai_gateway import AITaskType, ai_gateway
from app.services.llm.registry import provider_registry

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/routes")
def routes(current_user: User = Depends(get_current_user)) -> dict:
    return {
        task.value: {
            "provider": ai_gateway.route(task).provider,
            "model": ai_gateway.route(task).model,
        }
        for task in AITaskType
    }


@router.get("/providers/health")
async def provider_health(current_user: User = Depends(get_current_user)) -> dict:
    results = []
    for provider_name in provider_registry.all_provider_names():
        provider = provider_registry.get(provider_name)
        health = await provider.health_check()
        results.append(health.__dict__)
    return {"providers": results, "enabled": provider_registry.enabled_provider_names()}
