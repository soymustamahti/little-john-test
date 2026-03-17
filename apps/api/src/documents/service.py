import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from src.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from src.documents.processing import DocumentProcessingError, DocumentProcessingService
from src.documents.repository import DocumentRepository
from src.documents.schemas import (
    DocumentChunkCreateRecord,
    DocumentCreateRecord,
    DocumentRead,
    build_document_read,
)
from src.documents.validation import (
    DocumentValidationError,
    build_storage_key,
    validate_uploaded_document,
)
from src.storage.object_store import ObjectStorage, ObjectStorageError, RetrievedObject


@dataclass(frozen=True)
class UploadedDocumentInput:
    filename: str
    content_type: str | None
    content: bytes


@dataclass(frozen=True)
class DocumentContentRead:
    content: bytes
    content_type: str
    original_filename: str


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        object_storage: ObjectStorage,
        processing_service: DocumentProcessingService,
        *,
        max_upload_size_bytes: int,
    ) -> None:
        self._repository = repository
        self._object_storage = object_storage
        self._processing_service = processing_service
        self._max_upload_size_bytes = max_upload_size_bytes

    @property
    def max_upload_size_bytes(self) -> int:
        return self._max_upload_size_bytes

    async def list_documents(
        self,
        pagination: PaginationParams,
    ) -> PaginatedResponse[DocumentRead]:
        result = await self._repository.list(pagination)
        items = [build_document_read(document) for document in result.items]
        return build_paginated_response(
            items=items,
            pagination=pagination,
            total_items=result.total_items,
        )

    async def get_document(self, document_id: UUID) -> DocumentRead:
        document = await self._repository.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} was not found.",
            )
        return build_document_read(document)

    async def upload_document(self, upload: UploadedDocumentInput) -> DocumentRead:
        try:
            validated = await asyncio.to_thread(
                validate_uploaded_document,
                filename=upload.filename,
                content_type=upload.content_type,
                content=upload.content,
                max_size_bytes=self._max_upload_size_bytes,
            )
        except DocumentValidationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        document_id = uuid4()
        storage_key = build_storage_key(
            document_id=document_id,
            sanitized_stem=validated.sanitized_stem,
            file_extension=validated.file_extension,
        )

        try:
            processed = await self._processing_service.process_document(
                filename=validated.original_filename,
                file_extension=validated.file_extension,
                content_type=validated.content_type,
                content=validated.content,
            )
        except DocumentProcessingError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        try:
            stored_object = await self._object_storage.upload_object(
                key=storage_key,
                content=validated.content,
                content_type=validated.content_type,
                metadata={
                    "document-id": str(document_id),
                    "sha256": validated.sha256,
                },
            )
        except ObjectStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        try:
            document = await self._repository.create(
                DocumentCreateRecord(
                    id=document_id,
                    original_filename=validated.original_filename,
                    content_type=validated.content_type,
                    file_extension=validated.file_extension,
                    file_kind=validated.file_kind,
                    size_bytes=validated.size_bytes,
                    sha256=validated.sha256,
                    storage_provider=stored_object.provider,
                    storage_bucket=stored_object.bucket,
                    storage_key=stored_object.key,
                    public_url=stored_object.public_url,
                    content_source=processed.content_source,
                    extracted_text=processed.text,
                    extraction_metadata=processed.metadata,
                    processed_at=datetime.now(UTC),
                ),
                chunks=[
                    DocumentChunkCreateRecord(
                        document_id=document_id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        content_start_offset=chunk.content_start_offset,
                        content_end_offset=chunk.content_end_offset,
                        embedding_provider=processed.metadata["embedding_provider"],
                        embedding_model=processed.metadata["embedding_model"],
                        embedding_dimensions=len(chunk.embedding),
                        embedding=chunk.embedding,
                    )
                    for chunk in processed.chunks
                ],
            )
        except Exception:
            try:
                await self._object_storage.delete_object(key=stored_object.key)
            except ObjectStorageError:
                logging.exception(
                    "Failed to clean up R2 object '%s' after repository failure.",
                    stored_object.key,
                )
            raise

        return build_document_read(document)

    async def delete_document(self, document_id: UUID) -> None:
        document = await self._repository.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} was not found.",
            )

        try:
            await self._object_storage.delete_object(key=document.storage_key)
        except ObjectStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        await self._repository.delete(document)

    async def get_document_content(self, document_id: UUID) -> DocumentContentRead:
        document = await self._repository.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} was not found.",
            )

        try:
            stored_object: RetrievedObject = await self._object_storage.download_object(
                key=document.storage_key
            )
        except ObjectStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        return DocumentContentRead(
            content=stored_object.content,
            content_type=stored_object.content_type or document.content_type,
            original_filename=document.original_filename,
        )
