"""A rejected old condition must not become a mandatory repair condition."""
from dataclasses import replace
from types import SimpleNamespace

from qa_agent.clarify.rules import SemanticIntent
from qa_agent.clarify.state import SessionState
from qa_agent.config import get_settings
from qa_agent.pipeline import chat
from qa_agent.schemas import ChatRequest, IntentContract
from qa_agent.sql.executor import SQLResult


def test_retired_filter_is_rejected_before_repair_lock(monkeypatch):
    country = {"column": "invoice.billing_country", "operator": "=", "value": "USA"}
    state = SessionState(
        session_id="patch-repair-fixture", scope={},
        original_question="查发票张数", effective_question="取消国家限制后查全部发票张数",
        intent=IntentContract(route="sql", task_type="aggregation", metric="invoice_count", intent_version=2),
        analysis=SemanticIntent(task_type="aggregation", metric="invoice_count"),
        resolutions=[{"previous_filters": [country], "patches": [{"op": "remove", "path": "filters", "value": [country]}]}],
    )
    decision = SimpleNamespace(level="ready", issues=[], assumptions=[], derived={})
    gate = SimpleNamespace(state=state, question=state.effective_question, card=None, decision=decision)
    monkeypatch.setattr("qa_agent.clarify.service.run_gate", lambda *args: gate)
    monkeypatch.setattr("qa_agent.clarify.service.public_metadata", lambda *args: {})
    monkeypatch.setattr("qa_agent.clarify.service.finish_gate", lambda *args, **kwargs: None)
    executed = []

    def execute(sql, *args, **kwargs):
        executed.append(sql)
        return SQLResult(columns=["n"], rows=[[412]], table=[{"n": 412}], row_count=1)

    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", execute)

    class Model:
        calls = 0

        def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
            self.calls += 1
            suffix = " WHERE billing_country='USA'" if self.calls == 1 else ""
            return response_model(sql="SELECT COUNT(invoice_id) AS n FROM invoice" + suffix,
                                  explanation="统计当前范围内发票数")

    model = Model()
    result = chat(ChatRequest(message="取消国家限制", session_id=state.session_id), llm=model,
                  settings=replace(get_settings(), nlu_enabled=False, sql_repair_attempts=2))
    assert result.status == "SUCCEEDED", result.error
    assert model.calls == 2
    assert len(executed) == 1 and "USA" not in executed[0]
    checks = [step for step in result.steps if step.name == "sql_current_contract_validate"]
    assert len(checks) == 2
    assert checks[0].status == "error" and checks[1].status == "ok"
    assert checks[1].output_summary["before_repair_filter_capture"] is True


def test_explicit_initial_primary_sort_checked_even_when_all_values_tie(monkeypatch):
    question = "按购买数量降序排名前3，返回编号和数量；并列按编号升序。"
    analysis = SemanticIntent(task_type="ranking", metric="purchased_quantity", rank_object="track", top_n=3,
                              order={"field": "purchased_quantity", "direction": "desc",
                                     "tie_breakers": [{"field": "track_id", "direction": "asc"}]})
    state = SessionState(session_id="initial-order-fixture", scope={}, original_question=question,
                         effective_question=question,
                         intent=IntentContract(route="sql", task_type="ranking", metric="purchased_quantity"),
                         analysis=analysis)
    gate = SimpleNamespace(state=state, question=question, card=None,
                           decision=SimpleNamespace(level="ready", issues=[], assumptions=[], derived={}))
    monkeypatch.setattr("qa_agent.clarify.service.run_gate", lambda *args: gate)
    monkeypatch.setattr("qa_agent.clarify.service.public_metadata", lambda *args: {})
    monkeypatch.setattr("qa_agent.clarify.service.finish_gate", lambda *args, **kwargs: None)
    executed = []

    def execute(sql, *args, **kwargs):
        executed.append(sql)
        # Both ordering variants happen to have identical rows when all
        # quantities tie; result EX alone cannot prove the declared main sort.
        return SQLResult(columns=["track_id", "quantity"], rows=[[1, 1], [2, 1], [3, 1]],
                         table=[{"track_id": i, "quantity": 1} for i in (1, 2, 3)], row_count=3)

    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", execute)

    class Model:
        calls = 0

        def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
            self.calls += 1
            sort = "track_id ASC" if self.calls == 1 else "SUM(quantity) DESC, track_id ASC"
            return response_model(sql="SELECT track_id, SUM(quantity) AS quantity FROM invoice_line "
                                  "GROUP BY track_id ORDER BY " + sort + " LIMIT 3", explanation="按当前排序返回前3")

    model = Model()
    result = chat(ChatRequest(message=question, session_id=state.session_id), llm=model,
                  settings=replace(get_settings(), nlu_enabled=False, sql_repair_attempts=2))
    assert result.status == "SUCCEEDED", result.error
    assert model.calls == 2 and len(executed) == 1
    assert "SUM" in executed[0] and "DESC" in executed[0]
    checks = [step for step in result.steps if step.name == "sql_current_contract_validate"]
    assert len(checks) == 2 and checks[0].status == "error" and checks[1].status == "ok"
