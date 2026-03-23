from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field

from src.documents.extraction_schemas import DocumentExtractionResultRead


class ExtractionDraftCell(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    value: Any = None
    raw_value: str | None = None
    confidence: Any = None
    extraction_mode: str | None = None
    evidence: Any = None


class ExtractionDraftRow(BaseModel):
    row_index: Any = None
    confidence: Any = None
    cells: list[ExtractionDraftCell] = Field(default_factory=list)


class ExtractionDraftField(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    kind: str | None = None
    value: Any = None
    raw_value: str | None = None
    confidence: Any = None
    extraction_mode: str | None = None
    evidence: Any = None
    rows: list[ExtractionDraftRow] = Field(default_factory=list)


class ExtractionDraftModule(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=100)]
    fields: list[ExtractionDraftField] = Field(default_factory=list)


class ExtractionResultDraft(BaseModel):
    modules: list[ExtractionDraftModule] = Field(default_factory=list)


class ExtractionFinalizerDraft(BaseModel):
    reasoning_summary: Annotated[str, Field(min_length=1)]
    result: ExtractionResultDraft = Field(default_factory=ExtractionResultDraft)


class ExtractionFinalizerDecision(BaseModel):
    reasoning_summary: Annotated[str, Field(min_length=1, max_length=1200)]
    result: DocumentExtractionResultRead
