import uuid
from dataclasses import dataclass
from pathlib import Path

import fitz
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.embedding_service import embed_texts
from app.services.qdrant_service import qdrant_service
from app.services.rag.chunking import semanticish_chunks


@dataclass
class ExtractedChunk:
    text: str
    page_number: int
    chunk_index: int


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def extract_pdf_chunks(file_bytes: bytes) -> tuple[list[ExtractedChunk], int]:
    settings = get_settings()
    chunks: list[ExtractedChunk] = []
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page_idx, page in enumerate(pdf, start=1):
            page_text = page.get_text("text")
            for chunk in semanticish_chunks(page_text, page_number=page_idx, starting_index=len(chunks)):
                chunks.append(ExtractedChunk(text=chunk.text, page_number=chunk.page_number, chunk_index=len(chunks)))
        return chunks, pdf.page_count


def create_queued_document(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    file_path: str,
) -> Document:
    document = Document(
        organization_id=organization_id,
        uploaded_by_id=user_id,
        filename=filename,
        content_type=content_type,
        file_path=file_path,
        status=DocumentStatus.PROCESSING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def ingest_pdf_document(db: Session, *, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise ValueError("Document not found")
    if not document.file_path:
        raise ValueError("Document has no stored file path")

    document.status = DocumentStatus.PROCESSING
    document.error_message = None
    document.progress_percent = 5
    document.current_step = "Reading uploaded PDF"
    db.add(document)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
    db.flush()

    try:
        file_bytes = Path(document.file_path).read_bytes()
        extracted_chunks, page_count = extract_pdf_chunks(file_bytes)
        if not extracted_chunks:
            raise ValueError("No extractable text found in PDF")
        document.progress_percent = 30
        document.current_step = "Generating embeddings"
        db.commit()

        chunk_payloads = [
            {
                "organization_id": str(organization_id),
                "document_id": str(document.id),
                "filename": document.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk.text,
            }
            for chunk in extracted_chunks
        ]
        embeddings = embed_texts([chunk.text for chunk in extracted_chunks])
        document.progress_percent = 70
        document.current_step = "Writing vectors to Qdrant"
        db.commit()
        vector_ids = qdrant_service.upsert_chunks(chunk_payloads, embeddings)

        for chunk, vector_id in zip(extracted_chunks, vector_ids, strict=True):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    organization_id=organization_id,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    text=chunk.text,
                    vector_id=vector_id,
                )
            )

        document.status = DocumentStatus.READY
        document.progress_percent = 100
        document.current_step = "Ready"
        document.page_count = page_count
        document.chunk_count = len(extracted_chunks)
        db.commit()
        db.refresh(document)
        return document
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.progress_percent = 100
        document.current_step = "Failed"
        document.error_message = str(exc)
        db.commit()
        db.refresh(document)
        raise
