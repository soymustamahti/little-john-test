from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.documents.classification import (
    DocumentClassificationMethod,
    DocumentClassificationStatus,
    SuggestedDocumentCategory,
)
from src.documents.classification_service import DocumentClassificationService
from src.documents.schemas import DocumentKind


@dataclass
class FakeDocumentCategoryRecord:
    id: UUID
    name: str
    label_key: str
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
    document_category_id: UUID | None = None
    classification_status: str = DocumentClassificationStatus.UNCLASSIFIED.value
    classification_method: str | None = None
    classification_metadata: dict | None = None
    classified_at: datetime | None = None
    content_source: str | None = None
    extracted_text: str | None = None
    extraction_metadata: dict | None = None
    processed_at: datetime | None = None
    document_category: FakeDocumentCategoryRecord | None = None
    chunks: list[FakeChunkRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeDocumentRepository:
    def __init__(
        self,
        records: dict[UUID, FakeDocumentRecord],
        categories: dict[UUID, FakeDocumentCategoryRecord],
    ) -> None:
        self._records = records
        self._categories = categories

    async def get(self, document_id: UUID) -> FakeDocumentRecord | None:
        return self._records.get(document_id)

    async def get_for_classification(self, document_id: UUID) -> FakeDocumentRecord | None:
        return self._records.get(document_id)

    async def update_classification(
        self,
        document: FakeDocumentRecord,
        *,
        document_category_id: UUID | None,
        classification_status: DocumentClassificationStatus,
        classification_method: DocumentClassificationMethod | None,
        classification_metadata: dict | None,
        classified_at: datetime | None,
    ) -> FakeDocumentRecord:
        document.document_category_id = document_category_id
        document.document_category = (
            self._categories.get(document_category_id) if document_category_id is not None else None
        )
        document.classification_status = classification_status.value
        document.classification_method = (
            classification_method.value if classification_method is not None else None
        )
        document.classification_metadata = classification_metadata
        document.classified_at = classified_at
        document.updated_at = datetime.now(UTC)
        return document


class FakeDocumentCategoryRepository:
    def __init__(self, categories: dict[UUID, FakeDocumentCategoryRecord]) -> None:
        self._categories = categories

    async def get(self, category_id: UUID) -> FakeDocumentCategoryRecord | None:
        return self._categories.get(category_id)

    async def list_all(self) -> list[FakeDocumentCategoryRecord]:
        return list(self._categories.values())

    async def get_by_name(self, normalized_name: str) -> FakeDocumentCategoryRecord | None:
        for category in self._categories.values():
            if category.name.lower() == normalized_name.lower():
                return category
        return None

    async def get_by_label_key(
        self,
        normalized_label_key: str,
    ) -> FakeDocumentCategoryRecord | None:
        for category in self._categories.values():
            if category.label_key.lower() == normalized_label_key.lower():
                return category
        return None

    async def create(self, payload) -> FakeDocumentCategoryRecord:
        category = FakeDocumentCategoryRecord(
            id=uuid4(),
            name=payload.name,
            label_key=payload.label_key,
        )
        self._categories[category.id] = category
        return category


class DummySessionContext:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class DummySessionFactory:
    def __call__(self) -> DummySessionContext:
        return DummySessionContext()


def build_service(monkeypatch: pytest.MonkeyPatch) -> tuple[
    DocumentClassificationService,
    FakeDocumentRecord,
    dict[UUID, FakeDocumentCategoryRecord],
]:
    category = FakeDocumentCategoryRecord(
        id=UUID("00000000-0000-0000-0000-000000000010"),
        name="Invoice",
        label_key="invoice",
    )
    categories = {category.id: category}
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
        extracted_text="Invoice total due on 2026-03-17.",
        chunks=[FakeChunkRecord(chunk_index=0, content="Invoice total due on 2026-03-17.")],
    )
    records = {document.id: document}
    fake_document_repository = FakeDocumentRepository(records, categories)
    fake_category_repository = FakeDocumentCategoryRepository(categories)

    monkeypatch.setattr(
        "src.documents.classification_service.DocumentRepository",
        lambda session: fake_document_repository,
    )
    monkeypatch.setattr(
        "src.documents.classification_service.DocumentCategoryRepository",
        lambda session: fake_category_repository,
    )

    service = DocumentClassificationService(DummySessionFactory())
    return service, document, categories


@pytest.mark.asyncio
async def test_start_ai_classification_session_marks_document_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, _ = build_service(monkeypatch)

    session = await service.start_ai_classification_session(document.id)

    assert session.document_id == document.id
    assert session.status == DocumentClassificationStatus.PROCESSING
    assert document.classification_status == DocumentClassificationStatus.PROCESSING.value
    assert document.classification_method == DocumentClassificationMethod.AI.value
    assert document.classification_metadata["thread_id"] == session.thread_id


@pytest.mark.asyncio
async def test_apply_manual_classification_assigns_existing_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, categories = build_service(monkeypatch)
    category = next(iter(categories.values()))

    result = await service.apply_manual_classification(document.id, category.id)

    assert result.classification.status == DocumentClassificationStatus.CLASSIFIED
    assert result.classification.method == DocumentClassificationMethod.MANUAL
    assert result.classification.category is not None
    assert result.classification.category.id == category.id
    assert document.document_category_id == category.id


@pytest.mark.asyncio
async def test_record_ai_suggestion_marks_document_pending_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, _ = build_service(monkeypatch)

    await service.record_ai_suggestion(
        document_id=document.id,
        thread_id="thread-123",
        suggested_category=SuggestedDocumentCategory(
            name="Utility Bill",
            label_key="utility_bill",
        ),
        confidence=0.74,
        rationale="The excerpt looks like a recurring household bill.",
        sampled_chunk_indices=[0],
        excerpt_character_count=42,
    )

    assert document.classification_status == DocumentClassificationStatus.PENDING_REVIEW.value
    assert document.classification_metadata["thread_id"] == "thread-123"
    assert document.classification_metadata["suggested_category"]["label_key"] == "utility_bill"


@pytest.mark.asyncio
async def test_accept_ai_suggested_category_creates_missing_category_and_assigns_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, document, categories = build_service(monkeypatch)
    categories.clear()

    await service.accept_ai_suggested_category(
        document_id=document.id,
        thread_id="thread-456",
        suggested_category=SuggestedDocumentCategory(
            name="Utility Bill",
            label_key="utility_bill",
        ),
        confidence=0.81,
        rationale="The excerpt is closer to a utility bill than any seeded category.",
        sampled_chunk_indices=[0],
        excerpt_character_count=42,
    )

    assert document.classification_status == DocumentClassificationStatus.CLASSIFIED.value
    assert document.document_category is not None
    assert document.document_category.label_key == "utility_bill"
    assert len(categories) == 1
