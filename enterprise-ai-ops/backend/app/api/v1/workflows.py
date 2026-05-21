import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership, require_roles
from app.core.database import get_db
from app.models.organization import Role
from app.models.user import User
from app.schemas.workflows import WorkflowCreate, WorkflowResponse, WorkflowRunCreate, WorkflowRunResponse
from app.services.workflow_service import create_workflow, create_workflow_run, get_workflow, get_workflow_run, list_workflows
from app.workers.tasks import execute_workflow_run

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse)
def create(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_roles(db, current_user.id, payload.organization_id, [Role.OWNER, Role.ADMIN, Role.MEMBER])
    return create_workflow(db, payload=payload, user_id=current_user.id)


@router.get("", response_model=list[WorkflowResponse])
def list_for_org(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership(db, current_user.id, organization_id)
    return list_workflows(db, organization_id=organization_id)


@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse)
def run_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow = get_workflow(db, workflow_id)
    require_roles(db, current_user.id, workflow.organization_id, [Role.OWNER, Role.ADMIN, Role.MEMBER])
    run = create_workflow_run(db, workflow=workflow, user_id=current_user.id, inputs=payload.inputs)
    execute_workflow_run.delay(str(run.id))
    return run


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
def get_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = get_workflow_run(db, run_id)
    get_membership(db, current_user.id, run.organization_id)
    return run
