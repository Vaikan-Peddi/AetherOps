from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.models.workflow import WorkflowRun
from app.schemas.tasks import TaskStatusResponse
from app.workers.celery_app import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatusResponse:
    if not task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task id is required")

    organization_id = db.scalar(select(Document.organization_id).where(Document.celery_task_id == task_id))
    if organization_id is None:
        organization_id = db.scalar(select(WorkflowRun.organization_id).where(WorkflowRun.celery_task_id == task_id))
    if organization_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    get_membership(db, current_user.id, organization_id)

    result = AsyncResult(task_id, app=celery_app)
    task_result = result.result
    if isinstance(task_result, Exception):
        task_result = str(task_result)
    return TaskStatusResponse(
        task_id=task_id,
        state=result.state,
        ready=result.ready(),
        successful=result.successful(),
        failed=result.failed(),
        result=task_result if isinstance(task_result, (str, dict, list)) else None,
    )
