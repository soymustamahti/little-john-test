from functools import lru_cache
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.database import get_async_db_session
from src.core.pagination import PaginatedResponse, PaginationParams, get_pagination_params
from src.documents.repository import DocumentRepository
from src.documents.schemas import DocumentRead
from src.documents.service import DocumentService, UploadedDocumentInput
from src.storage.r2 import R2ObjectStorage

router = APIRouter(prefix="/api/documents", tags=["documents"])


@lru_cache
def get_r2_object_storage() -> R2ObjectStorage:
    settings = get_settings()
    return R2ObjectStorage(settings.r2)


def get_document_service(
    session: AsyncSession = Depends(get_async_db_session),
) -> DocumentService:
    settings = get_settings()
    repository = DocumentRepository(session)
    return DocumentService(
        repository,
        get_r2_object_storage(),
        max_upload_size_bytes=settings.documents.max_upload_size_bytes,
    )


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
