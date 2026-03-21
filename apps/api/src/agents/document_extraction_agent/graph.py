from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Literal
from uuid import UUID

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agents.document_extraction_agent.normalization import (
    extraction_result_has_values,
    normalize_extraction_result,
    normalize_reasoning_summary,
)
from src.agents.document_extraction_agent.prompts import (
    FINALIZER_SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_agent_user_prompt,
    build_finalizer_user_prompt,
    build_repair_user_prompt,
)
from src.agents.document_extraction_agent.schemas import (
    ExtractionFinalizerDecision,
    ExtractionFinalizerDraft,
    ExtractionResultDraft,
)
from src.agents.document_extraction_agent.state import InputState, State
from src.agents.document_extraction_agent.tools import TOOLS
from src.core.config import Settings, get_settings
from src.documents.extraction_schemas import DocumentExtractionResultRead
from src.documents.extraction_service import DocumentExtractionService
from src.documents.runtime import get_document_extraction_service


@lru_cache
def _get_document_extraction_service() -> DocumentExtractionService:
    return get_document_extraction_service()


@lru_cache
def _get_settings() -> Settings:
    return get_settings()


def _load_extraction_model() -> BaseChatModel:
    return init_chat_model(
        _get_settings().openai_provider.extraction_model,
        model_provider="openai",
    )


MAX_TOOL_MESSAGES = 12


async def load_document_and_template(state: State) -> dict[str, object]:
    writer = get_stream_writer()
    writer(
        {
            "phase": "loading_extraction_context",
            "message": "Loading the selected template and the stored document content.",
        }
    )

    try:
        source = await _get_document_extraction_service().get_extraction_source(
            document_id=UUID(state.document_id),
            template_id=UUID(state.extraction_template_id),
        )
        return {
            "original_filename": source.original_filename,
            "file_kind": source.file_kind,
            "file_extension": source.file_extension,
            "template_name": source.template_name,
            "template_locale": source.template_locale,
            "template_modules": source.template_modules,
            "messages": [
                HumanMessage(
                    content=build_agent_user_prompt(
                        document_id=state.document_id,
                        original_filename=source.original_filename,
                        file_kind=source.file_kind,
                        template_name=source.template_name,
                        template_locale=source.template_locale,
                        template_modules=source.template_modules,
                    )
                )
            ],
        }
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def call_model(state: State) -> dict[str, object]:
    writer = get_stream_writer()
    tool_message_count = sum(
        1 for message in state.messages if isinstance(message, ToolMessage)
    )
    latest_tool_message = next(
        (message for message in reversed(state.messages) if isinstance(message, ToolMessage)),
        None,
    )
    if tool_message_count >= MAX_TOOL_MESSAGES:
        writer(
            {
                "phase": "planning_and_retrieving",
                "message": (
                    "Evidence collection budget reached. Finalizing from the strongest "
                    "findings gathered so far."
                ),
            }
        )
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Evidence collection budget reached. "
                        "Proceed with the strongest evidence gathered so far."
                    )
                )
            ]
        }

    writer(
        {
            "phase": "planning_and_retrieving",
            "message": (
                "Planning the first evidence pass across the required template fields."
                if latest_tool_message is None
                else (
                    "Reviewing the latest retrieval results and deciding the next targeted lookup."
                )
            ),
        }
    )

    try:
        model = _load_extraction_model().bind_tools(TOOLS)
        response = await model.ainvoke(
            [{"role": "system", "content": SYSTEM_PROMPT}, *state.messages]
        )

        if state.is_last_step and response.tool_calls:
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content=(
                            "I do not have enough budget to keep searching. "
                            "Proceed with the strongest evidence gathered so far."
                        ),
                    )
                ]
            }

        return {"messages": [response]}
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


def route_model_output(state: State) -> Literal["tools", "finalize_extraction"]:
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected an AIMessage before routing, got {type(last_message).__name__}."
        )
    if last_message.tool_calls:
        return "tools"
    return "finalize_extraction"


async def finalize_extraction(state: State) -> dict[str, object]:
    writer = get_stream_writer()
    writer(
        {
            "phase": "finalizing_extraction",
            "message": "Building the structured extraction draft from the gathered evidence.",
        }
    )

    try:
        structured_model = _load_extraction_model().with_structured_output(
            ExtractionFinalizerDraft,
            method="function_calling",
        )
        evidence_transcript = _build_evidence_transcript(state.messages)
        draft_response = await structured_model.ainvoke(
            [
                {"role": "system", "content": FINALIZER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_finalizer_user_prompt(
                        document_id=state.document_id,
                        original_filename=state.original_filename,
                        file_kind=state.file_kind,
                        template_name=state.template_name,
                        template_locale=state.template_locale,
                        template_modules=state.template_modules,
                        evidence_transcript=evidence_transcript,
                    ),
                },
            ]
        )
        draft = ExtractionFinalizerDraft.model_validate(draft_response)
        reasoning_summary = normalize_reasoning_summary(draft.reasoning_summary)
        normalized_result = normalize_extraction_result(
            template_modules=state.template_modules,
            raw_result=draft.result.model_dump(mode="python"),
        )
        if not extraction_result_has_values(normalized_result):
            writer(
                {
                    "phase": "finalizing_extraction",
                    "message": (
                        "Repairing the structured extraction fields from the summarized "
                        "findings and supporting evidence."
                    ),
                }
            )
            normalized_result = await _repair_extraction_result(
                state=state,
                evidence_transcript=evidence_transcript,
                reasoning_summary=reasoning_summary,
                fallback_result=normalized_result,
            )

        validated = ExtractionFinalizerDecision(
            reasoning_summary=reasoning_summary,
            result=normalized_result,
        )
        return {
            "extraction_summary": validated.reasoning_summary,
            "messages": [
                AIMessage(
                    content=(
                        "Evidence gathering finished. "
                        "The structured extraction draft is ready for review."
                    )
                )
            ],
            "final_result": validated.result.model_dump(mode="json"),
        }
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def _repair_extraction_result(
    *,
    state: State,
    evidence_transcript: str,
    reasoning_summary: str,
    fallback_result: DocumentExtractionResultRead,
) -> DocumentExtractionResultRead:
    try:
        repair_model = _load_extraction_model().with_structured_output(
            ExtractionResultDraft,
            method="function_calling",
        )
        repair_response = await repair_model.ainvoke(
            [
                {"role": "system", "content": REPAIR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_repair_user_prompt(
                        document_id=state.document_id,
                        original_filename=state.original_filename,
                        file_kind=state.file_kind,
                        template_name=state.template_name,
                        template_locale=state.template_locale,
                        template_modules=state.template_modules,
                        reasoning_summary=reasoning_summary,
                        evidence_transcript=evidence_transcript,
                    ),
                },
            ]
        )
        repaired_result = normalize_extraction_result(
            template_modules=state.template_modules,
            raw_result=ExtractionResultDraft.model_validate(repair_response).model_dump(
                mode="python"
            ),
        )
        if extraction_result_has_values(repaired_result):
            return repaired_result
    except Exception:
        return fallback_result

    return fallback_result


async def persist_extraction_draft(state: State) -> dict[str, object]:
    writer = get_stream_writer()
    writer(
        {
            "phase": "saving_extraction_draft",
            "message": "Saving the AI extraction draft for operator review.",
        }
    )

    try:
        final_result = getattr(state, "final_result", None)
        if not isinstance(final_result, dict):
            raise ValueError("The extraction finalizer did not produce a result payload.")

        await _get_document_extraction_service().save_ai_draft(
            document_id=UUID(state.document_id),
            template_id=UUID(state.extraction_template_id),
            thread_id=state.thread_id,
            result=ExtractionFinalizerDecision.model_validate(
                {
                    "reasoning_summary": state.extraction_summary or "Structured extraction ready.",
                    "result": final_result,
                }
            ).result,
            reasoning_summary=state.extraction_summary or None,
        )
        writer(
            {
                "phase": "extraction_ready_for_review",
                "message": "The extraction draft is ready for manual review in the UI.",
            }
        )
        return {}
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def _record_failure(state: State, error_message: str) -> None:
    try:
        await _get_document_extraction_service().mark_ai_failure(
            document_id=UUID(state.document_id),
            thread_id=state.thread_id,
            error_message=error_message,
        )
    except Exception:
        return


def _build_evidence_transcript(messages: Sequence[BaseMessage]) -> str:
    transcript_parts: list[str] = []
    for message in messages:
        if isinstance(message, ToolMessage):
            transcript_parts.append(f"[tool:{message.name or 'tool'}]\n{message.content}")

    return "\n\n".join(part for part in transcript_parts if part).strip()


builder = StateGraph(State, input_schema=InputState)
builder.add_node("load_document_and_template", load_document_and_template)
builder.add_node("call_model", call_model)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_node("finalize_extraction", finalize_extraction)
builder.add_node("persist_extraction_draft", persist_extraction_draft)

builder.add_edge("__start__", "load_document_and_template")
builder.add_edge("load_document_and_template", "call_model")
builder.add_conditional_edges(
    "call_model",
    route_model_output,
    path_map=["tools", "finalize_extraction"],
)
builder.add_edge("tools", "call_model")
builder.add_edge("finalize_extraction", "persist_extraction_draft")
builder.add_edge("persist_extraction_draft", END)

graph = builder.compile(name="document-extraction-agent")
