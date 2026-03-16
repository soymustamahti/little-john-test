from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.document_categories.model import DocumentCategoryModel
from src.document_categories.schemas import DocumentCategoryCreate, DocumentCategoryUpdate


class DocumentCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[DocumentCategoryModel]:
        result = await self._session.execute(
            select(DocumentCategoryModel).order_by(DocumentCategoryModel.name.asc())
        )
        return list(result.scalars().all())

    async def get(self, category_id: UUID) -> DocumentCategoryModel | None:
        result = await self._session.execute(
            select(DocumentCategoryModel).where(DocumentCategoryModel.id == category_id)
        )
        return result.scalar_one_or_none()

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
