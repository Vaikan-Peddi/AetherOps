from app.services.rag.retrieval import RetrievalResult


def _token_overlap(query: str, text: str) -> float:
    query_tokens = {token.lower() for token in query.split() if len(token) > 3}
    text_tokens = {token.lower() for token in text.split() if len(token) > 3}
    return len(query_tokens & text_tokens) / max(len(query_tokens), 1)


def rerank(query: str, results: list[RetrievalResult], *, top_k: int) -> list[RetrievalResult]:
    scored = [
        (
            result.score + (_token_overlap(query, result.chunk_text) * 0.25),
            result,
        )
        for result in results
    ]
    return [result for _, result in sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]]
