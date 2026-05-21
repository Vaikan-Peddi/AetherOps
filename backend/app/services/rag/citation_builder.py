from app.services.rag.retrieval import RetrievalResult


def build_context_with_citations(results: list[RetrievalResult]) -> str:
    lines = []
    for idx, result in enumerate(results, start=1):
        page = f", page {result.page_number}" if result.page_number else ""
        lines.append(f"[{idx}] {result.filename}{page}: {result.chunk_text}")
    return "\n\n".join(lines)


def append_citation_instruction(prompt: str) -> str:
    return prompt + "\n\nWhen you use a source, cite it inline like [1] or [2]."
