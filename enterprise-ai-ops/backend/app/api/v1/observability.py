import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.audit_log import AIUsageLog
from app.models.document import Document
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.schemas.observability import ObservabilitySummary

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
    return ObservabilitySummary(
        total_documents=total_documents,
        total_queries=total_queries,
        total_workflows=total_workflows,
        total_workflow_runs=total_workflow_runs,
    )
