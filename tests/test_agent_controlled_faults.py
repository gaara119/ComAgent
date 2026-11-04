"""Controlled transport failures through production JsonLLM, without paid APIs.

These fixtures exercise retry/recovery and budget stops. They are not online
Agent recovery, load tests, new benchmark questions, or real provider usage.
Set AGENT_CONTROLLED_FAULT_RECEIPT to a project-local .runtime JSON path to
retain the actual scenario results of this test execution.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from openai import OpenAI
from pydantic import BaseModel, ConfigDict
import pytest

from qa_agent.config import Settings
from qa_agent.llm import JsonLLM, LLMError, MissingCredentialError
from qa_agent.trace import TraceRecorder


class FaultProbe(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    ok: bool


def _healthy_response(content='{"ok":true}', *, finish="stop"):
    return httpx.Response(200, json={
        "id": "controlled-fault-response", "object": "chat.completion",
        "created": 0, "model": "controlled-fixture-model",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content},
                     "finish_reason": finish}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
    })


@pytest.fixture(scope="session")
def fault_results():
    records = []
    yield records
    configured = os.getenv("AGENT_CONTROLLED_FAULT_RECEIPT")
    if not configured:
        return
    root = Path(__file__).resolve().parents[1]
    path = Path(configured)
    path = (path if path.is_absolute() else root / path).resolve()
    if not path.is_relative_to((root / ".runtime").resolve()):
        raise ValueError("Controlled-fault receipt must stay in project .runtime")
    transient = [r for r in records if r["category"] == "transient_recovery"]
    fail_closed = [r for r in records if r["category"] in {"persistent_failure", "nonretryable_failure", "budget_stop", "missing_credential"}]
    payload = {
        "kind": "controlled_httpx_MockTransport_fault_injection",
        "production_target": "qa_agent.llm.JsonLLM.complete_json",
        "new_model_API_calls": 0, "database_queries": 0,
        "physical_fixture_attempts": sum(r["attempts"] for r in records),
        "scenarios": records,
        "transient_recovery": {"recovered": sum(r["recovered"] for r in transient),
                               "eligible_scenarios": len(transient)},
        "expected_fail_closed": {"passed_policy": sum(r["passed"] for r in fail_closed),
                                 "eligible_scenarios": len(fail_closed)},
        "limitations": ["All provider messages, statuses, usage and faults are fixtures.",
                        "No real provider reliability, current 240-task recovery rate or concurrent throughput is measured.",
                        "Sleep is stubbed; fixture elapsed time is not product latency.",
                        "Per-request total deadline is not implemented by JsonLLM alone and is not claimed here."]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def make_fault_llm(monkeypatch, events, *, call_limit=3, request_limit=3):
    calls = []

    def reply(request):
        calls.append(json.loads(request.content))
        event = events[min(len(calls) - 1, len(events) - 1)]
        if event == "timeout":
            raise httpx.ReadTimeout("controlled timeout", request=request)
        if isinstance(event, int):
            return httpx.Response(event, json={"error": {"message": "controlled provider failure"}})
        if event == "bad_json":
            return _healthy_response('{"ok":}')
        if event == "bad_schema":
            return _healthy_response('{"unrelated":true}')
        if event == "truncated":
            return _healthy_response('{"ok":', finish="length")
        return _healthy_response()

    settings = Settings(db_url="", llm_api_key="controlled-test-only",
                        llm_base_url="https://controlled.invalid/v1",
                        llm_max_attempts=call_limit,
                        llm_request_max_attempts=request_limit,
                        llm_timeout_seconds=1)
    model = JsonLLM(settings)
    monkeypatch.delenv("LLM_CAPTURE_DIR", raising=False)
    monkeypatch.setattr("qa_agent.llm.sleep", lambda _: None)
    monkeypatch.setattr(model, "_client", lambda: OpenAI(
        api_key="controlled-test-only", base_url="https://controlled.invalid/v1",
        max_retries=0, timeout=1,
        http_client=httpx.Client(transport=httpx.MockTransport(reply))))
    return model, calls


@pytest.mark.parametrize("event", [429, 503, "timeout", "bad_json", "bad_schema", "truncated"])
def test_transient_failure_recovers_without_changing_user_conditions(monkeypatch, fault_results, event):
    model, calls = make_fault_llm(monkeypatch, [event, "ok"])
    trace = TraceRecorder()
    result = model.complete_json("Validate structure only.", "Year=2024; country=Canada.", FaultProbe, trace)
    assert result.ok is True
    assert len(calls) == trace.llm_attempts == 2
    assert [s.status for s in trace.steps] == ["error", "ok"]
    assert all(c["messages"][1]["content"] == "Year=2024; country=Canada." for c in calls)
    assert trace.steps[-1].output_summary["usage"]["total_tokens"] == 13
    fault_results.append({"id": f"transient-{event}", "category": "transient_recovery",
                          "injected_fault": event, "attempts": len(calls), "recovered": True,
                          "passed": True, "trace_statuses": [s.status for s in trace.steps],
                          "usage_kind": "fixture_usage_only"})


@pytest.mark.parametrize("event,code", [(429, "llm_rate_limit"), (503, "llm_provider"),
                                        ("timeout", "llm_connection"), ("bad_json", "llm_format")])
def test_persistent_failure_stops_at_attempt_limit(monkeypatch, fault_results, event, code):
    model, calls = make_fault_llm(monkeypatch, [event])
    trace = TraceRecorder()
    with pytest.raises(LLMError) as error:
        model.complete_json("schema", "question", FaultProbe, trace)
    assert error.value.code == code
    assert len(calls) == trace.llm_attempts == 3
    assert all(s.status == "error" for s in trace.steps)
    fault_results.append({"id": f"persistent-{event}", "category": "persistent_failure",
                          "attempts": len(calls), "recovered": False, "passed": True,
                          "terminal_code": error.value.code})


@pytest.mark.parametrize("status,code", [(401, "llm_auth"), (403, "llm_auth"), (402, "llm_balance")])
def test_nonretryable_failure_never_spends_retry_budget(monkeypatch, fault_results, status, code):
    model, calls = make_fault_llm(monkeypatch, [status, "ok"])
    trace = TraceRecorder()
    with pytest.raises(LLMError) as error:
        model.complete_json("schema", "question", FaultProbe, trace)
    assert error.value.code == code and len(calls) == 1
    fault_results.append({"id": f"nonretryable-{status}", "category": "nonretryable_failure",
                          "attempts": 1, "recovered": False, "passed": True,
                          "terminal_code": error.value.code})


def test_budget_stops_format_retry_before_transport(monkeypatch, fault_results):
    model, calls = make_fault_llm(monkeypatch, ["bad_json", "ok"], request_limit=1)
    trace = TraceRecorder()
    with pytest.raises(LLMError) as error:
        model.complete_json("schema", "question", FaultProbe, trace)
    assert error.value.code == "llm_attempt_budget"
    assert len(calls) == trace.llm_attempts == 1
    fault_results.append({"id": "format-retry-budget-stop", "category": "budget_stop",
                          "attempts": 1, "recovered": False, "passed": True,
                          "terminal_code": error.value.code})


def test_shared_trace_budget_counts_failure_across_multiple_calls(monkeypatch, fault_results):
    model, calls = make_fault_llm(monkeypatch, [503, "ok", "ok"], request_limit=3)
    trace = TraceRecorder()
    assert model.complete_json("stage1", "question1", FaultProbe, trace).ok
    assert model.complete_json("stage2", "question2", FaultProbe, trace).ok
    with pytest.raises(LLMError) as error:
        model.complete_json("stage3", "question3", FaultProbe, trace)
    assert error.value.code == "llm_attempt_budget"
    assert len(calls) == trace.llm_attempts == 3
    fault_results.append({"id": "cross-stage-shared-budget", "category": "budget_stop",
                          "attempts": 3, "recovered": False, "passed": True,
                          "terminal_code": error.value.code,
                          "first_stage_recovery": True})


def test_missing_credential_blocks_before_client_or_transport(monkeypatch, fault_results):
    model = JsonLLM(Settings(db_url=""))
    calls = []

    def forbidden_client():
        calls.append(True)
        raise AssertionError("Transport must not be constructed")

    monkeypatch.setattr(model, "_client", forbidden_client)
    with pytest.raises(MissingCredentialError):
        model.complete_json("schema", "question", FaultProbe, TraceRecorder())
    assert calls == []
    fault_results.append({"id": "missing-credential", "category": "missing_credential",
                          "attempts": 0, "recovered": False, "passed": True})
