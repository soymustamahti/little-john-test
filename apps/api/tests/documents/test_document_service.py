import io
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import HTTPException
from src.documents.schemas import DocumentCreateRecord, DocumentKind
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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeDocumentRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, FakeDocumentRecord] = {}
        self.fail_on_create = False

    async def list(self) -> list[FakeDocumentRecord]:
        return sorted(self._records.values(), key=lambda record: record.created_at, reverse=True)

    async def get(self, document_id: UUID) -> FakeDocumentRecord | None:
        return self._records.get(document_id)

    async def create(self, payload: DocumentCreateRecord) -> FakeDocumentRecord:
        if self.fail_on_create:
            raise RuntimeError("database write failed")

        record = FakeDocumentRecord(**payload.model_dump())
        self._records[record.id] = record
        return record

    async def delete(self, document: FakeDocumentRecord) -> None:
        self._records.pop(document.id, None)


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


def build_service(
    repository: FakeDocumentRepository | None = None,
    storage: FakeObjectStorage | None = None,
) -> tuple[DocumentService, FakeDocumentRepository, FakeObjectStorage]:
    repository = repository or FakeDocumentRepository()
    storage = storage or FakeObjectStorage()
    service = DocumentService(repository, storage, max_upload_size_bytes=1024 * 1024)
    return service, repository, storage


def build_docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


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
    assert list(storage.objects) == [next(iter(repository._records.values())).storage_key]


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
