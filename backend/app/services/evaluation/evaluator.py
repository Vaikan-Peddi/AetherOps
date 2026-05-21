from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationScores:
    faithfulness: float
    answer_relevance: float
    retrieval_precision: float
    retrieval_recall_placeholder: float
    hallucination_risk_placeholder: float

    def as_dict(self) -> dict[str, float]:
        return self.__dict__.copy()


def _tokens(text: str) -> set[str]:
    return {token.strip(".,;:!?()[]{}\"'").lower() for token in text.split() if len(token) > 3}


def evaluate_answer(question: str, answer: str, contexts: list[str]) -> EvaluationScores:
    question_tokens = _tokens(question)
    answer_tokens = _tokens(answer)
    context_tokens = _tokens(" ".join(contexts))

    relevance = len(question_tokens & answer_tokens) / max(len(question_tokens), 1)
    faithfulness = len(answer_tokens & context_tokens) / max(len(answer_tokens), 1) if contexts else 0.0
    precision = sum(1 for ctx in contexts if _tokens(ctx) & answer_tokens) / max(len(contexts), 1)
    hallucination = max(0.0, 1.0 - faithfulness)
    return EvaluationScores(
        faithfulness=round(faithfulness, 3),
        answer_relevance=round(relevance, 3),
        retrieval_precision=round(precision, 3),
        retrieval_recall_placeholder=0.0,
        hallucination_risk_placeholder=round(hallucination, 3),
    )
