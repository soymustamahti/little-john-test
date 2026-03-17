from datetime import datetime
from enum import Enum
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.documents.classification import (
    DocumentClassificationMethod,
    DocumentClassificationStatus,
    parse_classification_metadata,
)


class DocumentKind(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    SPREADSHEET = "spreadsheet"
    DOCX = "docx"


class DocumentCreateRecord(BaseModel):
    id: UUID
    original_filename: Annotated[str, Field(min_length=1, max_length=255)]
    content_type: Annotated[str, Field(min_length=1, max_length=255)]
    file_extension: Annotated[str, Field(min_length=1, max_length=16)]
    file_kind: DocumentKind
    size_bytes: Annotated[int, Field(gt=0)]
    sha256: Annotated[str, Field(min_length=64, max_length=64)]
    storage_provider: Annotated[str, Field(min_length=1, max_length=64)]
    storage_bucket: Annotated[str, Field(min_length=1, max_length=120)]
    storage_key: Annotated[str, Field(min_length=1, max_length=512)]
    public_url: str | None = None
    content_source: Annotated[str, Field(min_length=1, max_length=64)] | None = None
    extracted_text: str | None = None
    extraction_metadata: dict | None = None
    processed_at: datetime | None = None


class DocumentChunkCreateRecord(BaseModel):
    document_id: UUID
    chunk_index: Annotated[int, Field(ge=0)]
    content: Annotated[str, Field(min_length=1)]
    content_start_offset: Annotated[int, Field(ge=0)]
    content_end_offset: Annotated[int, Field(gt=0)]
    embedding_provider: Annotated[str, Field(min_length=1, max_length=64)]
    embedding_model: Annotated[str, Field(min_length=1, max_length=120)]
    embedding_dimensions: Annotated[int, Field(gt=0)]
    embedding: Annotated[list[float], Field(min_length=1)]


class DocumentCategorySummaryRead(BaseModel):
    id: UUID
    name: Annotated[str, Field(min_length=1, max_length=120)]
    label_key: Annotated[str, Field(min_length=1, max_length=120)]


class SuggestedDocumentCategoryRead(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    label_key: Annotated[str, Field(min_length=1, max_length=120)]


class DocumentClassificationRead(BaseModel):
    status: DocumentClassificationStatus
    method: DocumentClassificationMethod | None = None
    confidence: Annotated[float | None, Field(default=None, ge=0, le=1)]
    rationale: str | None = None
    thread_id: str | None = None
    error: str | None = None
    sampled_chunk_indices: list[int] = Field(default_factory=list)
    excerpt_character_count: Annotated[int | None, Field(default=None, ge=0)]
    suggested_category: SuggestedDocumentCategoryRead | None = None
    category: DocumentCategorySummaryRead | None = None
    classified_at: datetime | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: Annotated[str, Field(min_length=1, max_length=255)]
    content_type: Annotated[str, Field(min_length=1, max_length=255)]
    file_extension: Annotated[str, Field(min_length=1, max_length=16)]
    file_kind: DocumentKind
    size_bytes: Annotated[int, Field(gt=0)]
    sha256: Annotated[str, Field(min_length=64, max_length=64)]
    public_url: str | None = None
    classification: DocumentClassificationRead
    created_at: datetime
    updated_at: datetime


class ManualDocumentClassificationRequest(BaseModel):
    category_id: UUID


class DocumentClassificationSessionRead(BaseModel):
    assistant_id: str
    thread_id: str
    document_id: UUID
    status: DocumentClassificationStatus


def build_document_read(document: Any) -> DocumentRead:
    metadata = parse_classification_metadata(getattr(document, "classification_metadata", None))
    document_category = getattr(document, "document_category", None)

    category_payload = None
    if document_category is not None:
        category_payload = DocumentCategorySummaryRead(
            id=document_category.id,
            name=document_category.name,
            label_key=document_category.label_key,
        )

    suggested_category_payload = None
    if metadata.suggested_category is not None:
        suggested_category_payload = SuggestedDocumentCategoryRead(
            name=metadata.suggested_category.name,
            label_key=metadata.suggested_category.label_key,
        )

    classification_status = getattr(document, "classification_status", None)
    classification_method = getattr(document, "classification_method", None)

    return DocumentRead.model_validate(
        {
            "id": document.id,
            "original_filename": document.original_filename,
            "content_type": document.content_type,
            "file_extension": document.file_extension,
            "file_kind": document.file_kind,
            "size_bytes": document.size_bytes,
            "sha256": document.sha256,
            "public_url": document.public_url,
            "classification": {
                "status": classification_status or DocumentClassificationStatus.UNCLASSIFIED.value,
                "method": classification_method,
                "confidence": metadata.confidence,
                "rationale": metadata.rationale,
                "thread_id": metadata.thread_id,
                "error": metadata.error,
                "sampled_chunk_indices": list(metadata.sampled_chunk_indices),
                "excerpt_character_count": metadata.excerpt_character_count,
                "suggested_category": suggested_category_payload,
                "category": category_payload,
                "classified_at": getattr(document, "classified_at", None),
            },
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
    )
