"""Candidate-domain errors use existing bounded JSON retry, not unsafe acceptance."""
from dataclasses import replace
import json

import httpx
from openai import OpenAI
from pydantic import ValidationError
import pytest

from qa_agent.config import get_settings
from qa_agent.llm import JsonLLM, LLMError
from qa_agent.sql.catalog import Catalog, CatalogColumn, CatalogTable
from qa_agent.sql.pruner import SchemaPruner, make_pruning_decision_model
from qa_agent.sql.schema_linker import SchemaBundle
from qa_agent.trace import TraceRecorder


def selected(name="s.sales"):
    return {"table": name, "columns": ["id"], "reason": "actual user object"}


def valid():
    return {"selected": [selected()], "excluded": {"s.purchase": "unrequested object"}}


def fixture_catalog_bundle():
    columns = (CatalogColumn("id", "integer"),)
    catalog = Catalog("fixture", tuple(CatalogTable("s", name, columns, name, ("id",))
                                       for name in ("sales", "purchase", "employee")))
    bundle = SchemaBundle(selected_tables=("s.sales", "s.purchase"), columns={}, join_paths=(), reasons={},
        table_recall=(), column_recall=(), value_recall=(), terminal_tables=("s.sales", "s.purchase"),
        bridge_tables=(), disconnected_components=(), scores={}, query_facets=("question",),
        per_query_recall=(), selected_catalog=catalog)
    return catalog, bundle


def mock_llm(monkeypatch, decisions, request_budget=None):
    calls = []
    def reply(request):
        calls.append(json.loads(request.content))
        body = decisions[min(len(calls) - 1, len(decisions) - 1)]
        return httpx.Response(200, json={"id": "chatcmpl-local-domain-test", "object": "chat.completion",
            "created": 0, "model": "test-model", "choices": [{"index": 0,
                "message": {"role": "assistant", "content": json.dumps(body)}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13}})
    monkeypatch.delenv("LLM_CAPTURE_DIR", raising=False)
    settings = replace(get_settings(), llm_api_key="test-dummy", llm_max_attempts=3,
                       llm_request_max_attempts=request_budget)
    llm = JsonLLM(settings)
    monkeypatch.setattr(llm, "_client", lambda: OpenAI(api_key="test-dummy", base_url="https://example.test/v1",
        max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(reply))))
    return llm, calls


@pytest.mark.parametrize("decision", [
    {"selected": [selected("s.employee")], "excluded": {}},
    {"selected": [selected("s.missing")], "excluded": {}},
    {"selected": [selected(), selected()], "excluded": {}},
    {"selected": [selected()], "excluded": {"s.employee": "exists outside candidate domain"}},
    {"selected": [selected()], "excluded": {"s.sales": "cannot both select and exclude"}},
])
def test_invalid_selection_or_exclusion_never_passes_domain_model(decision):
    model = make_pruning_decision_model(["s.sales", "s.purchase"])
    with pytest.raises(ValidationError):
        model.model_validate(decision)


def test_extra_exclusion_retry_then_valid_selection_succeeds(monkeypatch):
    bad = {"selected": [selected()], "excluded": {"s.employee": "FK mentioned this noncandidate"}}
    llm, calls = mock_llm(monkeypatch, [bad, valid()])
    trace = TraceRecorder(settings=llm.settings)
    catalog, bundle = fixture_catalog_bundle()
    result = SchemaPruner(catalog).prune("query the sales table", bundle, llm, trace)
    assert result.selected_tables == ("s.sales",)
    assert result.excluded_tables == {"s.purchase": "unrequested object"}
    assert len(calls) == trace.llm_attempts == 2
    assert [step.status for step in trace.steps if step.name == "llm"] == ["error", "ok"]
    assert "s.employee" not in result.excluded_tables


def test_repeated_invalid_domain_exhausts_existing_three_attempts(monkeypatch):
    bad = {"selected": [selected()], "excluded": {"s.employee": "not in actual candidate prompt"}}
    llm, calls = mock_llm(monkeypatch, [bad])
    trace = TraceRecorder(settings=llm.settings)
    catalog, bundle = fixture_catalog_bundle()
    with pytest.raises(LLMError) as error:
        SchemaPruner(catalog).prune("query", bundle, llm, trace)
    assert error.value.code == "llm_format"
    assert len(calls) == trace.llm_attempts == 3
    assert all(step.status == "error" for step in trace.steps if step.name == "llm")
    assert not any(step.name in {"sql_gen", "sql_exec"} for step in trace.steps)


def test_whole_request_budget_still_caps_domain_retries(monkeypatch):
    bad = {"selected": [selected()], "excluded": {"s.employee": "not a candidate"}}
    llm, calls = mock_llm(monkeypatch, [bad], request_budget=2)
    trace = TraceRecorder(settings=llm.settings)
    catalog, bundle = fixture_catalog_bundle()
    with pytest.raises(LLMError) as error:
        SchemaPruner(catalog).prune("query", bundle, llm, trace)
    assert error.value.code == "llm_attempt_budget"
    assert len(calls) == trace.llm_attempts == 2


def test_native_json_schema_lists_authentic_candidate_names():
    schema = make_pruning_decision_model(["s.sales", "s.purchase"]).model_json_schema()
    choice = schema["$defs"]["CandidateTableChoice"]
    assert choice["properties"]["table"]["enum"] == ["s.sales", "s.purchase"]
    assert schema["properties"]["excluded"]["propertyNames"]["enum"] == ["s.sales", "s.purchase"]
