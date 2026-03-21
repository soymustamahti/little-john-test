from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.documents.classification import DocumentClassificationStatus
from src.documents.extraction import (
    DocumentExtractionMethod,
    DocumentExtractionStatus,
    ParsedDocumentExtractionCorrectionEventGroup,
    ParsedDocumentExtractionCorrectionMessage,
    build_extraction_metadata,
    parse_extraction_metadata,
)
from src.documents.extraction_repository import DocumentExtractionRepository
from src.documents.extraction_schemas import (
    DocumentExtractionCorrectionActivityUpdate,
    DocumentExtractionCorrectionEventGroupRead,
    DocumentExtractionCorrectionMessageRead,
    DocumentExtractionCorrectionSessionRead,
    DocumentExtractionRead,
    DocumentExtractionResultRead,
    DocumentExtractionReviewUpdate,
    DocumentExtractionSessionRead,
    ExtractionTemplateSummaryRead,
)
from src.documents.model import DocumentExtractionModel
from src.documents.repository import DocumentRepository
from src.extraction_templates.repository import ExtractionTemplateRepository

DOCUMENT_EXTRACTION_ASSISTANT_ID = "document_extraction_agent"
DOCUMENT_EXTRACTION_CORRECTION_ASSISTANT_ID = "document_extraction_correction_agent"
CORRECTION_MESSAGE_HISTORY_LIMIT = 24


@dataclass(frozen=True)
class ExtractionSourceChunk:
    chunk_index: int
    content: str


@dataclass(frozen=True)
class DocumentExtractionSource:
    document_id: UUID
    original_filename: str
    file_kind: str
    file_extension: str
    extracted_text: str
    template_id: UUID
    template_name: str
    template_locale: str
    template_modules: list[dict[str, object]]
    chunks: tuple[ExtractionSourceChunk, ...]


@dataclass(frozen=True)
class DocumentExtractionCorrectionSource:
    document_id: UUID
    original_filename: str
    file_kind: str
    file_extension: str
    template_id: UUID
    template_name: str
    template_locale: str
    template_modules: list[dict[str, object]]
    current_result: DocumentExtractionResultRead
    reasoning_summary: str | None
    correction_messages: tuple[ParsedDocumentExtractionCorrectionMessage, ...]


class DocumentExtractionService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def start_ai_extraction_session(
        self,
        *,
        document_id: UUID,
        template_id: UUID,
    ) -> DocumentExtractionSessionRead:
        thread_id = str(uuid4())

        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            extraction_repository = DocumentExtractionRepository(session)
            template_repository = ExtractionTemplateRepository(session)

            document = await document_repository.get_for_extraction(document_id)
            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {document_id} was not found.",
                )
            if document.classification_status != DocumentClassificationStatus.CLASSIFIED.value:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Document must be classified before extraction can start.",
                )

            template = await template_repository.get(template_id)
            if template is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction template {template_id} was not found.",
                )

            await extraction_repository.upsert_session(
                document_id=document_id,
                template_id=template.id,
                status=DocumentExtractionStatus.PROCESSING,
                method=DocumentExtractionMethod.AI,
                metadata=build_extraction_metadata(thread_id=thread_id),
            )

        return DocumentExtractionSessionRead(
            assistant_id=DOCUMENT_EXTRACTION_ASSISTANT_ID,
            thread_id=thread_id,
            document_id=document_id,
            template_id=template_id,
            status=DocumentExtractionStatus.PROCESSING,
        )

    async def get_extraction(self, document_id: UUID) -> DocumentExtractionRead:
        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )
            return build_document_extraction_read(extraction)

    async def start_correction_session(
        self,
        *,
        document_id: UUID,
    ) -> DocumentExtractionCorrectionSessionRead:
        thread_id = str(uuid4())

        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )
            if not isinstance(extraction.extraction_result, dict):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="An extraction draft must exist before correction chat can start.",
                )

            metadata = parse_extraction_metadata(extraction.extraction_metadata)
            await extraction_repository.save_result(
                extraction=extraction,
                status=DocumentExtractionStatus.PROCESSING,
                metadata=build_extraction_metadata(
                    thread_id=metadata.thread_id,
                    overall_confidence=metadata.overall_confidence,
                    reasoning_summary=metadata.reasoning_summary,
                    correction_messages=_serialize_correction_messages(
                        metadata.correction_messages
                    ),
                    correction_event_groups=_serialize_correction_event_groups(
                        metadata.correction_event_groups
                    ),
                ),
                result=extraction.extraction_result,
                extracted_at=extraction.extracted_at,
                reviewed_at=extraction.reviewed_at,
            )

        return DocumentExtractionCorrectionSessionRead(
            assistant_id=DOCUMENT_EXTRACTION_CORRECTION_ASSISTANT_ID,
            thread_id=thread_id,
            document_id=document_id,
            status=DocumentExtractionStatus.PROCESSING,
        )

    async def get_extraction_source(
        self,
        *,
        document_id: UUID,
        template_id: UUID,
    ) -> DocumentExtractionSource:
        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            template_repository = ExtractionTemplateRepository(session)

            document = await document_repository.get_for_extraction(document_id)
            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {document_id} was not found.",
                )

            template = await template_repository.get(template_id)
            if template is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction template {template_id} was not found.",
                )

            extracted_text = (document.extracted_text or "").strip()
            if not extracted_text and not document.chunks:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Document has no extracted content available for structured extraction.",
                )

            return DocumentExtractionSource(
                document_id=document.id,
                original_filename=document.original_filename,
                file_kind=document.file_kind,
                file_extension=document.file_extension,
                extracted_text=extracted_text,
                template_id=template.id,
                template_name=template.name,
                template_locale=template.locale,
                template_modules=list(template.modules),
                chunks=tuple(
                    ExtractionSourceChunk(
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                    )
                    for chunk in document.chunks
                ),
            )

    async def get_correction_source(
        self,
        *,
        document_id: UUID,
    ) -> DocumentExtractionCorrectionSource:
        async with self._session_factory() as session:
            document_repository = DocumentRepository(session)
            extraction_repository = DocumentExtractionRepository(session)

            document = await document_repository.get_for_extraction(document_id)
            if document is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {document_id} was not found.",
                )

            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )

            template = extraction.extraction_template
            if template is None:
                raise RuntimeError(
                    "Document extraction "
                    f"{document_id} is missing its linked extraction template."
                )

            if not isinstance(extraction.extraction_result, dict):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="An extraction draft must exist before correction chat can start.",
                )

            metadata = parse_extraction_metadata(extraction.extraction_metadata)

            return DocumentExtractionCorrectionSource(
                document_id=document.id,
                original_filename=document.original_filename,
                file_kind=document.file_kind,
                file_extension=document.file_extension,
                template_id=template.id,
                template_name=template.name,
                template_locale=template.locale,
                template_modules=list(template.modules),
                current_result=DocumentExtractionResultRead.model_validate(
                    extraction.extraction_result
                ),
                reasoning_summary=metadata.reasoning_summary,
                correction_messages=metadata.correction_messages,
            )

    async def save_ai_draft(
        self,
        *,
        document_id: UUID,
        template_id: UUID,
        thread_id: str,
        result: DocumentExtractionResultRead,
        reasoning_summary: str | None,
    ) -> None:
        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )
            if extraction.extraction_template_id != template_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "The extraction template no longer matches the active extraction session."
                    ),
                )

            overall_confidence = compute_overall_confidence(result)
            existing_metadata = parse_extraction_metadata(extraction.extraction_metadata)
            await extraction_repository.save_result(
                extraction=extraction,
                status=DocumentExtractionStatus.PENDING_REVIEW,
                metadata=build_extraction_metadata(
                    thread_id=thread_id,
                    overall_confidence=overall_confidence,
                    reasoning_summary=reasoning_summary,
                    correction_messages=_serialize_correction_messages(
                        existing_metadata.correction_messages
                    ),
                    correction_event_groups=_serialize_correction_event_groups(
                        existing_metadata.correction_event_groups
                    ),
                ),
                result=result.model_dump(mode="json"),
                extracted_at=datetime.now(UTC),
                reviewed_at=None,
            )

    async def confirm_review(
        self,
        *,
        document_id: UUID,
        payload: DocumentExtractionReviewUpdate,
    ) -> DocumentExtractionRead:
        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )

            existing_metadata = parse_extraction_metadata(extraction.extraction_metadata)
            overall_confidence = compute_overall_confidence(payload.result)
            updated_extraction = await extraction_repository.save_result(
                extraction=extraction,
                status=DocumentExtractionStatus.CONFIRMED,
                metadata=build_extraction_metadata(
                    thread_id=existing_metadata.thread_id,
                    overall_confidence=overall_confidence,
                    reasoning_summary=existing_metadata.reasoning_summary,
                    correction_messages=_serialize_correction_messages(
                        existing_metadata.correction_messages
                    ),
                    correction_event_groups=_serialize_correction_event_groups(
                        existing_metadata.correction_event_groups
                    ),
                ),
                result=payload.result.model_dump(mode="json"),
                extracted_at=extraction.extracted_at,
                reviewed_at=datetime.now(UTC),
            )

        return build_document_extraction_read(updated_extraction)

    async def mark_ai_failure(
        self,
        *,
        document_id: UUID,
        thread_id: str,
        error_message: str,
    ) -> None:
        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )

            existing_metadata = parse_extraction_metadata(extraction.extraction_metadata)
            await extraction_repository.save_result(
                extraction=extraction,
                status=DocumentExtractionStatus.FAILED,
                metadata=build_extraction_metadata(
                    thread_id=thread_id,
                    error=error_message,
                    correction_messages=_serialize_correction_messages(
                        existing_metadata.correction_messages
                    ),
                    correction_event_groups=_serialize_correction_event_groups(
                        existing_metadata.correction_event_groups
                    ),
                ),
                result=None,
                extracted_at=None,
                reviewed_at=None,
            )

    async def save_chat_correction(
        self,
        *,
        document_id: UUID,
        user_message: str,
        assistant_response: str,
        result: DocumentExtractionResultRead,
        reasoning_summary: str | None,
    ) -> None:
        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )

            existing_metadata = parse_extraction_metadata(extraction.extraction_metadata)
            overall_confidence = compute_overall_confidence(result)
            correction_messages = _append_correction_messages(
                existing_metadata.correction_messages,
                (
                    _build_correction_message("user", user_message),
                    _build_correction_message("assistant", assistant_response),
                ),
            )

            await extraction_repository.save_result(
                extraction=extraction,
                status=DocumentExtractionStatus.PENDING_REVIEW,
                metadata=build_extraction_metadata(
                    thread_id=existing_metadata.thread_id,
                    overall_confidence=overall_confidence,
                    reasoning_summary=reasoning_summary
                    or existing_metadata.reasoning_summary
                    or "Extraction draft updated from correction chat.",
                    correction_messages=correction_messages,
                    correction_event_groups=_serialize_correction_event_groups(
                        existing_metadata.correction_event_groups
                    ),
                ),
                result=result.model_dump(mode="json"),
                extracted_at=datetime.now(UTC),
                reviewed_at=None,
            )

    async def mark_correction_failure(
        self,
        *,
        document_id: UUID,
        user_message: str,
        error_message: str,
    ) -> None:
        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )

            existing_metadata = parse_extraction_metadata(extraction.extraction_metadata)
            correction_messages = _append_correction_messages(
                existing_metadata.correction_messages,
                (
                    _build_correction_message("user", user_message),
                    _build_correction_message(
                        "assistant",
                        f"I could not apply the requested correction: {error_message}",
                    ),
                ),
            )

            await extraction_repository.save_result(
                extraction=extraction,
                status=DocumentExtractionStatus.FAILED,
                metadata=build_extraction_metadata(
                    thread_id=existing_metadata.thread_id,
                    overall_confidence=existing_metadata.overall_confidence,
                    reasoning_summary=existing_metadata.reasoning_summary,
                    error=error_message,
                    correction_messages=correction_messages,
                    correction_event_groups=_serialize_correction_event_groups(
                        existing_metadata.correction_event_groups
                    ),
                ),
                result=extraction.extraction_result,
                extracted_at=extraction.extracted_at,
                reviewed_at=extraction.reviewed_at,
            )

    async def save_correction_activity(
        self,
        *,
        document_id: UUID,
        payload: DocumentExtractionCorrectionActivityUpdate,
    ) -> DocumentExtractionRead:
        async with self._session_factory() as session:
            extraction_repository = DocumentExtractionRepository(session)
            extraction = await extraction_repository.get(document_id)
            if extraction is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Extraction for document {document_id} was not found.",
                )

            existing_metadata = parse_extraction_metadata(extraction.extraction_metadata)
            updated_extraction = await extraction_repository.save_result(
                extraction=extraction,
                status=DocumentExtractionStatus(extraction.status),
                metadata=build_extraction_metadata(
                    thread_id=existing_metadata.thread_id,
                    overall_confidence=existing_metadata.overall_confidence,
                    reasoning_summary=existing_metadata.reasoning_summary,
                    error=existing_metadata.error,
                    correction_messages=_serialize_correction_messages(
                        existing_metadata.correction_messages
                    ),
                    correction_event_groups=payload.model_dump(mode="json")["groups"],
                ),
                result=extraction.extraction_result,
                extracted_at=extraction.extracted_at,
                reviewed_at=extraction.reviewed_at,
            )

        return build_document_extraction_read(updated_extraction)


def build_document_extraction_read(extraction: DocumentExtractionModel) -> DocumentExtractionRead:
    metadata = parse_extraction_metadata(extraction.extraction_metadata)
    template = extraction.extraction_template
    if template is None:
        raise RuntimeError(
            "Document extraction "
            f"{extraction.document_id} is missing its linked extraction template."
        )

    result_payload = None
    if isinstance(extraction.extraction_result, dict):
        result_payload = DocumentExtractionResultRead.model_validate(extraction.extraction_result)

    return DocumentExtractionRead.model_validate(
        {
            "document_id": extraction.document_id,
            "status": extraction.status,
            "method": extraction.method,
            "template": ExtractionTemplateSummaryRead(
                id=template.id,
                name=template.name,
                locale=template.locale,
            ),
            "thread_id": metadata.thread_id,
            "overall_confidence": metadata.overall_confidence,
            "reasoning_summary": metadata.reasoning_summary,
            "error": metadata.error,
            "correction_messages": [
                DocumentExtractionCorrectionMessageRead(
                    role=item.role,
                    content=item.content,
                    created_at=item.created_at or extraction.updated_at,
                )
                for item in metadata.correction_messages
            ],
            "correction_event_groups": [
                DocumentExtractionCorrectionEventGroupRead.model_validate(
                    {
                        "id": group.id,
                        "user_turn_index": group.user_turn_index,
                        "summary": group.summary,
                        "status": group.status,
                        "expanded": group.expanded,
                        "items": [
                            {
                                "id": item.id,
                                "kind": item.kind,
                                "summary": item.summary,
                                "occurred_at": item.occurred_at,
                            }
                            for item in group.items
                        ],
                    }
                )
                for group in metadata.correction_event_groups
            ],
            "result": result_payload,
            "extracted_at": extraction.extracted_at,
            "reviewed_at": extraction.reviewed_at,
            "created_at": extraction.created_at,
            "updated_at": extraction.updated_at,
        }
    )


def compute_overall_confidence(result: DocumentExtractionResultRead) -> float | None:
    confidences: list[float] = []
    for module in result.modules:
        for field in module.fields:
            if field.kind == "scalar":
                confidences.append(field.confidence)
            else:
                for row in field.rows:
                    confidences.append(row.confidence)
                    for cell in row.cells:
                        confidences.append(cell.confidence)

    if not confidences:
        return None

    return sum(confidences) / len(confidences)


def _build_correction_message(
    role: str,
    content: str,
) -> dict[str, str]:
    return {
        "role": role,
        "content": content.strip(),
        "created_at": datetime.now(UTC).isoformat(),
    }


def _append_correction_messages(
    existing_messages: Sequence[ParsedDocumentExtractionCorrectionMessage],
    new_messages: Sequence[dict[str, str]],
) -> list[dict[str, str]]:
    combined = [
        *_serialize_correction_messages(existing_messages),
        *[message for message in new_messages if message.get("content")],
    ]
    return combined[-CORRECTION_MESSAGE_HISTORY_LIMIT:]


def _serialize_correction_messages(
    messages: Sequence[ParsedDocumentExtractionCorrectionMessage],
) -> list[dict[str, str]]:
    serialized: list[dict[str, str]] = []
    for message in messages:
        created_at = (
            message.created_at.isoformat()
            if message.created_at is not None
            else datetime.now(UTC).isoformat()
        )
        serialized.append(
            {
                "role": message.role,
                "content": message.content,
                "created_at": created_at,
            }
        )
    return serialized[-CORRECTION_MESSAGE_HISTORY_LIMIT:]


def _serialize_correction_event_groups(
    groups: Sequence[ParsedDocumentExtractionCorrectionEventGroup],
) -> list[dict[str, object]]:
    serialized: list[dict[str, object]] = []
    for group in groups:
        serialized.append(
            {
                "id": group.id,
                "user_turn_index": group.user_turn_index,
                "summary": group.summary,
                "status": group.status,
                "expanded": group.expanded,
                "items": [
                    {
                        "id": item.id,
                        "kind": item.kind,
                        "summary": item.summary,
                        "occurred_at": item.occurred_at,
                    }
                    for item in group.items
                ],
            }
        )
    return serialized
