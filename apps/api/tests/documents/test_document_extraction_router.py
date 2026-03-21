from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.documents.extraction import DocumentExtractionStatus
from src.documents.extraction_schemas import (
    DocumentExtractionCorrectionActivityUpdate,
    DocumentExtractionCorrectionSessionRead,
    DocumentExtractionRead,
    DocumentExtractionReviewUpdate,
    DocumentExtractionSessionRead,
)
from src.documents.router import get_document_extraction_service, router


class FakeDocumentExtractionService:
    def __init__(self) -> None:
        self.start_calls: list[tuple[str, str]] = []
        self.get_calls: list[str] = []
        self.review_calls: list[str] = []
        self.activity_calls: list[str] = []

    async def start_ai_extraction_session(
        self,
        *,
        document_id,
        template_id,
    ) -> DocumentExtractionSessionRead:
        self.start_calls.append((str(document_id), str(template_id)))
        return DocumentExtractionSessionRead(
            assistant_id="document_extraction_agent",
            thread_id="thread-789",
            document_id=document_id,
            template_id=template_id,
            status=DocumentExtractionStatus.PROCESSING,
        )

    async def get_extraction(self, document_id) -> DocumentExtractionRead:
        self.get_calls.append(str(document_id))
        return build_extraction_payload(document_id)

    async def start_correction_session(
        self,
        *,
        document_id,
    ) -> DocumentExtractionCorrectionSessionRead:
        return DocumentExtractionCorrectionSessionRead(
            assistant_id="document_extraction_correction_agent",
            thread_id="thread-correction-123",
            document_id=document_id,
            status=DocumentExtractionStatus.PROCESSING,
        )

    async def confirm_review(
        self,
        *,
        document_id,
        payload: DocumentExtractionReviewUpdate,
    ) -> DocumentExtractionRead:
        self.review_calls.append(str(document_id))
        return build_extraction_payload(document_id, status="confirmed")

    async def save_correction_activity(
        self,
        *,
        document_id,
        payload: DocumentExtractionCorrectionActivityUpdate,
    ) -> DocumentExtractionRead:
        self.activity_calls.append(str(document_id))
        return build_extraction_payload(document_id)


def build_extraction_payload(
    document_id,
    *,
    status: str = "pending_review",
) -> DocumentExtractionRead:
    now = "2026-03-18T12:00:00Z"
    return DocumentExtractionRead.model_validate(
        {
            "document_id": str(document_id),
            "status": status,
            "method": "ai",
            "template": {
                "id": str(uuid4()),
                "name": "Vendor Invoice",
                "locale": "en",
            },
            "thread_id": "thread-789",
            "overall_confidence": 0.87,
            "reasoning_summary": "Vendor evidence was found in the first chunk.",
            "error": None,
            "correction_event_groups": [],
            "result": {
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
                                "confidence": 0.87,
                                "extraction_mode": "direct",
                                "evidence": {
                                    "source_chunk_indices": [0],
                                    "source_excerpt": "Vendor: Acme Corp",
                                },
                            }
                        ],
                    }
                ]
            },
            "extracted_at": now,
            "reviewed_at": now if status == "confirmed" else None,
            "created_at": now,
            "updated_at": now,
        }
    )


def build_client(service: FakeDocumentExtractionService) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_document_extraction_service] = lambda: service
    return TestClient(app)


def test_ai_extraction_session_endpoint_returns_bootstrap_payload() -> None:
    service = FakeDocumentExtractionService()
    client = build_client(service)
    document_id = uuid4()
    template_id = uuid4()

    response = client.post(
        f"/api/documents/{document_id}/extraction/ai-session",
        json={"template_id": str(template_id)},
    )

    assert response.status_code == 200
    assert service.start_calls == [(str(document_id), str(template_id))]
    assert response.json() == {
        "assistant_id": "document_extraction_agent",
        "thread_id": "thread-789",
        "document_id": str(document_id),
        "template_id": str(template_id),
        "status": "processing",
    }


def test_get_document_extraction_endpoint_returns_extraction_payload() -> None:
    service = FakeDocumentExtractionService()
    client = build_client(service)
    document_id = uuid4()

    response = client.get(f"/api/documents/{document_id}/extraction")

    assert response.status_code == 200
    assert service.get_calls == [str(document_id)]
    assert response.json()["status"] == "pending_review"


def test_document_extraction_correction_session_endpoint_returns_bootstrap_payload() -> None:
    service = FakeDocumentExtractionService()
    client = build_client(service)
    document_id = uuid4()

    response = client.post(f"/api/documents/{document_id}/extraction/correction-session")

    assert response.status_code == 200
    assert response.json() == {
      "assistant_id": "document_extraction_correction_agent",
      "thread_id": "thread-correction-123",
      "document_id": str(document_id),
      "status": "processing",
    }


def test_confirm_document_extraction_review_endpoint_returns_confirmed_payload() -> None:
    service = FakeDocumentExtractionService()
    client = build_client(service)
    document_id = uuid4()

    response = client.put(
        f"/api/documents/{document_id}/extraction/review",
        json={
            "result": {
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
                                "confidence": 0.87,
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
        },
    )

    assert response.status_code == 200
    assert service.review_calls == [str(document_id)]
    assert response.json()["status"] == "confirmed"


def test_save_document_extraction_correction_activity_endpoint_returns_payload() -> None:
    service = FakeDocumentExtractionService()
    client = build_client(service)
    document_id = uuid4()

    response = client.put(
        f"/api/documents/{document_id}/extraction/correction-activity",
        json={
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
                            "occurred_at": 1710000000000,
                        }
                    ],
                }
            ]
        },
    )

    assert response.status_code == 200
    assert service.activity_calls == [str(document_id)]
