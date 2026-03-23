from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db_session
from src.core.pagination import PaginatedResponse, PaginationParams, get_pagination_params
from src.document_categories.repository import DocumentCategoryRepository
from src.document_categories.schemas import (
    DocumentCategoryCreate,
    DocumentCategoryRead,
    DocumentCategoryUpdate,
)
from src.document_categories.service import DocumentCategoryService

router = APIRouter(prefix="/api/document-categories", tags=["document-categories"])


def get_document_category_service(
    session: AsyncSession = Depends(get_async_db_session),
) -> DocumentCategoryService:
    repository = DocumentCategoryRepository(session)
    return DocumentCategoryService(repository)


@router.get("", response_model=PaginatedResponse[DocumentCategoryRead])
async def list_document_categories(
    pagination: PaginationParams = Depends(get_pagination_params),
    service: DocumentCategoryService = Depends(get_document_category_service),
) -> PaginatedResponse[DocumentCategoryRead]:
    return await service.list_document_categories(pagination)


@router.post("", response_model=DocumentCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_document_category(
    payload: DocumentCategoryCreate,
    service: DocumentCategoryService = Depends(get_document_category_service),
) -> DocumentCategoryRead:
    return await service.create_document_category(payload)


@router.get("/{category_id}", response_model=DocumentCategoryRead)
async def get_document_category(
    category_id: UUID,
    service: DocumentCategoryService = Depends(get_document_category_service),
) -> DocumentCategoryRead:
    return await service.get_document_category(category_id)


@router.patch("/{category_id}", response_model=DocumentCategoryRead)
async def update_document_category(
    category_id: UUID,
    payload: DocumentCategoryUpdate,
    service: DocumentCategoryService = Depends(get_document_category_service),
) -> DocumentCategoryRead:
    return await service.update_document_category(category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_category(
    category_id: UUID,
    service: DocumentCategoryService = Depends(get_document_category_service),
) -> Response:
    await service.delete_document_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
