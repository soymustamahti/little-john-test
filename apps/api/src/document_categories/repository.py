from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.pagination import PaginatedResult, PaginationParams
from src.document_categories.model import DocumentCategoryModel
from src.document_categories.schemas import DocumentCategoryCreate, DocumentCategoryUpdate


class DocumentCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        pagination: PaginationParams,
    ) -> PaginatedResult[DocumentCategoryModel]:
        total_items = await self._session.scalar(
            select(func.count()).select_from(DocumentCategoryModel)
        )
        result = await self._session.execute(
            select(DocumentCategoryModel)
            .order_by(DocumentCategoryModel.name.asc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        return PaginatedResult(
            items=list(result.scalars().all()),
            total_items=total_items or 0,
        )

    async def get(self, category_id: UUID) -> DocumentCategoryModel | None:
        result = await self._session.execute(
            select(DocumentCategoryModel).where(DocumentCategoryModel.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, normalized_name: str) -> DocumentCategoryModel | None:
        result = await self._session.execute(
            select(DocumentCategoryModel).where(
                func.lower(DocumentCategoryModel.name) == normalized_name.lower()
            )
        )
        return result.scalar_one_or_none()

    async def get_by_label_key(self, normalized_label_key: str) -> DocumentCategoryModel | None:
        result = await self._session.execute(
            select(DocumentCategoryModel).where(
                func.lower(DocumentCategoryModel.label_key) == normalized_label_key.lower()
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[DocumentCategoryModel]:
        result = await self._session.execute(
            select(DocumentCategoryModel).order_by(DocumentCategoryModel.name.asc())
        )
        return list(result.scalars().all())

    async def create(self, payload: DocumentCategoryCreate) -> DocumentCategoryModel:
        category = DocumentCategoryModel(**payload.model_dump(mode="json"))
        self._session.add(category)

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise

        await self._session.refresh(category)
        return category

    async def update(
        self,
        category: DocumentCategoryModel,
        payload: DocumentCategoryUpdate,
    ) -> DocumentCategoryModel:
        for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
            setattr(category, field, value)

        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise

        await self._session.refresh(category)
        return category

    async def delete(self, category: DocumentCategoryModel) -> None:
        await self._session.delete(category)
        await self._session.commit()
