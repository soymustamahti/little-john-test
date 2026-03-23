from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.documents.classification_service import DOCUMENT_CLASSIFICATION_ASSISTANT_ID
from src.documents.router import get_document_classification_service, router
from src.documents.schemas import (
    DocumentClassificationSessionRead,
    DocumentClassificationStatus,
    DocumentKind,
    DocumentRead,
)


class FakeDocumentClassificationService:
    def __init__(self) -> None:
        self.manual_calls: list[tuple[str, str]] = []
        self.ai_session_calls: list[str] = []

    async def apply_manual_classification(
        self,
        document_id,
        category_id,
    ) -> DocumentRead:
        self.manual_calls.append((str(document_id), str(category_id)))
        now = "2026-03-17T12:00:00Z"
        return DocumentRead.model_validate(
            {
                "id": str(document_id),
                "original_filename": "invoice.pdf",
                "content_type": "application/pdf",
                "file_extension": ".pdf",
                "file_kind": DocumentKind.PDF,
                "size_bytes": 123,
                "sha256": "a" * 64,
                "public_url": None,
                "classification": {
                    "status": "classified",
                    "method": "manual",
                    "confidence": None,
                    "rationale": None,
                    "thread_id": None,
                    "error": None,
                    "sampled_chunk_indices": [],
                    "excerpt_character_count": None,
                    "suggested_category": None,
                    "category": {
                        "id": str(category_id),
                        "name": "Invoice",
                        "label_key": "invoice",
                    },
                    "classified_at": now,
                },
                "created_at": now,
                "updated_at": now,
            }
        )

    async def start_ai_classification_session(
        self,
        document_id,
    ) -> DocumentClassificationSessionRead:
        self.ai_session_calls.append(str(document_id))
        return DocumentClassificationSessionRead(
            assistant_id=DOCUMENT_CLASSIFICATION_ASSISTANT_ID,
            thread_id="thread-123",
            document_id=document_id,
            status=DocumentClassificationStatus.PROCESSING,
        )


def build_client(service: FakeDocumentClassificationService) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_document_classification_service] = lambda: service
    return TestClient(app)


def test_manual_classification_endpoint_passes_document_and_category_ids() -> None:
    service = FakeDocumentClassificationService()
    client = build_client(service)
    document_id = uuid4()
    category_id = uuid4()

    response = client.post(
        f"/api/documents/{document_id}/classification/manual",
        json={"category_id": str(category_id)},
    )

    assert response.status_code == 200
    assert service.manual_calls == [(str(document_id), str(category_id))]
    assert response.json()["classification"]["category"]["id"] == str(category_id)


def test_ai_classification_session_endpoint_returns_thread_bootstrap_payload() -> None:
    service = FakeDocumentClassificationService()
    client = build_client(service)
    document_id = uuid4()

    response = client.post(f"/api/documents/{document_id}/classification/ai-session")

    assert response.status_code == 200
    assert service.ai_session_calls == [str(document_id)]
    assert response.json() == {
        "assistant_id": DOCUMENT_CLASSIFICATION_ASSISTANT_ID,
        "thread_id": "thread-123",
        "document_id": str(document_id),
        "status": "processing",
    }
