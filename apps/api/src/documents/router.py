from functools import lru_cache
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_async_db_session, get_async_session_factory
from src.core.pagination import PaginatedResponse, PaginationParams, get_pagination_params
from src.documents.classification_service import DocumentClassificationService
from src.documents.extraction_schemas import (
    DocumentExtractionCorrectionActivityUpdate,
    DocumentExtractionCorrectionSessionRead,
    DocumentExtractionRead,
    DocumentExtractionReviewUpdate,
    DocumentExtractionSessionCreate,
    DocumentExtractionSessionRead,
)
from src.documents.extraction_service import DocumentExtractionService
from src.documents.repository import DocumentRepository
from src.documents.runtime import (
    get_document_extraction_service as get_runtime_document_extraction_service,
)
from src.documents.runtime import (
    get_document_processing_service,
    get_r2_object_storage,
)
from src.documents.schemas import (
    DocumentClassificationSessionRead,
    DocumentRead,
    ManualDocumentClassificationRequest,
)
from src.documents.service import DocumentService, UploadedDocumentInput

router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_document_service(
    session: AsyncSession = Depends(get_async_db_session),
) -> DocumentService:
    settings = get_settings()
    repository = DocumentRepository(session)
    return DocumentService(
        repository,
        get_r2_object_storage(),
        get_document_processing_service(),
        max_upload_size_bytes=settings.documents.max_upload_size_bytes,
    )


@lru_cache
def get_document_classification_service() -> DocumentClassificationService:
    return DocumentClassificationService(get_async_session_factory())


@lru_cache
def get_document_extraction_service() -> DocumentExtractionService:
    return get_runtime_document_extraction_service()


async def read_upload_bytes(upload: UploadFile, max_size_bytes: int) -> bytes:
    content = bytearray()
    while chunk := await upload.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds the {max_size_bytes} byte limit.",
            )
    return bytes(content)


def build_inline_content_disposition(filename: str) -> str:
    ascii_fallback = "".join(
        char if 32 <= ord(char) < 127 and char not in {'"', "\\"} else "_"
        for char in filename
    ).strip()
    if not ascii_fallback:
        ascii_fallback = "document"
    encoded_filename = quote(filename, safe="")
    return f'inline; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_filename}'


@router.get("", response_model=PaginatedResponse[DocumentRead])
async def list_documents(
    pagination: PaginationParams = Depends(get_pagination_params),
    service: DocumentService = Depends(get_document_service),
) -> PaginatedResponse[DocumentRead]:
    return await service.list_documents(pagination)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    try:
        content = await read_upload_bytes(file, service.max_upload_size_bytes)
    finally:
        await file.close()

    return await service.upload_document(
        UploadedDocumentInput(
            filename=file.filename or "",
            content_type=file.content_type,
            content=content,
        )
    )


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    return await service.get_document(document_id)


@router.post(
    "/{document_id}/classification/manual",
    response_model=DocumentRead,
)
async def classify_document_manually(
    document_id: UUID,
    payload: ManualDocumentClassificationRequest,
    service: DocumentClassificationService = Depends(get_document_classification_service),
) -> DocumentRead:
    return await service.apply_manual_classification(document_id, payload.category_id)


@router.post(
    "/{document_id}/classification/ai-session",
    response_model=DocumentClassificationSessionRead,
)
async def create_document_ai_classification_session(
    document_id: UUID,
    service: DocumentClassificationService = Depends(get_document_classification_service),
) -> DocumentClassificationSessionRead:
    return await service.start_ai_classification_session(document_id)


@router.post(
    "/{document_id}/extraction/ai-session",
    response_model=DocumentExtractionSessionRead,
)
async def create_document_ai_extraction_session(
    document_id: UUID,
    payload: DocumentExtractionSessionCreate,
    service: DocumentExtractionService = Depends(get_document_extraction_service),
) -> DocumentExtractionSessionRead:
    return await service.start_ai_extraction_session(
        document_id=document_id,
        template_id=payload.template_id,
    )


@router.post(
    "/{document_id}/extraction/correction-session",
    response_model=DocumentExtractionCorrectionSessionRead,
)
async def create_document_extraction_correction_session(
    document_id: UUID,
    service: DocumentExtractionService = Depends(get_document_extraction_service),
) -> DocumentExtractionCorrectionSessionRead:
    return await service.start_correction_session(document_id=document_id)


@router.get(
    "/{document_id}/extraction",
    response_model=DocumentExtractionRead,
)
async def get_document_extraction(
    document_id: UUID,
    service: DocumentExtractionService = Depends(get_document_extraction_service),
) -> DocumentExtractionRead:
    return await service.get_extraction(document_id)


@router.put(
    "/{document_id}/extraction/correction-activity",
    response_model=DocumentExtractionRead,
)
async def save_document_extraction_correction_activity(
    document_id: UUID,
    payload: DocumentExtractionCorrectionActivityUpdate,
    service: DocumentExtractionService = Depends(get_document_extraction_service),
) -> DocumentExtractionRead:
    return await service.save_correction_activity(
        document_id=document_id,
        payload=payload,
    )


@router.put(
    "/{document_id}/extraction/review",
    response_model=DocumentExtractionRead,
)
async def confirm_document_extraction_review(
    document_id: UUID,
    payload: DocumentExtractionReviewUpdate,
    service: DocumentExtractionService = Depends(get_document_extraction_service),
) -> DocumentExtractionRead:
    return await service.confirm_review(document_id=document_id, payload=payload)


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
) -> Response:
    document = await service.get_document_content(document_id)
    return Response(
        content=document.content,
        media_type=document.content_type,
        headers={
            "Content-Disposition": build_inline_content_disposition(document.original_filename),
            "Cache-Control": "private, max-age=60",
        },
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
) -> Response:
    await service.delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
