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
    correction_event_groups: tuple[
        "ParsedDocumentExtractionCorrectionEventGroup", ...
    ] = ()


@dataclass(frozen=True)
class ParsedDocumentExtractionCorrectionMessage:
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class ParsedDocumentExtractionCorrectionEventItem:
    id: str
    kind: Literal["progress", "error", "end", "change"]
    summary: str
    occurred_at: float | None = None


@dataclass(frozen=True)
class ParsedDocumentExtractionCorrectionEventGroup:
    id: str
    user_turn_index: int
    summary: str
    status: Literal["running", "complete", "error"]
    expanded: bool = False
    items: tuple[ParsedDocumentExtractionCorrectionEventItem, ...] = ()


def build_extraction_metadata(
    *,
    thread_id: str | None = None,
    overall_confidence: float | None = None,
    reasoning_summary: str | None = None,
    error: str | None = None,
    correction_messages: list[dict[str, Any]] | None = None,
    correction_event_groups: list[dict[str, Any]] | None = None,
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
    if correction_event_groups:
        metadata["correction_event_groups"] = correction_event_groups

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

    correction_event_groups_raw = metadata.get("correction_event_groups")
    correction_event_groups: list[ParsedDocumentExtractionCorrectionEventGroup] = []
    if isinstance(correction_event_groups_raw, list):
        for group_item in correction_event_groups_raw:
            if not isinstance(group_item, dict):
                continue

            group_id_raw = group_item.get("id")
            group_id = group_id_raw.strip() if isinstance(group_id_raw, str) else ""
            if group_id == "":
                continue

            user_turn_index_raw = group_item.get("user_turn_index")
            if not isinstance(user_turn_index_raw, int) or user_turn_index_raw < 0:
                continue

            summary_raw = group_item.get("summary")
            summary = summary_raw.strip() if isinstance(summary_raw, str) else ""
            if summary == "":
                continue

            status_raw = group_item.get("status")
            if status_raw not in {"running", "complete", "error"}:
                continue

            expanded_raw = group_item.get("expanded")
            expanded = expanded_raw if isinstance(expanded_raw, bool) else False

            parsed_items: list[ParsedDocumentExtractionCorrectionEventItem] = []
            items_raw = group_item.get("items")
            if isinstance(items_raw, list):
                for item in items_raw:
                    if not isinstance(item, dict):
                        continue

                    item_id_raw = item.get("id")
                    item_id = item_id_raw.strip() if isinstance(item_id_raw, str) else ""
                    if item_id == "":
                        continue

                    item_kind_raw = item.get("kind")
                    if item_kind_raw not in {"progress", "error", "end", "change"}:
                        continue

                    item_summary_raw = item.get("summary")
                    item_summary = (
                        item_summary_raw.strip()
                        if isinstance(item_summary_raw, str)
                        else ""
                    )
                    if item_summary == "":
                        continue

                    occurred_at = None
                    occurred_at_raw = item.get("occurred_at")
                    if isinstance(occurred_at_raw, int | float):
                        candidate = float(occurred_at_raw)
                        if candidate >= 0:
                            occurred_at = candidate

                    parsed_items.append(
                        ParsedDocumentExtractionCorrectionEventItem(
                            id=item_id,
                            kind=item_kind_raw,
                            summary=item_summary,
                            occurred_at=occurred_at,
                        )
                    )

            correction_event_groups.append(
                ParsedDocumentExtractionCorrectionEventGroup(
                    id=group_id,
                    user_turn_index=user_turn_index_raw,
                    summary=summary,
                    status=status_raw,
                    expanded=expanded,
                    items=tuple(parsed_items),
                )
            )

    return ParsedDocumentExtractionMetadata(
        thread_id=thread_id,
        overall_confidence=overall_confidence,
        reasoning_summary=reasoning_summary,
        error=error,
        correction_messages=tuple(correction_messages),
        correction_event_groups=tuple(correction_event_groups),
    )
