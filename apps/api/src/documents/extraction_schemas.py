from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.documents.extraction import (
    DocumentExtractionMethod,
    DocumentExtractionStatus,
    ExtractionValueMode,
)
from src.extraction_templates.schemas import ScalarValueType

ScalarExtractionValue = str | float | bool | None


class ExtractionEvidenceRead(BaseModel):
    source_chunk_indices: list[int] = Field(default_factory=list)
    source_excerpt: str | None = None


class ScalarExtractionFieldRead(BaseModel):
    kind: Literal["scalar"] = "scalar"
    key: Annotated[str, Field(min_length=1, max_length=100)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    value_type: ScalarValueType
    required: bool = False
    value: ScalarExtractionValue = None
    raw_value: str | None = None
    confidence: Annotated[float, Field(ge=0, le=1)] = 0
    extraction_mode: ExtractionValueMode = ExtractionValueMode.NOT_FOUND
    evidence: ExtractionEvidenceRead | None = None


class TableExtractionCellRead(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    value_type: ScalarValueType
    required: bool = False
    value: ScalarExtractionValue = None
    raw_value: str | None = None
    confidence: Annotated[float, Field(ge=0, le=1)] = 0
    extraction_mode: ExtractionValueMode = ExtractionValueMode.NOT_FOUND
    evidence: ExtractionEvidenceRead | None = None


class TableExtractionRowRead(BaseModel):
    row_index: Annotated[int, Field(ge=0)]
    confidence: Annotated[float, Field(ge=0, le=1)] = 0
    cells: list[TableExtractionCellRead] = Field(default_factory=list)


class TableExtractionFieldRead(BaseModel):
    kind: Literal["table"] = "table"
    key: Annotated[str, Field(min_length=1, max_length=100)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    required: bool = False
    min_rows: Annotated[int, Field(ge=0)] = 0
    rows: list[TableExtractionRowRead] = Field(default_factory=list)


DocumentExtractionFieldRead = Annotated[
    ScalarExtractionFieldRead | TableExtractionFieldRead,
    Field(discriminator="kind"),
]


class ExtractionModuleResultRead(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    fields: list[DocumentExtractionFieldRead] = Field(default_factory=list)


class DocumentExtractionResultRead(BaseModel):
    modules: list[ExtractionModuleResultRead] = Field(default_factory=list)


class ExtractionTemplateSummaryRead(BaseModel):
    id: UUID
    name: Annotated[str, Field(min_length=1, max_length=200)]
    locale: Annotated[str, Field(min_length=1, max_length=8)]


class DocumentExtractionCorrectionMessageRead(BaseModel):
    role: Literal["user", "assistant"]
    content: Annotated[str, Field(min_length=1, max_length=4000)]
    created_at: datetime


class DocumentExtractionCorrectionEventItemRead(BaseModel):
    id: Annotated[str, Field(min_length=1, max_length=120)]
    kind: Literal["progress", "error", "end", "change"]
    summary: Annotated[str, Field(min_length=1, max_length=200)]
    occurred_at: Annotated[float | None, Field(default=None, ge=0)]


class DocumentExtractionCorrectionEventGroupRead(BaseModel):
    id: Annotated[str, Field(min_length=1, max_length=120)]
    user_turn_index: Annotated[int, Field(ge=0)]
    summary: Annotated[str, Field(min_length=1, max_length=200)]
    status: Literal["running", "complete", "error"]
    expanded: bool = False
    items: list[DocumentExtractionCorrectionEventItemRead] = Field(default_factory=list)


class DocumentExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    status: DocumentExtractionStatus
    method: DocumentExtractionMethod | None = None
    template: ExtractionTemplateSummaryRead
    thread_id: str | None = None
    overall_confidence: Annotated[float | None, Field(default=None, ge=0, le=1)]
    reasoning_summary: str | None = None
    error: str | None = None
    correction_messages: list[DocumentExtractionCorrectionMessageRead] = Field(default_factory=list)
    correction_event_groups: list[DocumentExtractionCorrectionEventGroupRead] = Field(
        default_factory=list
    )
    result: DocumentExtractionResultRead | None = None
    extracted_at: datetime | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DocumentExtractionSessionCreate(BaseModel):
    template_id: UUID


class DocumentExtractionSessionRead(BaseModel):
    assistant_id: str
    thread_id: str
    document_id: UUID
    template_id: UUID
    status: DocumentExtractionStatus


class DocumentExtractionCorrectionSessionRead(BaseModel):
    assistant_id: str
    thread_id: str
    document_id: UUID
    status: DocumentExtractionStatus


class DocumentExtractionCorrectionActivityUpdate(BaseModel):
    groups: list[DocumentExtractionCorrectionEventGroupRead] = Field(default_factory=list)


class DocumentExtractionReviewUpdate(BaseModel):
    result: DocumentExtractionResultRead
