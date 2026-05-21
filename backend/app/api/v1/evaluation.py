from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_membership
from app.core.database import get_db
from app.models.evaluation import EvaluationRun
from app.models.user import User
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.services.evaluation.evaluator import evaluate_answer

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationResponse)
def run_evaluation(
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_membership(db, current_user.id, payload.organization_id)
    scores = evaluate_answer(payload.question, payload.answer, payload.contexts)
    run = EvaluationRun(
        organization_id=payload.organization_id,
        user_id=current_user.id,
        question=payload.question,
        answer=payload.answer,
        status="COMPLETED",
        metrics=scores.as_dict(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
