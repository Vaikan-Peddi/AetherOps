import uuid
from dataclasses import dataclass

import fitz
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.embedding_service import embed_texts
from app.services.qdrant_service import qdrant_service


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
            for chunk_text in _chunk_text(
                page_text,
                chunk_size=settings.DOCUMENT_CHUNK_SIZE,
                overlap=settings.DOCUMENT_CHUNK_OVERLAP,
            ):
                chunks.append(
                    ExtractedChunk(text=chunk_text, page_number=page_idx, chunk_index=len(chunks))
                )
        return chunks, pdf.page_count


def ingest_pdf(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    upload: UploadFile,
    file_bytes: bytes,
) -> Document:
    if upload.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported")

    document = Document(
        organization_id=organization_id,
        uploaded_by_id=user_id,
        filename=upload.filename or "uploaded.pdf",
        content_type=upload.content_type or "application/pdf",
        status=DocumentStatus.PROCESSING,
    )
    db.add(document)
    db.flush()

    try:
        extracted_chunks, page_count = extract_pdf_chunks(file_bytes)
        if not extracted_chunks:
            raise ValueError("No extractable text found in PDF")

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
        document.page_count = page_count
        document.chunk_count = len(extracted_chunks)
        db.commit()
        db.refresh(document)
        return document
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
        db.commit()
        db.refresh(document)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=document.error_message) from exc
