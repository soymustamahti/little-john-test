from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep


@dataclass
class InputState:
    document_id: str
    thread_id: str
    user_message: str
    messages: Annotated[Sequence[AnyMessage], add_messages] = field(default_factory=list)


@dataclass
class State(InputState):
    original_filename: str = ""
    file_kind: str = ""
    file_extension: str = ""
    template_name: str = ""
    template_locale: str = ""
    template_modules: list[dict[str, Any]] = field(default_factory=list)
    current_result: dict[str, Any] | None = None
    current_reasoning_summary: str = ""
    correction_history: list[dict[str, str]] = field(default_factory=list)
    assistant_response: str = ""
    correction_summary: str = ""
    corrected_result: dict[str, Any] | None = None
    is_last_step: IsLastStep = field(default=False)
