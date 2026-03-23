from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

SLUG_LIKE_DOCUMENT_CATEGORY_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[ _-][a-z0-9]+)+$")


class DocumentClassificationStatus(str, Enum):
    UNCLASSIFIED = "unclassified"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    CLASSIFIED = "classified"
    FAILED = "failed"


class DocumentClassificationMethod(str, Enum):
    MANUAL = "manual"
    AI = "ai"


@dataclass(frozen=True)
class SuggestedDocumentCategory:
    name: str
    label_key: str


@dataclass(frozen=True)
class ParsedClassificationMetadata:
    thread_id: str | None = None
    confidence: float | None = None
    rationale: str | None = None
    suggested_category: SuggestedDocumentCategory | None = None
    sampled_chunk_indices: tuple[int, ...] = ()
    excerpt_character_count: int | None = None
    error: str | None = None


def slugify_document_category_label_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = normalized.strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized


def normalize_document_category_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip())
    if not normalized:
        return ""

    if not SLUG_LIKE_DOCUMENT_CATEGORY_NAME_PATTERN.fullmatch(normalized):
        return normalized

    return " ".join(part.capitalize() for part in re.split(r"[ _-]+", normalized) if part)


def build_classification_metadata(
    *,
    thread_id: str | None = None,
    confidence: float | None = None,
    rationale: str | None = None,
    suggested_category: SuggestedDocumentCategory | None = None,
    sampled_chunk_indices: Sequence[int] = (),
    excerpt_character_count: int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    if thread_id:
        metadata["thread_id"] = thread_id
    if confidence is not None:
        metadata["confidence"] = confidence
    if rationale:
        metadata["rationale"] = rationale
    if suggested_category is not None:
        metadata["suggested_category"] = {
            "name": suggested_category.name,
            "label_key": suggested_category.label_key,
        }
    if sampled_chunk_indices:
        metadata["sampled_chunk_indices"] = list(sampled_chunk_indices)
    if excerpt_character_count is not None:
        metadata["excerpt_character_count"] = excerpt_character_count
    if error:
        metadata["error"] = error

    return metadata


def parse_classification_metadata(metadata: dict[str, Any] | None) -> ParsedClassificationMetadata:
    if not isinstance(metadata, dict):
        return ParsedClassificationMetadata()

    thread_id = metadata.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        thread_id = None

    confidence_raw = metadata.get("confidence")
    confidence = None
    if isinstance(confidence_raw, int | float):
        candidate = float(confidence_raw)
        if 0 <= candidate <= 1:
            confidence = candidate

    rationale = metadata.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        rationale = None

    suggested_category_raw = metadata.get("suggested_category")
    suggested_category = None
    if isinstance(suggested_category_raw, dict):
        suggested_name = suggested_category_raw.get("name")
        suggested_label_key = suggested_category_raw.get("label_key")
        if (
            isinstance(suggested_name, str)
            and suggested_name.strip()
            and isinstance(suggested_label_key, str)
            and suggested_label_key.strip()
        ):
            suggested_category = SuggestedDocumentCategory(
                name=suggested_name.strip(),
                label_key=suggested_label_key.strip(),
            )

    sampled_chunk_indices: tuple[int, ...] = ()
    sampled_chunk_indices_raw = metadata.get("sampled_chunk_indices")
    if isinstance(sampled_chunk_indices_raw, list):
        sampled_chunk_indices = tuple(
            item for item in sampled_chunk_indices_raw if isinstance(item, int) and item >= 0
        )

    excerpt_character_count_raw = metadata.get("excerpt_character_count")
    excerpt_character_count = None
    if isinstance(excerpt_character_count_raw, int) and excerpt_character_count_raw >= 0:
        excerpt_character_count = excerpt_character_count_raw

    error = metadata.get("error")
    if not isinstance(error, str) or not error.strip():
        error = None

    return ParsedClassificationMetadata(
        thread_id=thread_id,
        confidence=confidence,
        rationale=rationale,
        suggested_category=suggested_category,
        sampled_chunk_indices=sampled_chunk_indices,
        excerpt_character_count=excerpt_character_count,
        error=error,
    )
