from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class TextChunk:
    text: str
    page_number: int
    chunk_index: int


def semanticish_chunks(page_text: str, *, page_number: int, starting_index: int = 0) -> list[TextChunk]:
    settings = get_settings()
    paragraphs = [paragraph.strip() for paragraph in page_text.split("\n\n") if paragraph.strip()]
    chunks: list[TextChunk] = []
    buffer = ""

    def flush() -> None:
        nonlocal buffer
        if buffer.strip():
            chunks.append(
                TextChunk(text=" ".join(buffer.split()), page_number=page_number, chunk_index=starting_index + len(chunks))
            )
        buffer = ""

    for paragraph in paragraphs or [page_text]:
        normalized = " ".join(paragraph.split())
        if not normalized:
            continue
        if len(buffer) + len(normalized) > settings.DOCUMENT_CHUNK_SIZE:
            flush()
            if chunks and settings.DOCUMENT_CHUNK_OVERLAP:
                buffer = chunks[-1].text[-settings.DOCUMENT_CHUNK_OVERLAP :] + " "
        buffer += normalized + "\n"
    flush()
    return chunks
