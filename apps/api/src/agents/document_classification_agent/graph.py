from __future__ import annotations

from functools import lru_cache
from typing import Literal
from uuid import UUID

from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from src.agents.document_classification_agent.prompts import SYSTEM_PROMPT, build_user_prompt
from src.agents.document_classification_agent.schemas import DocumentClassificationDecision
from src.agents.document_classification_agent.state import InputState, State
from src.agents.document_classification_agent.utils import (
    build_classification_excerpt,
    load_classification_model,
)
from src.core.config import Settings, get_settings
from src.core.database import get_async_session_factory
from src.documents.classification import (
    SuggestedDocumentCategory,
    normalize_document_category_name,
    slugify_document_category_label_key,
)
from src.documents.classification_service import (
    DocumentClassificationService,
    get_document_classification_service,
)


@lru_cache
def _get_document_classification_service() -> DocumentClassificationService:
    return get_document_classification_service(get_async_session_factory())


@lru_cache
def _get_settings() -> Settings:
    return get_settings()


async def load_document_context(state: State) -> dict[str, object]:
    try:
        writer = get_stream_writer()
        writer(
            {
                "phase": "loading_document_context",
                "message": "Loading sampled document content and existing categories.",
            }
        )

        source = await _get_document_classification_service().get_classification_source(
            UUID(state.document_id)
        )
        excerpt_text, sampled_chunk_indices = build_classification_excerpt(
            extracted_text=source.extracted_text,
            chunks=source.chunks,
            max_characters=_get_settings().documents.classification_excerpt_chars,
        )

        return {
            "original_filename": source.original_filename,
            "excerpt_text": excerpt_text,
            "sampled_chunk_indices": sampled_chunk_indices,
            "excerpt_character_count": len(excerpt_text),
            "categories": [
                {
                    "id": str(category.id),
                    "name": category.name,
                    "label_key": category.label_key,
                }
                for category in source.categories
            ],
        }
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def classify_document(state: State) -> dict[str, object]:
    try:
        writer = get_stream_writer()
        writer(
            {
                "phase": "classifying_document",
                "message": "Classifying the document against the known category catalog.",
            }
        )

        model = load_classification_model(_get_settings().openai_provider.classification_model)
        structured_model = model.with_structured_output(DocumentClassificationDecision)
        categories_text = _format_categories(state.categories)
        raw_decision = await structured_model.ainvoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_user_prompt(
                        original_filename=state.original_filename,
                        excerpt_text=state.excerpt_text,
                        categories_text=categories_text,
                    ),
                },
            ]
        )
        decision = DocumentClassificationDecision.model_validate(raw_decision)

        return {
            "decision": decision.decision,
            "matched_category_id": (
                str(decision.matched_category_id)
                if decision.matched_category_id is not None
                else None
            ),
            "suggested_category_name": decision.suggested_category_name,
            "suggested_category_label_key": (
                slugify_document_category_label_key(decision.suggested_category_label_key or "")
                if decision.suggested_category_label_key is not None
                else None
            ),
            "confidence": decision.confidence,
            "rationale": decision.rationale,
        }
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


def route_after_classification(
    state: State,
) -> Literal["persist_existing_category", "persist_suggested_category"]:
    if state.decision == "match_existing_category":
        return "persist_existing_category"
    return "persist_suggested_category"


async def persist_existing_category(state: State) -> dict[str, object]:
    try:
        matched_category_id = _require_string(state.matched_category_id, "matched_category_id")
        confidence = _require_float(state.confidence, "confidence")
        rationale = _require_string(state.rationale, "rationale")

        await _get_document_classification_service().record_ai_category_match(
            document_id=UUID(state.document_id),
            thread_id=state.thread_id,
            category_id=UUID(matched_category_id),
            confidence=confidence,
            rationale=rationale,
            sampled_chunk_indices=state.sampled_chunk_indices,
            excerpt_character_count=state.excerpt_character_count,
        )

        writer = get_stream_writer()
        writer(
            {
                "phase": "classification_completed",
                "message": "Matched the document to an existing category.",
            }
        )
        return {}
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def persist_suggested_category(state: State) -> dict[str, object]:
    try:
        suggested_category = _build_suggested_category(state)
        confidence = _require_float(state.confidence, "confidence")
        rationale = _require_string(state.rationale, "rationale")

        await _get_document_classification_service().record_ai_suggestion(
            document_id=UUID(state.document_id),
            thread_id=state.thread_id,
            suggested_category=suggested_category,
            confidence=confidence,
            rationale=rationale,
            sampled_chunk_indices=state.sampled_chunk_indices,
            excerpt_character_count=state.excerpt_character_count,
        )

        writer = get_stream_writer()
        writer(
            {
                "phase": "awaiting_human_review",
                "message": (
                    "No existing category matched cleanly. "
                    "Waiting for human review of the suggested category."
                ),
            }
        )
        return {}
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def review_suggested_category(state: State) -> dict[str, object]:
    suggested_category = _build_suggested_category(state)
    confidence = _require_float(state.confidence, "confidence")
    rationale = _require_string(state.rationale, "rationale")

    human_response = interrupt(
        {
            "action_request": {
                "action": "review_suggested_document_category",
                "args": {
                    "document_id": state.document_id,
                    "document_filename": state.original_filename,
                    "suggested_category": {
                        "name": suggested_category.name,
                        "label_key": suggested_category.label_key,
                    },
                    "confidence": confidence,
                    "rationale": rationale,
                },
            },
            "config": {
                "allow_accept": True,
                "allow_edit": True,
                "allow_ignore": True,
            },
        }
    )

    if not isinstance(human_response, list) or not human_response:
        return {"review_action": END}

    response = human_response[0]
    response_type = response.get("type")
    response_args = response.get("args")

    if response_type == "accept":
        return {"review_action": "accept_suggested_category"}

    if response_type == "edit" and isinstance(response_args, dict):
        updated_name = str(response_args.get("name") or suggested_category.name).strip()
        updated_label_key = slugify_document_category_label_key(
            str(response_args.get("label_key") or updated_name)
        )
        if updated_name:
            return {
                "review_action": "accept_suggested_category",
                "suggested_category_name": updated_name,
                "suggested_category_label_key": updated_label_key,
            }

    return {"review_action": END}


def route_after_review(state: State) -> Literal["accept_suggested_category", "__end__"]:
    if state.review_action == "accept_suggested_category":
        return "accept_suggested_category"
    return "__end__"


async def accept_suggested_category(state: State) -> dict[str, object]:
    try:
        suggested_category = _build_suggested_category(state)
        confidence = _require_float(state.confidence, "confidence")
        rationale = _require_string(state.rationale, "rationale")

        await _get_document_classification_service().accept_ai_suggested_category(
            document_id=UUID(state.document_id),
            thread_id=state.thread_id,
            suggested_category=suggested_category,
            confidence=confidence,
            rationale=rationale,
            sampled_chunk_indices=state.sampled_chunk_indices,
            excerpt_character_count=state.excerpt_character_count,
        )

        writer = get_stream_writer()
        writer(
            {
                "phase": "classification_completed",
                "message": "Saved the reviewed category and linked it to the document.",
            }
        )
        return {}
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def _record_failure(state: State, error_message: str) -> None:
    try:
        await _get_document_classification_service().mark_ai_failure(
            document_id=UUID(state.document_id),
            thread_id=state.thread_id,
            error_message=error_message,
        )
    except Exception:
        return


def _format_categories(categories: list[dict[str, str]]) -> str:
    if not categories:
        return "- No existing categories are available."
    return "\n".join(
        f"- id={category['id']} | name={category['name']} | label_key={category['label_key']}"
        for category in categories
    )


def _build_suggested_category(state: State) -> SuggestedDocumentCategory:
    name = normalize_document_category_name(
        _require_string(state.suggested_category_name, "suggested_category_name")
    )
    label_key = slugify_document_category_label_key(
        _require_string(state.suggested_category_label_key, "suggested_category_label_key")
    )
    if not label_key:
        label_key = slugify_document_category_label_key(name)
    return SuggestedDocumentCategory(name=name, label_key=label_key)


def _require_string(value: str | None, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required.")
    return normalized


def _require_float(value: float | None, field_name: str) -> float:
    if value is None:
        raise ValueError(f"{field_name} is required.")
    return value


builder = StateGraph(State, input_schema=InputState)
builder.add_node("load_document_context", load_document_context)
builder.add_node("classify_document", classify_document)
builder.add_node("persist_existing_category", persist_existing_category)
builder.add_node("persist_suggested_category", persist_suggested_category)
builder.add_node("review_suggested_category", review_suggested_category)
builder.add_node("accept_suggested_category", accept_suggested_category)

builder.add_edge("__start__", "load_document_context")
builder.add_edge("load_document_context", "classify_document")
builder.add_conditional_edges(
    "classify_document",
    route_after_classification,
    path_map=["persist_existing_category", "persist_suggested_category"],
)
builder.add_edge("persist_existing_category", END)
builder.add_edge("persist_suggested_category", "review_suggested_category")
builder.add_conditional_edges(
    "review_suggested_category",
    route_after_review,
    {
        "accept_suggested_category": "accept_suggested_category",
        "__end__": END,
    },
)
builder.add_edge("accept_suggested_category", END)

graph = builder.compile(name="document-classification-agent")
