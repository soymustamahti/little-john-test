from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import src.main as main_module
from langgraph.errors import GraphInterrupt
from openinference.instrumentation.langchain import _tracer
from src.core.observability import (
    patch_langchain_control_flow_exceptions,
    reset_langchain_control_flow_patch_for_tests,
)


def test_patch_ignores_graph_interrupts_without_hiding_real_errors() -> None:
    original_patterns = list(_tracer.IGNORED_EXCEPTION_PATTERNS)
    original_record_exception = _tracer._record_exception
    recorded_errors: list[BaseException] = []

    def fake_record_exception(_span: object, error: BaseException) -> None:
        recorded_errors.append(error)

    try:
        reset_langchain_control_flow_patch_for_tests()
        _tracer.IGNORED_EXCEPTION_PATTERNS = []
        _tracer._record_exception = fake_record_exception

        patch_langchain_control_flow_exceptions()

        assert r"^GraphInterrupt\(" in _tracer.IGNORED_EXCEPTION_PATTERNS

        _tracer._record_exception(SimpleNamespace(), GraphInterrupt(("waiting",)))
        assert recorded_errors == []

        real_error = RuntimeError("boom")
        _tracer._record_exception(SimpleNamespace(), real_error)
        assert recorded_errors == [real_error]
    finally:
        _tracer.IGNORED_EXCEPTION_PATTERNS = original_patterns
        _tracer._record_exception = original_record_exception
        reset_langchain_control_flow_patch_for_tests()


@pytest.mark.asyncio
async def test_lifespan_applies_graph_interrupt_patch(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_mock = Mock()
    check_database_connection_mock = AsyncMock(return_value=True)
    run_app_migrations_async_mock = AsyncMock()
    run_app_seeds_async_mock = AsyncMock()
    dispose_database_mock = AsyncMock()

    monkeypatch.setattr(main_module, "patch_langchain_control_flow_exceptions", patch_mock)
    monkeypatch.setattr(main_module, "check_database_connection", check_database_connection_mock)
    monkeypatch.setattr(main_module, "run_app_migrations_async", run_app_migrations_async_mock)
    monkeypatch.setattr(main_module, "run_app_seeds_async", run_app_seeds_async_mock)
    monkeypatch.setattr(main_module, "dispose_database", dispose_database_mock)

    async with main_module.lifespan(main_module.app):
        pass

    patch_mock.assert_called_once_with()
    check_database_connection_mock.assert_awaited_once_with()
    run_app_migrations_async_mock.assert_awaited_once_with()
    run_app_seeds_async_mock.assert_awaited_once_with()
    dispose_database_mock.assert_awaited_once_with()
