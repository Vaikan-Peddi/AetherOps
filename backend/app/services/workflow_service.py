import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.workflow import Workflow, WorkflowRun, WorkflowRunStatus, WorkflowStep
from app.schemas.workflows import WorkflowCreate


def create_workflow(db: Session, *, payload: WorkflowCreate, user_id: uuid.UUID) -> Workflow:
    workflow = Workflow(
        organization_id=payload.organization_id,
        name=payload.name,
        description=payload.description,
        created_by_id=user_id,
    )
    db.add(workflow)
    db.flush()
    for idx, step in enumerate(payload.steps):
        db.add(
            WorkflowStep(
                workflow_id=workflow.id,
                order_index=idx,
                name=step.name,
                action_type=step.action_type,
                config=step.config,
            )
        )
    db.commit()
    return get_workflow(db, workflow.id)


def list_workflows(db: Session, *, organization_id: uuid.UUID) -> list[Workflow]:
    return list(
        db.scalars(
            select(Workflow)
            .options(selectinload(Workflow.steps))
            .where(Workflow.organization_id == organization_id)
            .order_by(Workflow.created_at.desc())
        )
    )


def get_workflow(db: Session, workflow_id: uuid.UUID) -> Workflow:
    workflow = db.scalar(
        select(Workflow).options(selectinload(Workflow.steps)).where(Workflow.id == workflow_id)
    )
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


def create_workflow_run(
    db: Session,
    *,
    workflow: Workflow,
    user_id: uuid.UUID,
    inputs: dict,
) -> WorkflowRun:
    run = WorkflowRun(
        workflow_id=workflow.id,
        organization_id=workflow.organization_id,
        triggered_by_id=user_id,
        status=WorkflowRunStatus.QUEUED,
        inputs=inputs,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_workflow_run(db: Session, run_id: uuid.UUID) -> WorkflowRun:
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return run
