"""Automatic request-local tool tracing without argument/credential capture."""

import asyncio
import inspect
import json
from dataclasses import replace
from time import sleep

import pytest

from qa_agent.config import get_settings
from qa_agent.pipeline import chat
from qa_agent.schemas import ChatRequest
from qa_agent.sql.executor import SQLExecutionError, execute_sql
from qa_agent.trace import TraceRecorder, traced


def test_sync_decorator_preserves_result_signature_and_records_only_opted_in_fields():
    trace = TraceRecorder()
    result = object()

    @traced("tool", input_summary=lambda arguments: {"db_id": "chinook", "db_url": "private"},
            output_summary=lambda value: {"row_count": 1, "api_key": "private"})
    def tool(secret, trace=None):
        sleep(0.003)
        return result

    assert tool("must-not-be-logged", trace=trace) is result
    assert list(inspect.signature(tool).parameters) == ["secret", "trace"]
    assert len(trace.steps) == 1
    assert trace.steps[0].input_summary == {"db_id": "chinook"}
    assert trace.steps[0].output_summary == {"row_count": 1}
    assert trace.steps[0].status == "ok" and trace.steps[0].latency_ms >= 1
    assert "must-not-be-logged" not in json.dumps(trace.steps[0].model_dump())


def test_decorator_without_trace_preserves_call_and_has_no_summary_side_effects():
    def unexpected_summary(arguments):
        pytest.fail("A call without a recorder must not inspect or summarize arguments")

    @traced("tool", input_summary=unexpected_summary)
    def tool(value, trace=None):
        return value * 2

    assert tool(3) == 6


def test_failure_propagates_original_exception_with_sanitized_error_and_summaries():
    settings = replace(get_settings(), llm_api_key="sk-fake-unit-test",
                       db_url="postgresql://test:test-unit-password@localhost/test")
    trace = TraceRecorder(settings=settings)
    failure = RuntimeError(settings.db_url + " Bearer sk-fake-unit-test")

    @traced("tool", input_summary=lambda arguments: {"sql": "SELECT 'sk-fake-unit-test'"})
    def tool(trace=None):
        raise failure

    with pytest.raises(RuntimeError) as captured:
        tool(trace=trace)
    assert captured.value is failure
    assert trace.steps[0].status == "error"
    saved = json.dumps(trace.steps[0].model_dump())
    assert "sk-fake-unit-test" not in saved and "test-unit-password" not in saved
    assert "[redacted]" in saved


def test_concurrent_async_requests_keep_separate_recorders_and_values():
    async def scenario():
        first, second = TraceRecorder(), TraceRecorder()
        entered, release = asyncio.Event(), asyncio.Event()

        @traced("tool", output_summary=lambda value: {"row_count": value})
        async def tool(value, trace=None):
            if value == 1:
                entered.set()
                await release.wait()
            else:
                await entered.wait()
                release.set()
            return value

        assert await asyncio.gather(tool(1, first), tool(2, second)) == [1, 2]
        assert first.trace_id != second.trace_id
        assert len(first.steps) == len(second.steps) == 1
        assert first.steps[0] is not second.steps[0]
        assert first.steps[0].output_summary == {"row_count": 1}
        assert second.steps[0].output_summary == {"row_count": 2}

    asyncio.run(scenario())


def test_async_failure_is_recorded_and_re_raised():
    trace = TraceRecorder()
    failure = ValueError("Bearer sk-fake-async-test")

    @traced("tool")
    async def tool(trace=None):
        await asyncio.sleep(0)
        raise failure

    with pytest.raises(ValueError) as captured:
        asyncio.run(tool(trace))
    assert captured.value is failure
    assert trace.steps[0].status == "error"
    assert "sk-fake-async-test" not in json.dumps(trace.steps[0].model_dump())


def test_real_executor_records_actual_result_without_connection_arguments():
    settings = get_settings()
    trace = TraceRecorder(settings=settings)
    result = execute_sql("SELECT COUNT(*) AS n FROM customer", settings.db_url, trace=trace)
    assert result.rows == [[59]]
    assert len(trace.steps) == 1
    assert trace.steps[0].input_summary == {"sql": "SELECT COUNT(*) AS n FROM customer", "db_id": "chinook"}
    assert trace.steps[0].output_summary == {"row_count": 1, "columns": ["n"], "truncated": False}


def test_executor_failure_adds_one_error_step_and_preserves_error_type():
    trace = TraceRecorder()
    with pytest.raises(SQLExecutionError):
        execute_sql("SELECT 1", "", trace=trace)
    assert len(trace.steps) == 1 and trace.steps[0].status == "error"


def test_real_pipeline_uses_one_automatic_sql_exec_step_without_duplicate_timing():
    class ScriptedSQL:
        def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
            return response_model(sql="SELECT COUNT(*) AS n FROM customer", tables_used=["customer"],
                                  explanation="固定 SQL 仅验证工程链路，不计模型准确率")

    answer = chat(ChatRequest(message="工程检查客户数量"), llm=ScriptedSQL())
    assert answer.status == "SUCCEEDED" and answer.table == [{"n": 59}]
    execution_steps = [step for step in answer.steps if step.name == "sql_exec"]
    assert len(execution_steps) == 1
    assert execution_steps[0].status == "ok"
    assert execution_steps[0].output_summary == {"row_count": 1, "columns": ["n"], "truncated": False}
    assert answer.steps.index(execution_steps[0]) > next(i for i, step in enumerate(answer.steps) if step.name == "sql_validate")
