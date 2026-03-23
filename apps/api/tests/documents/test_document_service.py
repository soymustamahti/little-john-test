import io
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import HTTPException
from src.core.pagination import PaginatedResult, PaginationParams
from src.documents.processing import DocumentProcessingError
from src.documents.processing_schemas import ChunkEmbedding, ProcessedDocumentContent
from src.documents.schemas import DocumentChunkCreateRecord, DocumentCreateRecord, DocumentKind
from src.documents.service import DocumentContentRead, DocumentService, UploadedDocumentInput
from src.storage.object_store import ObjectStorageError, RetrievedObject, StoredObject


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
    content_source: str | None = None
    extracted_text: str | None = None
    extraction_metadata: dict | None = None
    processed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeDocumentRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, FakeDocumentRecord] = {}
        self._chunks: dict[UUID, list[DocumentChunkCreateRecord]] = {}
        self.fail_on_create = False

    async def list(self, pagination: PaginationParams) -> PaginatedResult[FakeDocumentRecord]:
        items = sorted(self._records.values(), key=lambda record: record.created_at, reverse=True)
        start = pagination.offset
        end = start + pagination.page_size
        return PaginatedResult(items=items[start:end], total_items=len(items))

    async def get(self, document_id: UUID) -> FakeDocumentRecord | None:
        return self._records.get(document_id)

    async def create(
        self,
        payload: DocumentCreateRecord,
        *,
        chunks: Sequence[DocumentChunkCreateRecord] = (),
    ) -> FakeDocumentRecord:
        if self.fail_on_create:
            raise RuntimeError("database write failed")

        record = FakeDocumentRecord(**payload.model_dump())
        self._records[record.id] = record
        self._chunks[record.id] = list(chunks)
        return record

    async def delete(self, document: FakeDocumentRecord) -> None:
        self._records.pop(document.id, None)
        self._chunks.pop(document.id, None)


class FakeObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted_keys: list[str] = []
        self.fail_on_upload = False
        self.fail_on_delete = False
        self.fail_on_download = False

    async def upload_object(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        if self.fail_on_upload:
            raise ObjectStorageError("upload failed")

        self.objects[key] = content
        return StoredObject(
            provider="cloudflare_r2",
            bucket="little-john-local",
            key=key,
            public_url=f"https://files.example.com/{key}",
        )

    async def delete_object(self, *, key: str) -> None:
        if self.fail_on_delete:
            raise ObjectStorageError("delete failed")

        self.deleted_keys.append(key)
        self.objects.pop(key, None)

    async def download_object(self, *, key: str) -> RetrievedObject:
        if self.fail_on_download:
            raise ObjectStorageError("download failed")

        return RetrievedObject(
            content=self.objects[key],
            content_type="application/pdf",
        )


class FakeDocumentProcessingService:
    async def process_document(
        self,
        *,
        filename: str,
        file_extension: str,
        content_type: str,
        content: bytes,
    ) -> ProcessedDocumentContent:
        return ProcessedDocumentContent(
            text=f"processed::{filename}",
            content_source=f"source::{file_extension}",
            metadata={
                "character_count": len(filename),
                "chunk_count": 1,
                "embedding_provider": "openai",
                "embedding_model": "text-embedding-3-small",
            },
            chunks=[
                ChunkEmbedding(
                    chunk_index=0,
                    content=f"chunk::{filename}",
                    content_start_offset=0,
                    content_end_offset=len(filename),
                    embedding=[0.1, 0.2, 0.3],
                )
            ],
        )


class FailingDocumentProcessingService:
    async def process_document(
        self,
        *,
        filename: str,
        file_extension: str,
        content_type: str,
        content: bytes,
    ) -> ProcessedDocumentContent:
        raise DocumentProcessingError("processing failed", status_code=422)


def build_service(
    repository: FakeDocumentRepository | None = None,
    storage: FakeObjectStorage | None = None,
    processing_service: FakeDocumentProcessingService | None = None,
) -> tuple[DocumentService, FakeDocumentRepository, FakeObjectStorage]:
    repository = repository or FakeDocumentRepository()
    storage = storage or FakeObjectStorage()
    processing_service = processing_service or FakeDocumentProcessingService()
    service = DocumentService(
        repository,
        storage,
        processing_service,
        max_upload_size_bytes=1024 * 1024,
    )
    return service, repository, storage


def build_docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_list_documents_returns_paginated_response() -> None:
    service, repository, _ = build_service()

    await repository.create(
        DocumentCreateRecord(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            original_filename="older.pdf",
            content_type="application/pdf",
            file_extension=".pdf",
            file_kind=DocumentKind.PDF,
            size_bytes=10,
            sha256="1" * 64,
            storage_provider="cloudflare_r2",
            storage_bucket="little-john-local",
            storage_key="documents/1/older.pdf",
            public_url=None,
        )
    )
    await repository.create(
        DocumentCreateRecord(
            id=UUID("00000000-0000-0000-0000-000000000002"),
            original_filename="newer.pdf",
            content_type="application/pdf",
            file_extension=".pdf",
            file_kind=DocumentKind.PDF,
            size_bytes=10,
            sha256="2" * 64,
            storage_provider="cloudflare_r2",
            storage_bucket="little-john-local",
            storage_key="documents/2/newer.pdf",
            public_url=None,
        )
    )

    result = await service.list_documents(PaginationParams(page=1, page_size=1))

    assert result.page == 1
    assert result.page_size == 1
    assert result.total_items == 2
    assert result.total_pages == 2
    assert [document.original_filename for document in result.items] == ["newer.pdf"]


@pytest.mark.asyncio
async def test_upload_document_persists_pdf_metadata_and_object() -> None:
    service, repository, storage = build_service()

    created_document = await service.upload_document(
        UploadedDocumentInput(
            filename=r"C:\fakepath\Invoice March 2026.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4\nexample payload",
        )
    )

    assert created_document.original_filename == "Invoice March 2026.pdf"
    assert created_document.file_kind == DocumentKind.PDF
    assert created_document.file_extension == ".pdf"
    assert created_document.public_url is not None
    assert len(repository._records) == 1
    stored_record = next(iter(repository._records.values()))
    assert stored_record.extracted_text == "processed::Invoice March 2026.pdf"
    assert stored_record.content_source == "source::.pdf"
    assert repository._chunks[stored_record.id][0].content == "chunk::Invoice March 2026.pdf"
    assert list(storage.objects) == [stored_record.storage_key]


@pytest.mark.asyncio
async def test_upload_document_accepts_docx_files() -> None:
    service, _, _ = build_service()

    created_document = await service.upload_document(
        UploadedDocumentInput(
            filename="contract.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            content=build_docx_bytes(),
        )
    )

    assert created_document.file_kind == DocumentKind.DOCX
    assert created_document.file_extension == ".docx"


@pytest.mark.asyncio
async def test_upload_document_rejects_filenames_with_control_characters() -> None:
    service, _, _ = build_service()

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(
            UploadedDocumentInput(
                filename="invoice\n2026.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.4\nexample payload",
            )
        )

    assert exc_info.value.status_code == 400
    assert "control characters" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_document_rejects_unsupported_extension() -> None:
    service, _, storage = build_service()

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(
            UploadedDocumentInput(
                filename="payload.exe",
                content_type="application/octet-stream",
                content=b"MZnot-allowed",
            )
        )

    assert exc_info.value.status_code == 415
    assert "Unsupported file type" in exc_info.value.detail
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_upload_document_rejects_invalid_pdf_signature() -> None:
    service, _, _ = build_service()

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(
            UploadedDocumentInput(
                filename="invoice.pdf",
                content_type="application/pdf",
                content=b"not-a-real-pdf",
            )
        )

    assert exc_info.value.status_code == 415
    assert "valid PDF header" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_document_stops_before_object_upload_when_processing_fails() -> None:
    storage = FakeObjectStorage()
    service, _, _ = build_service(
        storage=storage,
        processing_service=FailingDocumentProcessingService(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(
            UploadedDocumentInput(
                filename="invoice.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.4\npayload",
            )
        )

    assert exc_info.value.status_code == 422
    assert "processing failed" in exc_info.value.detail
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_delete_document_removes_metadata_and_r2_object() -> None:
    service, repository, storage = build_service()
    created_document = await service.upload_document(
        UploadedDocumentInput(
            filename="receipt.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4\nreceipt",
        )
    )

    await service.delete_document(created_document.id)

    assert repository._records == {}
    assert storage.deleted_keys
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_upload_document_cleans_up_object_when_repository_create_fails() -> None:
    repository = FakeDocumentRepository()
    repository.fail_on_create = True
    storage = FakeObjectStorage()
    service, _, _ = build_service(repository=repository, storage=storage)

    with pytest.raises(RuntimeError) as exc_info:
        await service.upload_document(
            UploadedDocumentInput(
                filename="invoice.pdf",
                content_type="application/pdf",
                content=b"%PDF-1.4\npayload",
            )
        )

    assert "database write failed" in str(exc_info.value)
    assert storage.objects == {}
    assert len(storage.deleted_keys) == 1


@pytest.mark.asyncio
async def test_get_document_content_returns_bytes_for_existing_document() -> None:
    service, _, _ = build_service()
    created_document = await service.upload_document(
        UploadedDocumentInput(
            filename="invoice.pdf",
            content_type="application/pdf",
            content=b"%PDF-1.4\npreview",
        )
    )

    content = await service.get_document_content(created_document.id)

    assert isinstance(content, DocumentContentRead)
    assert content.content == b"%PDF-1.4\npreview"
    assert content.content_type == "application/pdf"
    assert content.original_filename == "invoice.pdf"
