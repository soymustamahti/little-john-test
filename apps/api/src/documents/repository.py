from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.documents.model import DocumentModel
from src.documents.schemas import DocumentCreateRecord


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self) -> list[DocumentModel]:
        result = await self._session.execute(
            select(DocumentModel).order_by(DocumentModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, document_id: UUID) -> DocumentModel | None:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: DocumentCreateRecord) -> DocumentModel:
        document = DocumentModel(**payload.model_dump())
        self._session.add(document)
        await self._session.commit()
        await self._session.refresh(document)
        return document

    async def delete(self, document: DocumentModel) -> None:
        await self._session.delete(document)
        await self._session.commit()
