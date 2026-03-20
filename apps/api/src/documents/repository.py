from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.pagination import PaginatedResult, PaginationParams
from src.documents.classification import (
    DocumentClassificationMethod,
    DocumentClassificationStatus,
)
from src.documents.model import DocumentChunkModel, DocumentModel
from src.documents.schemas import DocumentChunkCreateRecord, DocumentCreateRecord


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, pagination: PaginationParams) -> PaginatedResult[DocumentModel]:
        total_items = await self._session.scalar(select(func.count()).select_from(DocumentModel))
        result = await self._session.execute(
            select(DocumentModel)
            .options(selectinload(DocumentModel.document_category))
            .order_by(DocumentModel.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        return PaginatedResult(
            items=list(result.scalars().all()),
            total_items=total_items or 0,
        )

    async def get(self, document_id: UUID) -> DocumentModel | None:
        result = await self._session.execute(
            select(DocumentModel)
            .options(selectinload(DocumentModel.document_category))
            .where(DocumentModel.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_for_classification(self, document_id: UUID) -> DocumentModel | None:
        result = await self._session.execute(
            select(DocumentModel)
            .options(
                selectinload(DocumentModel.chunks),
                selectinload(DocumentModel.document_category),
            )
            .where(DocumentModel.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_for_extraction(self, document_id: UUID) -> DocumentModel | None:
        result = await self._session.execute(
            select(DocumentModel)
            .options(
                selectinload(DocumentModel.chunks),
                selectinload(DocumentModel.document_category),
            )
            .where(DocumentModel.id == document_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        payload: DocumentCreateRecord,
        *,
        chunks: Sequence[DocumentChunkCreateRecord] = (),
    ) -> DocumentModel:
        document = DocumentModel(**payload.model_dump())
        self._session.add(document)

        for chunk in chunks:
            self._session.add(DocumentChunkModel(**chunk.model_dump()))

        await self._session.commit()
        await self._session.refresh(document)
        stored_document = await self.get(document.id)
        return stored_document or document

    async def delete(self, document: DocumentModel) -> None:
        await self._session.delete(document)
        await self._session.commit()

    async def update_classification(
        self,
        document: DocumentModel,
        *,
        document_category_id: UUID | None,
        classification_status: DocumentClassificationStatus,
        classification_method: DocumentClassificationMethod | None,
        classification_metadata: dict | None,
        classified_at: datetime | None,
    ) -> DocumentModel:
        document.document_category_id = document_category_id
        document.classification_status = classification_status.value
        document.classification_method = (
            classification_method.value if classification_method is not None else None
        )
        document.classification_metadata = classification_metadata
        document.classified_at = classified_at

        await self._session.commit()

        stored_document = await self.get(document.id)
        if stored_document is None:
            raise RuntimeError(f"Document {document.id} disappeared after classification update.")
        return stored_document
