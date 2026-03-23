from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.documents.extraction import DocumentExtractionMethod, DocumentExtractionStatus
from src.documents.model import DocumentExtractionModel


class DocumentExtractionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, document_id: UUID) -> DocumentExtractionModel | None:
        result = await self._session.execute(
            select(DocumentExtractionModel)
            .options(selectinload(DocumentExtractionModel.extraction_template))
            .where(DocumentExtractionModel.document_id == document_id)
        )
        return result.scalar_one_or_none()

    async def upsert_session(
        self,
        *,
        document_id: UUID,
        template_id: UUID,
        status: DocumentExtractionStatus,
        method: DocumentExtractionMethod,
        metadata: dict | None,
    ) -> DocumentExtractionModel:
        extraction = await self.get(document_id)
        if extraction is None:
            extraction = DocumentExtractionModel(
                document_id=document_id,
                extraction_template_id=template_id,
                status=status.value,
                method=method.value,
                extraction_metadata=metadata,
                extraction_result=None,
                extracted_at=None,
                reviewed_at=None,
            )
            self._session.add(extraction)
        else:
            extraction.extraction_template_id = template_id
            extraction.status = status.value
            extraction.method = method.value
            extraction.extraction_metadata = metadata
            extraction.extraction_result = None
            extraction.extracted_at = None
            extraction.reviewed_at = None

        await self._session.commit()
        stored = await self.get(document_id)
        if stored is None:
            raise RuntimeError(f"Extraction for document {document_id} was not persisted.")
        return stored

    async def save_result(
        self,
        *,
        extraction: DocumentExtractionModel,
        status: DocumentExtractionStatus,
        metadata: dict | None,
        result: dict | None,
        extracted_at: datetime | None,
        reviewed_at: datetime | None,
    ) -> DocumentExtractionModel:
        extraction.status = status.value
        extraction.extraction_metadata = metadata
        extraction.extraction_result = result
        extraction.extracted_at = extracted_at
        extraction.reviewed_at = reviewed_at

        await self._session.commit()
        stored = await self.get(extraction.document_id)
        if stored is None:
            raise RuntimeError(
                f"Extraction for document {extraction.document_id} disappeared after update."
            )
        return stored
