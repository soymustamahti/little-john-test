from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class DocumentExtractionStatus(str, Enum):
    NOT_STARTED = "not_started"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class DocumentExtractionMethod(str, Enum):
    AI = "ai"


class ExtractionValueMode(str, Enum):
    DIRECT = "direct"
    INFERRED = "inferred"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class ParsedDocumentExtractionMetadata:
    thread_id: str | None = None
    overall_confidence: float | None = None
    reasoning_summary: str | None = None
    error: str | None = None
    correction_messages: tuple["ParsedDocumentExtractionCorrectionMessage", ...] = ()


@dataclass(frozen=True)
class ParsedDocumentExtractionCorrectionMessage:
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime | None = None


def build_extraction_metadata(
    *,
    thread_id: str | None = None,
    overall_confidence: float | None = None,
    reasoning_summary: str | None = None,
    error: str | None = None,
    correction_messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    if thread_id:
        metadata["thread_id"] = thread_id
    if overall_confidence is not None:
        metadata["overall_confidence"] = overall_confidence
    if reasoning_summary:
        metadata["reasoning_summary"] = reasoning_summary
    if error:
        metadata["error"] = error
    if correction_messages:
        metadata["correction_messages"] = correction_messages

    return metadata


def parse_extraction_metadata(
    metadata: dict[str, Any] | None,
) -> ParsedDocumentExtractionMetadata:
    if not isinstance(metadata, dict):
        return ParsedDocumentExtractionMetadata()

    thread_id_raw = metadata.get("thread_id")
    thread_id = thread_id_raw.strip() if isinstance(thread_id_raw, str) else None
    if thread_id == "":
        thread_id = None

    overall_confidence_raw = metadata.get("overall_confidence")
    overall_confidence = None
    if isinstance(overall_confidence_raw, int | float):
        candidate = float(overall_confidence_raw)
        if 0 <= candidate <= 1:
            overall_confidence = candidate

    reasoning_summary_raw = metadata.get("reasoning_summary")
    reasoning_summary = (
        reasoning_summary_raw.strip()
        if isinstance(reasoning_summary_raw, str)
        else None
    )
    if reasoning_summary == "":
        reasoning_summary = None

    error_raw = metadata.get("error")
    error = error_raw.strip() if isinstance(error_raw, str) else None
    if error == "":
        error = None

    correction_messages_raw = metadata.get("correction_messages")
    correction_messages: list[ParsedDocumentExtractionCorrectionMessage] = []
    if isinstance(correction_messages_raw, list):
        for item in correction_messages_raw:
            if not isinstance(item, dict):
                continue

            role_raw = item.get("role")
            if role_raw not in {"user", "assistant"}:
                continue

            content_raw = item.get("content")
            content = content_raw.strip() if isinstance(content_raw, str) else ""
            if content == "":
                continue

            created_at = None
            created_at_raw = item.get("created_at")
            if isinstance(created_at_raw, str):
                try:
                    created_at = datetime.fromisoformat(created_at_raw)
                except ValueError:
                    created_at = None

            correction_messages.append(
                ParsedDocumentExtractionCorrectionMessage(
                    role=role_raw,
                    content=content,
                    created_at=created_at,
                )
            )

    return ParsedDocumentExtractionMetadata(
        thread_id=thread_id,
        overall_confidence=overall_confidence,
        reasoning_summary=reasoning_summary,
        error=error,
        correction_messages=tuple(correction_messages),
    )
