import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from src.documents.repository import DocumentRepository
from src.documents.schemas import DocumentCreateRecord, DocumentRead
from src.documents.validation import (
    DocumentValidationError,
    build_storage_key,
    validate_uploaded_document,
)
from src.storage.object_store import ObjectStorage, ObjectStorageError


@dataclass(frozen=True)
class UploadedDocumentInput:
    filename: str
    content_type: str | None
    content: bytes


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        object_storage: ObjectStorage,
        *,
        max_upload_size_bytes: int,
    ) -> None:
        self._repository = repository
        self._object_storage = object_storage
        self._max_upload_size_bytes = max_upload_size_bytes

    @property
    def max_upload_size_bytes(self) -> int:
        return self._max_upload_size_bytes

    async def list_documents(self) -> list[DocumentRead]:
        documents = await self._repository.list()
        return [DocumentRead.model_validate(document) for document in documents]

    async def get_document(self, document_id: UUID) -> DocumentRead:
        document = await self._repository.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} was not found.",
            )
        return DocumentRead.model_validate(document)

    async def upload_document(self, upload: UploadedDocumentInput) -> DocumentRead:
        try:
            validated = validate_uploaded_document(
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
                )
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

        return DocumentRead.model_validate(document)

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
