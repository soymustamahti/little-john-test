from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
    created_at: datetime
    updated_at: datetime
