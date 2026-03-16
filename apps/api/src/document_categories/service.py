from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.document_categories.repository import DocumentCategoryRepository
from src.document_categories.schemas import (
    DocumentCategoryCreate,
    DocumentCategoryRead,
    DocumentCategoryUpdate,
)


class DocumentCategoryService:
    def __init__(self, repository: DocumentCategoryRepository) -> None:
        self._repository = repository

    async def list_document_categories(self) -> list[DocumentCategoryRead]:
        categories = await self._repository.list()
        return [DocumentCategoryRead.model_validate(category) for category in categories]

    async def get_document_category(self, category_id: UUID) -> DocumentCategoryRead:
        category = await self._repository.get(category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document category {category_id} was not found.",
            )
        return DocumentCategoryRead.model_validate(category)

    async def create_document_category(
        self,
        payload: DocumentCategoryCreate,
    ) -> DocumentCategoryRead:
        try:
            category = await self._repository.create(payload)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document category '{payload.name}' already exists.",
            ) from exc

        return DocumentCategoryRead.model_validate(category)

    async def update_document_category(
        self,
        category_id: UUID,
        payload: DocumentCategoryUpdate,
    ) -> DocumentCategoryRead:
        category = await self._repository.get(category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document category {category_id} was not found.",
            )

        try:
            updated_category = await self._repository.update(category, payload)
        except IntegrityError as exc:
            attempted_name = payload.name or category.name
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document category '{attempted_name}' already exists.",
            ) from exc

        return DocumentCategoryRead.model_validate(updated_category)

    async def delete_document_category(self, category_id: UUID) -> None:
        category = await self._repository.get(category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document category {category_id} was not found.",
            )
        await self._repository.delete(category)
