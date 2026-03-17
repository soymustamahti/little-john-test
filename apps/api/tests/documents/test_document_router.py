from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.documents.router import get_document_service, router
from src.documents.schemas import DocumentKind, DocumentRead
from src.documents.service import DocumentContentRead, UploadedDocumentInput


class FakeDocumentService:
    def __init__(self, *, max_upload_size_bytes: int = 1024 * 1024) -> None:
        self.max_upload_size_bytes = max_upload_size_bytes
        self.upload_calls: list[UploadedDocumentInput] = []

    async def list_documents(self) -> list[DocumentRead]:
        return []

    async def upload_document(self, upload: UploadedDocumentInput) -> DocumentRead:
        self.upload_calls.append(upload)
        now = "2026-03-17T12:00:00Z"
        return DocumentRead.model_validate(
            {
                "id": str(uuid4()),
                "original_filename": upload.filename,
                "content_type": "application/pdf",
                "file_extension": ".pdf",
                "file_kind": DocumentKind.PDF,
                "size_bytes": len(upload.content),
                "sha256": "a" * 64,
                "public_url": None,
                "created_at": now,
                "updated_at": now,
            }
        )

    async def get_document(self, document_id):  # pragma: no cover - unused in these tests
        raise NotImplementedError

    async def get_document_content(self, document_id) -> DocumentContentRead:
        return DocumentContentRead(
            content=b"%PDF-1.4\npreview",
            content_type="application/pdf",
            original_filename='report "Q1".pdf',
        )

    async def delete_document(self, document_id) -> None:  # pragma: no cover - unused in tests
        raise NotImplementedError


def build_client(service: FakeDocumentService) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_document_service] = lambda: service
    return TestClient(app)


def test_upload_document_returns_413_before_service_for_oversized_payload() -> None:
    service = FakeDocumentService(max_upload_size_bytes=8)
    client = build_client(service)

    response = client.post(
        "/api/documents",
        files={"file": ("invoice.pdf", b"%PDF-1.4\npayload", "application/pdf")},
    )

    assert response.status_code == 413
    assert "byte limit" in response.json()["detail"]
    assert service.upload_calls == []


def test_get_document_content_sets_safe_content_disposition_header() -> None:
    service = FakeDocumentService()
    client = build_client(service)

    response = client.get(f"/api/documents/{uuid4()}/content")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == 'inline; filename="report _Q1_.pdf"; filename*=UTF-8\'\'report%20%22Q1%22.pdf'
    )
