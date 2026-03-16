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
