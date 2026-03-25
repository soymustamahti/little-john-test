"""Backport LangGraph control-flow tracing fixes missing from Aegra 0.8.2.

LangGraph pauses human-in-the-loop runs by raising ``GraphInterrupt``. Older
Aegra/OpenInference combinations record that expected control flow as a real
error in tracing backends such as Langfuse.

The local Aegra reference repo already patches this behavior. This module keeps
the current app runtime aligned until the packaged Aegra dependency is upgraded.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_PATCHED = False


def patch_langchain_control_flow_exceptions() -> None:
    """Treat expected LangGraph interrupt exceptions as non-errors."""

    global _PATCHED
    if _PATCHED:
        return

    try:
        from langgraph.errors import GraphBubbleUp
        from openinference.instrumentation.langchain import _tracer
    except ImportError as exc:
        logger.debug(
            "langchain_control_flow_patch_skipped",
            extra={"reason": str(exc)},
        )
        return

    ignored_exception_patterns = getattr(_tracer, "IGNORED_EXCEPTION_PATTERNS", None)
    original_record_exception = getattr(_tracer, "_record_exception", None)
    if not isinstance(ignored_exception_patterns, list) or original_record_exception is None:
        logger.debug(
            "langchain_control_flow_patch_skipped",
            extra={"reason": "unexpected_openinference_tracer_shape"},
        )
        return

    ignore_pattern = r"^GraphInterrupt\("
    if ignore_pattern not in ignored_exception_patterns:
        ignored_exception_patterns.append(ignore_pattern)

    if getattr(original_record_exception, "_little_john_graphbubble_wrapped", False):
        _PATCHED = True
        return

    def _record_exception_without_graph_bubbleups(span: Any, error: BaseException) -> None:
        if isinstance(error, GraphBubbleUp):
            return
        original_record_exception(span, error)

    setattr(
        _record_exception_without_graph_bubbleups,
        "_little_john_graphbubble_wrapped",
        True,
    )
    _tracer._record_exception = _record_exception_without_graph_bubbleups
    _PATCHED = True


def reset_langchain_control_flow_patch_for_tests() -> None:
    """Reset local patch state for unit tests."""

    global _PATCHED
    _PATCHED = False
