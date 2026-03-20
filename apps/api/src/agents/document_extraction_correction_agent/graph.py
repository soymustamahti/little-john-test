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
from src.agents.document_extraction_agent.normalization import normalize_reasoning_summary
from src.agents.document_extraction_agent.tools import TOOLS
from src.agents.document_extraction_correction_agent.merge import (
    apply_extraction_corrections,
)
from src.agents.document_extraction_correction_agent.prompts import (
    FINALIZER_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_agent_user_prompt,
    build_finalizer_user_prompt,
)
from src.agents.document_extraction_correction_agent.schemas import (
    CorrectionFinalizerDraft,
)
from src.agents.document_extraction_correction_agent.state import InputState, State
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


def _load_correction_model() -> BaseChatModel:
    return init_chat_model(
        _get_settings().openai_provider.extraction_model,
        model_provider="openai",
    )


MAX_TOOL_MESSAGES = 10


async def load_correction_context(state: State) -> dict[str, object]:
    writer = get_stream_writer()
    writer(
        {
            "phase": "loading_correction_context",
            "message": "Loading the current extraction draft, chat history, and document context.",
        }
    )

    try:
        source = await _get_document_extraction_service().get_correction_source(
            document_id=UUID(state.document_id),
        )
        current_result = source.current_result.model_dump(mode="json")
        correction_history = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in source.correction_messages
        ]
        return {
            "original_filename": source.original_filename,
            "file_kind": source.file_kind,
            "file_extension": source.file_extension,
            "template_name": source.template_name,
            "template_locale": source.template_locale,
            "template_modules": source.template_modules,
            "current_result": current_result,
            "current_reasoning_summary": source.reasoning_summary or "",
            "correction_history": correction_history,
            "messages": [
                HumanMessage(
                    content=build_agent_user_prompt(
                        document_id=state.document_id,
                        original_filename=source.original_filename,
                        file_kind=source.file_kind,
                        template_name=source.template_name,
                        template_locale=source.template_locale,
                        template_modules=source.template_modules,
                        current_result=current_result,
                        current_reasoning_summary=source.reasoning_summary or "",
                        correction_history=correction_history,
                        user_message=state.user_message,
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
                "phase": "reviewing_requested_change",
                "message": (
                    "Correction search budget reached. Finalizing from the strongest findings "
                    "gathered so far."
                ),
            }
        )
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Correction search budget reached. "
                        "Proceed with the strongest supported patch."
                    )
                )
            ]
        }

    writer(
        {
            "phase": "reviewing_requested_change",
            "message": (
                "Reviewing the requested change and deciding whether more "
                "document evidence is needed."
                if latest_tool_message is None
                else (
                    "Checking the latest evidence and deciding the next targeted correction lookup."
                )
            ),
        }
    )

    try:
        model = _load_correction_model().bind_tools(TOOLS)
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
                            "Proceed with the strongest supported correction."
                        ),
                    )
                ]
            }

        return {"messages": [response]}
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


def route_model_output(state: State) -> Literal["tools", "finalize_correction"]:
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected an AIMessage before routing, got {type(last_message).__name__}."
        )
    if last_message.tool_calls:
        return "tools"
    return "finalize_correction"


async def finalize_correction(state: State) -> dict[str, object]:
    writer = get_stream_writer()
    writer(
        {
            "phase": "finalizing_correction",
            "message": "Applying the requested correction to the extraction draft.",
        }
    )

    try:
        structured_model = _load_correction_model().with_structured_output(
            CorrectionFinalizerDraft,
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
                        current_result=state.current_result or {"modules": []},
                        template_modules=state.template_modules,
                        user_message=state.user_message,
                        evidence_transcript=evidence_transcript,
                    ),
                },
            ]
        )
        draft = CorrectionFinalizerDraft.model_validate(draft_response)
        current_result = DocumentExtractionResultRead.model_validate(
            state.current_result or {"modules": []}
        )
        corrected_result = apply_extraction_corrections(
            template_modules=state.template_modules,
            current_result=current_result,
            raw_updates=draft.updates.model_dump(mode="python"),
        )
        assistant_response = _normalize_chat_reply(draft.assistant_response)
        correction_summary = normalize_reasoning_summary(draft.reasoning_summary)
        return {
            "assistant_response": assistant_response,
            "correction_summary": correction_summary,
            "corrected_result": corrected_result.model_dump(mode="json"),
            "messages": [
                AIMessage(
                    content=(
                        "The correction patch is ready and the extraction draft will be updated."
                    )
                )
            ],
        }
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def persist_correction_draft(state: State) -> dict[str, object]:
    writer = get_stream_writer()
    writer(
        {
            "phase": "saving_correction_draft",
            "message": "Saving the corrected extraction draft and chat response.",
        }
    )

    try:
        corrected_result = getattr(state, "corrected_result", None)
        if not isinstance(corrected_result, dict):
            raise ValueError("The correction finalizer did not produce a corrected draft.")

        await _get_document_extraction_service().save_chat_correction(
            document_id=UUID(state.document_id),
            user_message=state.user_message,
            assistant_response=state.assistant_response or "The draft was updated.",
            result=DocumentExtractionResultRead.model_validate(corrected_result),
            reasoning_summary=state.correction_summary or None,
        )
        writer(
            {
                "phase": "correction_ready_for_review",
                "message": "The corrected draft is ready for review in the extraction panel.",
            }
        )
        return {}
    except Exception as exc:
        await _record_failure(state, str(exc))
        raise


async def _record_failure(state: State, error_message: str) -> None:
    try:
        await _get_document_extraction_service().mark_correction_failure(
            document_id=UUID(state.document_id),
            user_message=state.user_message,
            error_message=error_message,
        )
    except Exception:
        return


def _build_evidence_transcript(messages: Sequence[BaseMessage]) -> str:
    transcript_parts: list[str] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            transcript_parts.append(f"[human]\n{message.content}")
        elif isinstance(message, AIMessage):
            content = str(message.content).strip()
            if content:
                transcript_parts.append(f"[assistant]\n{content}")
        elif isinstance(message, ToolMessage):
            transcript_parts.append(f"[tool:{message.name or 'tool'}]\n{message.content}")

    return "\n\n".join(part for part in transcript_parts if part).strip()


def _normalize_chat_reply(value: str) -> str:
    normalized = " ".join(value.split()).strip()
    if normalized:
        return normalized[:1200]
    return "I reviewed the correction request and updated the extraction draft."


builder = StateGraph(State, input_schema=InputState)
builder.add_node("load_correction_context", load_correction_context)
builder.add_node("call_model", call_model)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_node("finalize_correction", finalize_correction)
builder.add_node("persist_correction_draft", persist_correction_draft)

builder.add_edge("__start__", "load_correction_context")
builder.add_edge("load_correction_context", "call_model")
builder.add_conditional_edges(
    "call_model",
    route_model_output,
    path_map=["tools", "finalize_correction"],
)
builder.add_edge("tools", "call_model")
builder.add_edge("finalize_correction", "persist_correction_draft")
builder.add_edge("persist_correction_draft", END)

graph = builder.compile(name="document-extraction-correction-agent")
