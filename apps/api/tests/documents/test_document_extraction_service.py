from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import pytest
from src.documents.classification import DocumentClassificationStatus
from src.documents.extraction import (
    DocumentExtractionMethod,
    DocumentExtractionStatus,
    parse_extraction_metadata,
)
from src.documents.extraction_schemas import (
    DocumentExtractionCorrectionActivityUpdate,
    DocumentExtractionResultRead,
    DocumentExtractionReviewUpdate,
)
from src.documents.extraction_service import DocumentExtractionService
from src.documents.schemas import DocumentKind


@dataclass
class FakeTemplateRecord:
    id: UUID
    name: str
    locale: str
    modules: list[dict[str, object]]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeChunkRecord:
    chunk_index: int
    content: str


@dataclass
class FakeDocumentRecord:
    id: UUID
    original_filename: str
    content_type: str
    file_extension: str
    file_kind: DocumentKind
    size_bytes: int
    sha256: str
    storage_provider: str
    storage_bucket: str
    storage_key: str
    public_url: str | None
    classification_status: str = DocumentClassificationStatus.CLASSIFIED.value
    extracted_text: str | None = None
    chunks: list[FakeChunkRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeExtractionRecord:
    document_id: UUID
    extraction_template_id: UUID
    status: str
    method: str | None
    extraction_result: dict | None
    extraction_metadata: dict | None
    extracted_at: datetime | None
    reviewed_at: datetime | None
    extraction_template: FakeTemplateRecord | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeDocumentRepository:
    def __init__(self, records: dict[UUID, FakeDocumentRecord]) -> None:
        self._records = records

    async def get(self, document_id: UUID) -> FakeDocumentRecord | None:
        return self._records.get(document_id)

    async def get_for_extraction(self, document_id: UUID) -> FakeDocumentRecord | None:
        return self._records.get(document_id)


class FakeTemplateRepository:
    def __init__(self, templates: dict[UUID, FakeTemplateRecord]) -> None:
        self._templates = templates

    async def get(self, template_id: UUID) -> FakeTemplateRecord | None:
        return self._templates.get(template_id)


class FakeExtractionRepository:
    def __init__(
        self,
        templates: dict[UUID, FakeTemplateRecord],
    ) -> None:
        self._templates = templates
        self._records: dict[UUID, FakeExtractionRecord] = {}

    async def get(self, document_id: UUID) -> FakeExtractionRecord | None:
        return self._records.get(document_id)

    async def upsert_session(
        self,
        *,
        document_id: UUID,
        template_id: UUID,
        status: DocumentExtractionStatus,
        method: DocumentExtractionMethod,
        metadata: dict | None,
    ) -> FakeExtractionRecord:
        record = FakeExtractionRecord(
            document_id=document_id,
            extraction_template_id=template_id,
            status=status.value,
            method=method.value,
            extraction_result=None,
            extraction_metadata=metadata,
            extracted_at=None,
            reviewed_at=None,
            extraction_template=self._templates[template_id],
        )
        self._records[document_id] = record
        return record

    async def save_result(
        self,
        *,
        extraction: FakeExtractionRecord,
        status: DocumentExtractionStatus,
        metadata: dict | None,
        result: dict | None,
        extracted_at: datetime | None,
        reviewed_at: datetime | None,
    ) -> FakeExtractionRecord:
        extraction.status = status.value
        extraction.extraction_metadata = metadata
        extraction.extraction_result = result
        extraction.extracted_at = extracted_at
        extraction.reviewed_at = reviewed_at
        extraction.updated_at = datetime.now(UTC)
        return extraction


class DummySessionContext:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class DummySessionFactory:
    def __call__(self) -> DummySessionContext:
        return DummySessionContext()


def build_result_payload() -> DocumentExtractionResultRead:
    return DocumentExtractionResultRead.model_validate(
        {
            "modules": [
                {
                    "key": "vendor_information",
                    "label": "Vendor Information",
                    "fields": [
                        {
                            "kind": "scalar",
                            "key": "vendor_name",
                            "label": "Vendor Name",
                            "value_type": "string",
                            "required": True,
                            "value": "Acme Corp",
                            "raw_value": "ACME CORP",
                            "confidence": 0.91,
                            "extraction_mode": "direct",
                            "evidence": {
                                "source_chunk_indices": [0],
                                "source_excerpt": "Vendor: Acme Corp",
                            },
                        }
                    ],
                }
            ]
        }
    )


def build_service(monkeypatch: pytest.MonkeyPatch) -> tuple[
    DocumentExtractionService,
    FakeDocumentRecord,
    FakeTemplateRecord,
    FakeExtractionRepository,
]:
    template = FakeTemplateRecord(
        id=UUID("00000000-0000-0000-0000-000000000100"),
        name="Vendor Invoice",
        locale="en",
        modules=[
            {
                "key": "vendor_information",
                "label": "Vendor Information",
                "fields": [],
            }
        ],
    )
    document = FakeDocumentRecord(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        original_filename="invoice.pdf",
        content_type="application/pdf",
        file_extension=".pdf",
        file_kind=DocumentKind.PDF,
        size_bytes=100,
        sha256="a" * 64,
        storage_provider="cloudflare_r2",
        storage_bucket="little-john-local",
        storage_key="documents/1/invoice.pdf",
        public_url=None,
        extracted_text="Vendor: Acme Corp",
        chunks=[FakeChunkRecord(chunk_index=0, content="Vendor: Acme Corp")],
    )

    documents = {document.id: document}
    templates = {template.id: template}
    extraction_repository = FakeExtractionRepository(templates)

    monkeypatch.setattr(
        "src.documents.extraction_service.DocumentRepository",
        lambda session: FakeDocumentRepository(documents),
    )
    monkeypatch.setattr(
        "src.documents.extraction_service.DocumentExtractionRepository",
        lambda session: extraction_repository,
    )
    monkeypatch.setattr(
        "src.documents.extraction_service.ExtractionTemplateRepository",
        lambda session: FakeTemplateRepository(templates),
    )

    return (
        DocumentExtractionService(DummySessionFactory()),
        document,
        template,
        extraction_repository,
    )


@pytest.mark.asyncio
async def test_start_ai_extraction_session_creates_processing_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, template, repository = build_service(monkeypatch)

    session = await service.start_ai_extraction_session(
        document_id=document.id,
        template_id=template.id,
    )

    stored = await repository.get(document.id)

    assert session.document_id == document.id
    assert session.template_id == template.id
    assert session.status == DocumentExtractionStatus.PROCESSING
    assert stored is not None
    assert stored.status == DocumentExtractionStatus.PROCESSING.value


@pytest.mark.asyncio
async def test_start_correction_session_marks_existing_draft_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, template, repository = build_service(monkeypatch)
    await service.start_ai_extraction_session(
        document_id=document.id,
        template_id=template.id,
    )
    await service.save_ai_draft(
        document_id=document.id,
        template_id=template.id,
        thread_id="thread-1",
        result=build_result_payload(),
        reasoning_summary="Initial extraction summary.",
    )

    session = await service.start_correction_session(document_id=document.id)
    stored = await repository.get(document.id)

    assert session.assistant_id == "document_extraction_correction_agent"
    assert session.document_id == document.id
    assert stored is not None
    assert stored.status == DocumentExtractionStatus.PROCESSING.value


@pytest.mark.asyncio
async def test_save_chat_correction_persists_updated_result_and_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, template, repository = build_service(monkeypatch)
    await service.start_ai_extraction_session(
        document_id=document.id,
        template_id=template.id,
    )
    await service.save_ai_draft(
        document_id=document.id,
        template_id=template.id,
        thread_id="thread-1",
        result=build_result_payload(),
        reasoning_summary="Initial extraction summary.",
    )

    corrected_result = build_result_payload().model_copy(deep=True)
    corrected_result.modules[0].fields[0].value = "Acme Corporation"
    corrected_result.modules[0].fields[0].raw_value = "Acme Corporation"

    await service.save_chat_correction(
        document_id=document.id,
        user_message="The vendor name is incorrect. Use Acme Corporation.",
        assistant_response="I updated the vendor name to Acme Corporation.",
        result=corrected_result,
        reasoning_summary="Updated the vendor name from the operator correction.",
    )

    stored = await repository.get(document.id)

    assert stored is not None
    assert stored.status == DocumentExtractionStatus.PENDING_REVIEW.value
    assert stored.extraction_result is not None
    assert (
        stored.extraction_result["modules"][0]["fields"][0]["value"]
        == "Acme Corporation"
    )

    metadata = parse_extraction_metadata(stored.extraction_metadata)
    assert metadata.reasoning_summary == "Updated the vendor name from the operator correction."
    assert [message.role for message in metadata.correction_messages] == [
        "user",
        "assistant",
    ]
    assert stored.method == DocumentExtractionMethod.AI.value
    assert stored.extraction_metadata is not None
    assert stored.extraction_metadata["thread_id"] == "thread-1"


@pytest.mark.asyncio
async def test_save_ai_draft_marks_extraction_pending_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, template, repository = build_service(monkeypatch)
    session = await service.start_ai_extraction_session(
        document_id=document.id,
        template_id=template.id,
    )
    result = build_result_payload()

    await service.save_ai_draft(
        document_id=document.id,
        template_id=template.id,
        thread_id=session.thread_id,
        result=result,
        reasoning_summary="Vendor details extracted from the first chunk.",
    )

    stored = await repository.get(document.id)
    assert stored is not None
    assert stored.status == DocumentExtractionStatus.PENDING_REVIEW.value
    assert stored.extraction_result is not None
    assert stored.extraction_result["modules"][0]["fields"][0]["value"] == "Acme Corp"
    assert stored.extraction_metadata is not None
    assert stored.extraction_metadata["overall_confidence"] == pytest.approx(0.91)


@pytest.mark.asyncio
async def test_confirm_review_marks_extraction_confirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, template, _ = build_service(monkeypatch)
    session = await service.start_ai_extraction_session(
        document_id=document.id,
        template_id=template.id,
    )
    result = build_result_payload()

    await service.save_ai_draft(
        document_id=document.id,
        template_id=template.id,
        thread_id=session.thread_id,
        result=result,
        reasoning_summary="Vendor details extracted from the first chunk.",
    )
    await service.save_correction_activity(
        document_id=document.id,
        payload=DocumentExtractionCorrectionActivityUpdate.model_validate(
            {
                "groups": [
                    {
                        "id": "turn-1",
                        "user_turn_index": 0,
                        "summary": "Applied the requested correction to the extraction draft.",
                        "status": "complete",
                        "expanded": False,
                        "items": [
                            {
                                "id": "event-1",
                                "kind": "progress",
                                "summary": "Running keyword search for vendor name evidence.",
                                "occurred_at": 1_710_000_000_000,
                            }
                        ],
                    }
                ]
            }
        ),
    )

    reviewed = DocumentExtractionReviewUpdate(result=result)
    extraction = await service.confirm_review(
        document_id=document.id,
        payload=reviewed,
    )

    assert extraction.status == DocumentExtractionStatus.CONFIRMED
    assert extraction.result is not None
    assert extraction.overall_confidence == pytest.approx(0.91)
    assert extraction.reviewed_at is not None
    assert len(extraction.correction_event_groups) == 1
    assert extraction.correction_event_groups[0].summary == (
        "Applied the requested correction to the extraction draft."
    )


@pytest.mark.asyncio
async def test_save_correction_activity_persists_event_groups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, template, repository = build_service(monkeypatch)
    await service.start_ai_extraction_session(
        document_id=document.id,
        template_id=template.id,
    )
    await service.save_ai_draft(
        document_id=document.id,
        template_id=template.id,
        thread_id="thread-1",
        result=build_result_payload(),
        reasoning_summary="Initial extraction summary.",
    )

    extraction = await service.save_correction_activity(
        document_id=document.id,
        payload=DocumentExtractionCorrectionActivityUpdate.model_validate(
            {
                "groups": [
                    {
                        "id": "turn-1",
                        "user_turn_index": 0,
                        "summary": "Applied the requested correction to the extraction draft.",
                        "status": "complete",
                        "expanded": False,
                        "items": [
                            {
                                "id": "event-1",
                                "kind": "progress",
                                "summary": "Running keyword search for vendor name evidence.",
                                "occurred_at": 1_710_000_000_000,
                            }
                        ],
                    }
                ]
            }
        ),
    )

    stored = await repository.get(document.id)

    assert stored is not None
    metadata = parse_extraction_metadata(stored.extraction_metadata)
    assert len(metadata.correction_event_groups) == 1
    assert metadata.correction_event_groups[0].summary == (
        "Applied the requested correction to the extraction draft."
    )
    assert len(extraction.correction_event_groups) == 1
