"""Bounded JSON retry and provider error behavior with an HTTP fixture."""
import json
from dataclasses import replace

import httpx
import pytest
from openai import OpenAI
from pydantic import BaseModel

from qa_agent.config import get_settings
from qa_agent.llm import JsonLLM, LLMError
from qa_agent.trace import TraceRecorder


class Probe(BaseModel):
    ok: bool


def make_llm(monkeypatch, contents, status=200):
    calls = []
    def reply(request):
        calls.append(json.loads(request.content))
        if status != 200:
            return httpx.Response(status, json={"error": {"message": "provider error"}})
        content = contents[min(len(calls)-1, len(contents)-1)]
        return httpx.Response(200, json={
            "id": "chatcmpl-test", "object": "chat.completion", "created": 0, "model": "test-model",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
        })
    settings = replace(get_settings(), llm_api_key="test-dummy", llm_max_attempts=3)
    model = JsonLLM(settings)
    monkeypatch.setattr(model, "_client", lambda: OpenAI(api_key="test-dummy", base_url="https://example.test/v1",
                         max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(reply))))
    return model, calls


def test_json_fields_validated_and_real_usage_recorded(monkeypatch):
    llm, calls = make_llm(monkeypatch, ['{"ok":true}'])
    trace = TraceRecorder()
    assert llm.complete_json("prompt", "question", Probe, trace).ok is True
    assert len(calls) == 1
    assert trace.steps[0].output_summary["usage"]["total_tokens"] == 13


def test_format_retry_is_bounded(monkeypatch):
    llm, calls = make_llm(monkeypatch, ["not json", "not json", "not json"])
    trace = TraceRecorder()
    with pytest.raises(LLMError) as error:
        llm.complete_json("prompt", "question", Probe, trace)
    assert error.value.code == "llm_format"
    assert len(calls) == 3
    assert all(step.status == "error" for step in trace.steps)


def test_auth_failure_is_not_retried(monkeypatch):
    llm, calls = make_llm(monkeypatch, [""], status=401)
    with pytest.raises(LLMError) as error:
        llm.complete_json("prompt", "question", Probe, TraceRecorder())
    assert error.value.code == "llm_auth"
    assert len(calls) == 1


def test_total_budget_survives_multiple_generation_calls(monkeypatch):
    llm, calls = make_llm(monkeypatch, ['{"ok":true}'])
    trace = TraceRecorder()
    for _ in range(3):
        assert llm.complete_json("prompt", "question", Probe, trace).ok
    with pytest.raises(LLMError) as error:
        llm.complete_json("prompt", "question", Probe, trace)
    assert error.value.code == "llm_attempt_budget"
    assert len(calls) == 3
