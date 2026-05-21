import asyncio
import time
from datetime import datetime, timezone

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.services.document_service import ingest_pdf_document
from app.models.workflow import Workflow, WorkflowActionType, WorkflowRun, WorkflowRunStatus
from app.services.ai_gateway import AITaskType, ai_gateway
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

    if step.action_type in {WorkflowActionType.CHAT}:
        message = step.config.get("message") or run.inputs.get("message") or previous_output or ""
        response, route, latency_ms = await ai_gateway.generate(str(message), task_type=AITaskType.CHAT)
        return {"response": response, "provider": route.provider, "model": route.model, "latency_ms": latency_ms}

    if step.action_type in {WorkflowActionType.SUMMARIZE_TEXT, WorkflowActionType.SUMMARIZE}:
        text = step.config.get("text") or run.inputs.get("text") or previous_output or ""
        try:
            summary, route, latency_ms = await ai_gateway.generate(
                f"Summarize this text for an enterprise operator:\n\n{text}",
                task_type=AITaskType.SUMMARIZATION,
            )
        except Exception:
            route = ai_gateway.route(AITaskType.SUMMARIZATION)
            latency_ms = 0
            summary = (
                "Ollama is not reachable yet. Summary fallback: "
                + str(text).replace("\n", " ")[:900]
            )
        return {"summary": summary, "provider": route.provider, "model": route.model, "latency_ms": latency_ms}

    if step.action_type in {WorkflowActionType.SEND_WEBHOOK_PLACEHOLDER, WorkflowActionType.WEBHOOK}:
        return {
            "webhook_placeholder": True,
            "target_url": step.config.get("url", "not-configured"),
            "payload_preview": previous_output,
        }

    if step.action_type == WorkflowActionType.CONDITION:
        expected = step.config.get("contains")
        matched = bool(expected and expected.lower() in str(previous_output).lower())
        return {"condition_matched": matched, "expected": expected}

    if step.action_type == WorkflowActionType.DELAY:
        seconds = min(float(step.config.get("seconds", 0) or 0), 60.0)
        if seconds > 0:
            time.sleep(seconds)
        return {"delayed": True, "seconds": seconds}

    if step.action_type == WorkflowActionType.HUMAN_APPROVAL:
        return {"human_approval_placeholder": True, "status": "waiting_not_implemented"}

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
        run.progress_percent = 1
        run.current_step = "Starting"
        db.commit()

        step_outputs = []
        previous_output = None
        total_steps = max(len(run.workflow.steps), 1)
        skip_next = False
        for index, step in enumerate(run.workflow.steps, start=1):
            if skip_next:
                step_outputs.append(
                    {
                        "step_id": str(step.id),
                        "name": step.name,
                        "action_type": step.action_type.value,
                        "output": {"skipped": True, "reason": "Previous condition was not met"},
                    }
                )
                skip_next = False
                continue
            run.current_step = step.name
            run.progress_percent = int(((index - 1) / total_steps) * 100)
            db.commit()
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
            if step.action_type == WorkflowActionType.CONDITION:
                skip_next = bool(step.config.get("skip_next_on_false", True)) and not output.get("condition_matched", False)

        run.outputs = {"steps": step_outputs}
        run.status = WorkflowRunStatus.COMPLETED
        run.progress_percent = 100
        run.current_step = "Completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        run = db.get(WorkflowRun, uuid.UUID(run_id))
        if run is not None:
            run.status = WorkflowRunStatus.FAILED
            run.error_message = str(exc)
            run.progress_percent = 100
            run.current_step = "Failed"
            run.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@celery_app.task(
    name="app.workers.tasks.ingest_document_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 10},
)
def ingest_document_task(document_id: str) -> None:
    db = SessionLocal()
    try:
        ingest_pdf_document(db, document_id=uuid.UUID(document_id))
    finally:
        db.close()
