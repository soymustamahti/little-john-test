from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from src.document_categories.schemas import DocumentCategoryCreate, DocumentCategoryUpdate
from src.document_categories.service import DocumentCategoryService


@dataclass
class FakeDocumentCategoryRecord:
    id: UUID
    name: str
    label_key: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeDocumentCategoryRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, FakeDocumentCategoryRecord] = {}

    async def list(self) -> list[FakeDocumentCategoryRecord]:
        return sorted(self._records.values(), key=lambda record: record.name.lower())

    async def get(self, category_id: UUID) -> FakeDocumentCategoryRecord | None:
        return self._records.get(category_id)

    async def create(self, payload: DocumentCategoryCreate) -> FakeDocumentCategoryRecord:
        if any(
            record.name.lower() == payload.name.lower()
            or record.label_key.lower() == payload.label_key.lower()
            for record in self._records.values()
        ):
            raise IntegrityError(None, None, Exception("duplicate key"))

        record = FakeDocumentCategoryRecord(id=uuid4(), **payload.model_dump(mode="json"))
        self._records[record.id] = record
        return record

    async def update(
        self,
        category: FakeDocumentCategoryRecord,
        payload: DocumentCategoryUpdate,
    ) -> FakeDocumentCategoryRecord:
        next_name = payload.name or category.name
        next_label_key = payload.label_key or category.label_key
        if any(
            record.id != category.id
            and (
                record.name.lower() == next_name.lower()
                or record.label_key.lower() == next_label_key.lower()
            )
            for record in self._records.values()
        ):
            raise IntegrityError(None, None, Exception("duplicate key"))

        for field_name, value in payload.model_dump(exclude_unset=True, mode="json").items():
            setattr(category, field_name, value)
        category.updated_at = datetime.now(UTC)
        return category

    async def delete(self, category: FakeDocumentCategoryRecord) -> None:
        self._records.pop(category.id, None)


@pytest.mark.asyncio
async def test_list_document_categories_is_sorted_by_name() -> None:
    repository = FakeDocumentCategoryRepository()
    service = DocumentCategoryService(repository)

    await repository.create(DocumentCategoryCreate(name="Receipt", label_key="receipt"))
    await repository.create(
        DocumentCategoryCreate(name="Bank Statement", label_key="bank_statement")
    )

    categories = await service.list_document_categories()

    assert [category.name for category in categories] == ["Bank Statement", "Receipt"]


@pytest.mark.asyncio
async def test_create_document_category_returns_conflict_on_duplicate_name() -> None:
    repository = FakeDocumentCategoryRepository()
    service = DocumentCategoryService(repository)

    await service.create_document_category(
        DocumentCategoryCreate(name="Invoice", label_key="invoice")
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_document_category(
            DocumentCategoryCreate(name="Invoice", label_key="invoice_duplicate")
        )

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_document_category_raises_404_for_unknown_id() -> None:
    service = DocumentCategoryService(FakeDocumentCategoryRepository())

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_document_category(uuid4())

    assert exc_info.value.status_code == 404
    assert "Document category" in exc_info.value.detail
