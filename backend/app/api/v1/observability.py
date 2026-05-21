import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.audit_log import AIUsageLog
from app.models.document import Document
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.schemas.observability import ObservabilitySummary
from app.services.observability.metrics import metrics

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/summary", response_model=ObservabilitySummary)
def summary(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ObservabilitySummary:
    get_membership(db, current_user.id, organization_id)
    total_documents = db.scalar(select(func.count()).select_from(Document).where(Document.organization_id == organization_id)) or 0
    total_queries = db.scalar(select(func.count()).select_from(AIUsageLog).where(AIUsageLog.organization_id == organization_id)) or 0
    total_workflows = db.scalar(select(func.count()).select_from(Workflow).where(Workflow.organization_id == organization_id)) or 0
    total_workflow_runs = db.scalar(select(func.count()).select_from(WorkflowRun).where(WorkflowRun.organization_id == organization_id)) or 0
    avg_latency = db.scalar(select(func.avg(AIUsageLog.latency_ms)).where(AIUsageLog.organization_id == organization_id)) or 0
    total_tokens = db.scalar(select(func.sum(AIUsageLog.token_count)).where(AIUsageLog.organization_id == organization_id)) or 0
    usage_logs = list(db.scalars(select(AIUsageLog).where(AIUsageLog.organization_id == organization_id)))
    provider_usage: dict[str, int] = {}
    model_distribution: dict[str, int] = {}
    for log in usage_logs:
        provider = log.metadata_json.get("provider", "unknown")
        provider_usage[provider] = provider_usage.get(provider, 0) + 1
        model = log.model_name or "unknown"
        model_distribution[model] = model_distribution.get(model, 0) + 1
    workflow_status_rows = db.execute(
        select(WorkflowRun.status, func.count()).where(WorkflowRun.organization_id == organization_id).group_by(WorkflowRun.status)
    ).all()
    workflow_status = {status.value: count for status, count in workflow_status_rows}
    return ObservabilitySummary(
        total_documents=total_documents,
        total_queries=total_queries,
        total_workflows=total_workflows,
        total_workflow_runs=total_workflow_runs,
        avg_latency_ms=round(float(avg_latency or 0), 2),
        total_tokens=int(total_tokens or 0),
        provider_usage=provider_usage,
        model_distribution=model_distribution,
        workflow_status=workflow_status,
    )


@router.get("/metrics")
def prometheus_metrics() -> Response:
    return Response(content=metrics.prometheus(), media_type="text/plain")
