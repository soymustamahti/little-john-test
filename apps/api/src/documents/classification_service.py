from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.document_categories.repository import DocumentCategoryRepository
from src.document_categories.schemas import DocumentCategoryCreate
from src.documents.classification import (
    DocumentClassificationMethod,
    DocumentClassificationStatus,
    SuggestedDocumentCategory,
    build_classification_metadata,
    normalize_document_category_name,
    slugify_document_category_label_key,
)
from src.documents.model import DocumentModel
from src.documents.repository import DocumentRepository
from src.documents.schemas import (
    DocumentClassificationSessionRead,
    DocumentRead,
    build_document_read,
)

DOCUMENT_CLASSIFICATION_ASSISTANT_ID = "document_classification_agent"


def _normalize_suggested_category(
    suggested_category: SuggestedDocumentCategory,
) -> SuggestedDocumentCategory:
    normalized_name = (
        normalize_document_category_name(suggested_category.name) or suggested_category.name.strip()
    )
    normalized_label_key = slugify_document_category_label_key(
        suggested_category.label_key or normalized_name
    )
    return SuggestedDocumentCategory(
        name=normalized_name,
        label_key=normalized_label_key,
    )


def get_document_classification_service(
    session_factory: async_sessionmaker[AsyncSession],
) -> DocumentClassificationService:
    return DocumentClassificationService(session_factory)


@dataclass(frozen=True)
class ClassificationSourceChunk:
    chunk_index: int
    content: str


@dataclass(frozen=True)
class ClassificationCategoryOption:
    id: UUID
    name: str
    label_key: str


@dataclass(frozen=True)
class DocumentClassificationSource:
    document_id: UUID
    original_filename: str
    extracted_text: str
    chunks: tuple[ClassificationSourceChunk, ...]
    categories: tuple[ClassificationCategoryOption, ...]


class DocumentClassificationService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def start_ai_classification_session(
        self,
        document_id: UUID,
    ) -> DocumentClassificationSessionRead:
        thread_id = str(uuid4())

        async with self._session_factory() as session:
            repository = DocumentRepository(session)
            document = await self._get_document_or_404(repository, document_id)
            await repository.update_classification(
                document,
                document_category_id=None,
                classification_status=DocumentClassificationStatus.PROCESSING,
                classification_method=DocumentClassificationMethod.AI,
                classification_metadata=build_classification_metadata(thread_id=thread_id),
                classified_at=None,
            )

        return DocumentClassificationSessionRead(
            assistant_id=DOCUMENT_CLASSIFICATION_ASSISTANT_ID,
            thread_id=thread_id,
            document_id=document_id,
            status=DocumentClassificationStatus.PROCESSING,
        )

    async def apply_manual_classification(
        self,
        document_id: UUID,
        category_id: UUID,
    ) -> DocumentRead:
        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            category_repository = DocumentCategoryRepository(session)
            document = await self._get_document_or_404(document_repository, document_id)
            category = await category_repository.get(category_id)

            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document category {category_id} was not found.",
                )

            updated_document = await document_repository.update_classification(
                document,
                document_category_id=category.id,
                classification_status=DocumentClassificationStatus.CLASSIFIED,
                classification_method=DocumentClassificationMethod.MANUAL,
                classification_metadata=None,
                classified_at=datetime.now(UTC),
            )

        return build_document_read(updated_document)

    async def get_classification_source(self, document_id: UUID) -> DocumentClassificationSource:
        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            category_repository = DocumentCategoryRepository(session)
            document = await self._get_document_for_classification_or_404(
                document_repository,
                document_id,
            )
            categories = await category_repository.list_all()

            extracted_text = (document.extracted_text or "").strip()
            if not extracted_text and not document.chunks:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Document has no extracted content available for classification.",
                )

            return DocumentClassificationSource(
                document_id=document.id,
                original_filename=document.original_filename,
                extracted_text=extracted_text,
                chunks=tuple(
                    ClassificationSourceChunk(
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                    )
                    for chunk in document.chunks
                ),
                categories=tuple(
                    ClassificationCategoryOption(
                        id=category.id,
                        name=category.name,
                        label_key=category.label_key,
                    )
                    for category in categories
                ),
            )

    async def record_ai_category_match(
        self,
        *,
        document_id: UUID,
        thread_id: str,
        category_id: UUID,
        confidence: float,
        rationale: str,
        sampled_chunk_indices: Sequence[int],
        excerpt_character_count: int,
    ) -> None:
        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            category_repository = DocumentCategoryRepository(session)
            document = await self._get_document_or_404(document_repository, document_id)
            category = await category_repository.get(category_id)

            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document category {category_id} was not found.",
                )

            await document_repository.update_classification(
                document,
                document_category_id=category.id,
                classification_status=DocumentClassificationStatus.CLASSIFIED,
                classification_method=DocumentClassificationMethod.AI,
                classification_metadata=build_classification_metadata(
                    thread_id=thread_id,
                    confidence=confidence,
                    rationale=rationale,
                    sampled_chunk_indices=sampled_chunk_indices,
                    excerpt_character_count=excerpt_character_count,
                ),
                classified_at=datetime.now(UTC),
            )

    async def record_ai_suggestion(
        self,
        *,
        document_id: UUID,
        thread_id: str,
        suggested_category: SuggestedDocumentCategory,
        confidence: float,
        rationale: str,
        sampled_chunk_indices: Sequence[int],
        excerpt_character_count: int,
    ) -> None:
        normalized_suggested_category = _normalize_suggested_category(suggested_category)

        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            document = await self._get_document_or_404(document_repository, document_id)

            await document_repository.update_classification(
                document,
                document_category_id=None,
                classification_status=DocumentClassificationStatus.PENDING_REVIEW,
                classification_method=DocumentClassificationMethod.AI,
                classification_metadata=build_classification_metadata(
                    thread_id=thread_id,
                    confidence=confidence,
                    rationale=rationale,
                    suggested_category=normalized_suggested_category,
                    sampled_chunk_indices=sampled_chunk_indices,
                    excerpt_character_count=excerpt_character_count,
                ),
                classified_at=None,
            )

    async def accept_ai_suggested_category(
        self,
        *,
        document_id: UUID,
        thread_id: str,
        suggested_category: SuggestedDocumentCategory,
        confidence: float,
        rationale: str,
        sampled_chunk_indices: Sequence[int],
        excerpt_character_count: int,
    ) -> None:
        normalized_suggested_category = _normalize_suggested_category(suggested_category)

        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            category_repository = DocumentCategoryRepository(session)
            document = await self._get_document_or_404(document_repository, document_id)

            normalized_name = normalized_suggested_category.name
            normalized_label_key = normalized_suggested_category.label_key

            category = await category_repository.get_by_label_key(normalized_label_key)
            if category is None:
                category = await category_repository.get_by_name(normalized_name)
            if category is None:
                category = await category_repository.create(
                    DocumentCategoryCreate(
                        name=normalized_name,
                        label_key=normalized_label_key,
                    )
                )

            await document_repository.update_classification(
                document,
                document_category_id=category.id,
                classification_status=DocumentClassificationStatus.CLASSIFIED,
                classification_method=DocumentClassificationMethod.AI,
                classification_metadata=build_classification_metadata(
                    thread_id=thread_id,
                    confidence=confidence,
                    rationale=rationale,
                    suggested_category=normalized_suggested_category,
                    sampled_chunk_indices=sampled_chunk_indices,
                    excerpt_character_count=excerpt_character_count,
                ),
                classified_at=datetime.now(UTC),
            )

    async def mark_ai_failure(
        self,
        *,
        document_id: UUID,
        thread_id: str,
        error_message: str,
    ) -> None:
        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            document = await self._get_document_or_404(document_repository, document_id)

            await document_repository.update_classification(
                document,
                document_category_id=None,
                classification_status=DocumentClassificationStatus.FAILED,
                classification_method=DocumentClassificationMethod.AI,
                classification_metadata=build_classification_metadata(
                    thread_id=thread_id,
                    error=error_message,
                ),
                classified_at=None,
            )

    async def _get_document_or_404(
        self,
        repository: DocumentRepository,
        document_id: UUID,
    ) -> DocumentModel:
        document = await repository.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} was not found.",
            )
        return document

    async def _get_document_for_classification_or_404(
        self,
        repository: DocumentRepository,
        document_id: UUID,
    ) -> DocumentModel:
        document = await repository.get_for_classification(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} was not found.",
            )
        return document
