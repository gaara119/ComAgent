"""Contract and real DB wiring checks; scripted SQL is not an NL2SQL benchmark."""
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from api.main import app
from qa_agent.config import get_settings
from qa_agent.pipeline import chat
from qa_agent.schemas import AnswerEnvelope, ChatRequest


class ScriptedSQL:
    def __init__(self, sql):
        self.sql = sql
        self.calls = 0

    def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
        self.calls += 1
        return response_model(sql=self.sql, tables_used=[], explanation="测试注入的固定 SQL")


def test_missing_key_is_failed_not_clarification():
    settings = replace(get_settings(), llm_api_key="")
    response = chat(ChatRequest(message="客户有多少位？"), settings=settings)
    assert response.status == "FAILED"
    assert response.error.code == "missing_llm_key"
    assert response.sql is None


def test_api_rejects_empty_message():
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 422


def test_unsupported_cross_source_request_does_not_claim_success(monkeypatch):
    def unexpected_execution(*args, **kwargs):
        pytest.fail("不支持的跨源请求不得进入SQL执行链路")
    monkeypatch.setattr("qa_agent.pipeline._sql", unexpected_execution)
    response = chat(ChatRequest(message="问题", scope={"route": "hybrid"}))
    assert response.status == "UNSUPPORTED"
    assert response.sql is None


def test_auto_single_database_scope_dispatches_without_live_model(monkeypatch):
    received = []
    def scripted_channel(request, trace, settings, llm):
        received.append(request.scope)
        return AnswerEnvelope(trace_id=trace.trace_id, status="SUCCEEDED", answer="受控SQL通道")
    monkeypatch.setattr("qa_agent.pipeline._sql", scripted_channel)
    response = chat(ChatRequest(message="客户有多少位？", scope={"route": "auto", "db_id": "chinook"}))
    assert response.answer == "受控SQL通道"
    assert len(received) == 1
    assert received[0].route == "sql"
    assert received[0].db_id == "chinook"
    assert received[0].doc_ids == []


def test_auto_single_document_scope_dispatches_without_live_model(monkeypatch):
    received = []
    def scripted_channel(request, trace, settings):
        received.append(request.scope)
        return AnswerEnvelope(trace_id=trace.trace_id, status="SUCCEEDED", answer="受控文档通道")
    monkeypatch.setattr("qa_agent.pipeline._doc", scripted_channel)
    response = chat(ChatRequest(message="文档怎么说？", scope={"route": "auto", "db_id": "chinook", "doc_ids": ["manual-test"]}))
    assert response.answer == "受控文档通道"
    assert len(received) == 1
    assert received[0].route == "doc"
    assert received[0].db_id is None
    assert received[0].doc_ids == ["manual-test"]


def test_rag_hook_not_ready_is_explicit():
    settings = replace(get_settings(), rag_handler="qa_agent.rag.not_implemented:run")
    result = chat(ChatRequest(message="文档怎么说？", scope={"route": "doc", "db_id": None, "doc_ids": ["manual-1"]}), settings=settings)
    assert result.status == "UNSUPPORTED"
    assert not result.evidences


@pytest.mark.integration
@pytest.mark.parametrize("sql,expected_status,expected_table", [
    ("SELECT COUNT(*) AS total FROM customer", "SUCCEEDED", [{"total": 59}]),
    ("SELECT COUNT(*) AS total FROM customer WHERE country='Antarctica'", "SUCCEEDED", [{"total": 0}]),
    ("SELECT customer_id FROM customer WHERE country='Antarctica'", "EMPTY_RESULT", []),
    ("SELECT SUM(total) AS amount FROM invoice WHERE billing_country='Antarctica'", "SUCCEEDED", [{"amount": None}]),
])
def test_scripted_model_real_database_wiring(sql, expected_status, expected_table):
    if not get_settings().catalog_path.exists():
        pytest.skip("先运行数据库初始化与目录脚本")
    response = chat(ChatRequest(message="测试固定查询与真实数据库连接"), llm=ScriptedSQL(sql))
    assert response.status == expected_status
    assert response.table == expected_table
    assert response.sql
    assert {"sql_gen", "sql_validate", "sql_exec", "answer"} <= {s.name for s in response.steps}


@pytest.mark.parametrize("sql", [
    "DELETE FROM customer",
    "SELECT 59 AS customer_count",
    "SELECT COUNT(*) FROM customer c JOIN invoice i ON TRUE",
])
def test_rejected_generated_sql_never_reaches_executor(monkeypatch, sql):
    def unexpected_execution(*args, **kwargs):
        pytest.fail("禁止执行未经验证的 SQL")
    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", unexpected_execution)
    response = chat(ChatRequest(message="检查拦截"), llm=ScriptedSQL(sql))
    assert response.status == "FAILED"
    assert response.error.code == "sql_rejected"
    assert "sql_exec" not in [s.name for s in response.steps]


def test_health_reports_database_unavailable_without_secrets(monkeypatch):
    monkeypatch.setattr("api.main.get_settings", lambda: replace(get_settings(), db_url=""))
    with TestClient(app) as client:
        body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database_ready"] is False
    assert "db_url" not in body
    assert "llm_api_key" not in body


def test_api_contract_preserves_real_trace(monkeypatch):
    monkeypatch.setattr("api.main.chat", lambda req: chat(req, llm=ScriptedSQL("SELECT COUNT(*) AS n FROM customer")))
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"session_id": "integration-test", "message": "客户数"})
    assert response.status_code == 200
    body = response.json()
    assert body["table"] == [{"n": 59}]
    assert body["trace_id"]
    assert body["metadata"]["result_columns"] == ["n"]


def test_doc_hook_cannot_return_another_documents_evidence(monkeypatch):
    from types import SimpleNamespace
    from qa_agent.schemas import AnswerEnvelope, Evidence
    def handler(**kwargs):
        return AnswerEnvelope(trace_id=kwargs["trace_id"], status="SUCCEEDED", answer="错误来源",
                              evidences=[Evidence(evidence_id="E1", doc_id="another-doc", doc_title="另一个文档", text="片段")])
    # This unit isolates the plugin's citation boundary. The actual registered
    # manifest/index resolution is exercised by document_scope_intent_pipeline.
    monkeypatch.setattr("qa_agent.rag.task.resolve_document_scope", lambda request, settings: [
        {"doc_id": "selected-doc", "title": "selected fixture"}])
    monkeypatch.setattr("qa_agent.pipeline.importlib.import_module", lambda _: SimpleNamespace(run=handler))
    settings = replace(get_settings(), rag_handler="qa_agent.rag.test:run")
    result = chat(ChatRequest(message="问题", scope={"route": "doc", "doc_ids": ["selected-doc"], "db_id": None}), settings=settings)
    assert result.status == "FAILED"
    assert result.error.code == "rag_failed"


@pytest.mark.parametrize("sqlstate", [None, "08006", "42501", "25006"])
def test_database_connection_or_permission_failure_does_not_call_model_again(monkeypatch, sqlstate):
    from qa_agent.sql.executor import SQLExecutionError
    def fail_execution(*args, **kwargs):
        raise SQLExecutionError("数据库连接或权限错误", sqlstate=sqlstate)
    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", fail_execution)
    llm = ScriptedSQL("SELECT COUNT(*) FROM customer")
    response = chat(ChatRequest(message="客户数"), llm=llm)
    assert response.status == "FAILED"
    assert response.error.code == "sql_execution"
    assert llm.calls == 1


def test_technical_execution_error_has_bounded_sql_repair(monkeypatch):
    from qa_agent.sql.executor import SQLExecutionError
    def fail_execution(*args, **kwargs):
        raise SQLExecutionError("SQL 类型错误", sqlstate="42804")
    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", fail_execution)
    llm = ScriptedSQL("SELECT COUNT(*) FROM customer")
    settings = replace(get_settings(), sql_repair_attempts=2)
    response = chat(ChatRequest(message="客户数"), llm=llm, settings=settings)
    assert response.error.code == "sql_execution"
    assert llm.calls == 3


def test_doc_dependency_failure_is_failed_not_unimplemented(monkeypatch):
    def fail_import(name):
        raise ModuleNotFoundError("No module named 'missing_b_dependency'", name="missing_b_dependency")
    monkeypatch.setattr("qa_agent.pipeline.importlib.import_module", fail_import)
    result = chat(ChatRequest(message="问题", scope={"route": "doc", "doc_ids": ["manual-1"], "db_id": None}))
    assert result.status == "FAILED"
    assert result.error.code == "rag_dependency"
