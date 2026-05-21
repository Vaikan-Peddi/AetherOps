import asyncio
from datetime import datetime, timezone

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.services.document_service import ingest_pdf_document
from app.models.workflow import Workflow, WorkflowActionType, WorkflowRun, WorkflowRunStatus
from app.services.llm_provider import get_llm_provider
from app.services.rag_service import query_rag
from app.workers.celery_app import celery_app


async def _run_step(db, run: WorkflowRun, step, previous_output):
    if step.action_type == WorkflowActionType.RAG_QUERY:
        query = step.config.get("query") or run.inputs.get("query") or previous_output or ""
        answer, sources = await query_rag(
            db,
            organization_id=run.organization_id,
            user_id=run.triggered_by_id,
            query=query,
            workflow_run_id=run.id,
        )
        return {
            "answer": answer,
            "sources": [
                {
                    "document_id": str(source.document_id),
                    "filename": source.filename,
                    "chunk_text": source.chunk_text,
                    "score": source.score,
                }
                for source in sources
            ],
        }

    if step.action_type == WorkflowActionType.SUMMARIZE_TEXT:
        text = step.config.get("text") or run.inputs.get("text") or previous_output or ""
        provider = get_llm_provider()
        try:
            summary = await provider.generate(f"Summarize this text for an enterprise operator:\n\n{text}")
        except Exception:
            summary = (
                "Ollama is not reachable yet. Summary fallback: "
                + str(text).replace("\n", " ")[:900]
            )
        return {"summary": summary, "provider": provider.provider_name, "model": provider.model_name}

    if step.action_type == WorkflowActionType.SEND_WEBHOOK_PLACEHOLDER:
        return {
            "webhook_placeholder": True,
            "target_url": step.config.get("url", "not-configured"),
            "payload_preview": previous_output,
        }

    raise ValueError(f"Unsupported workflow action: {step.action_type}")


@celery_app.task(name="app.workers.tasks.execute_workflow_run")
def execute_workflow_run(run_id: str) -> None:
    db = SessionLocal()
    try:
        parsed_run_id = uuid.UUID(run_id)
        run = db.scalar(
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.workflow).selectinload(Workflow.steps))
            .where(WorkflowRun.id == parsed_run_id)
        )
        if run is None:
            return

        run.status = WorkflowRunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        step_outputs = []
        previous_output = None
        for step in run.workflow.steps:
            output = asyncio.run(_run_step(db, run, step, previous_output))
            step_outputs.append(
                {
                    "step_id": str(step.id),
                    "name": step.name,
                    "action_type": step.action_type.value,
                    "output": output,
                }
            )
            previous_output = output.get("answer") or output.get("summary") or output

        run.outputs = {"steps": step_outputs}
        run.status = WorkflowRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        run = db.get(WorkflowRun, uuid.UUID(run_id))
        if run is not None:
            run.status = WorkflowRunStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.ingest_document_task")
def ingest_document_task(document_id: str) -> None:
    db = SessionLocal()
    try:
        ingest_pdf_document(db, document_id=uuid.UUID(document_id))
    finally:
        db.close()
