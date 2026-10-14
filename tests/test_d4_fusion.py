"""D4 module fixtures; these are not live API/model accuracy measurements."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from qa_agent.config import PROJECT_ROOT, Settings
from qa_agent.fusion import planner
from qa_agent.rag.answer import DocumentAnswer
from qa_agent.schemas import AnswerEnvelope, ChatRequest, IntentContract, SourceScope
from qa_agent.schemas import SQLGeneration
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import SQLValidationError
from qa_agent.trace import TraceRecorder


CATALOG = load_catalog(PROJECT_ROOT / "data/catalog/chinook.yaml")
ARTIST_SQL = """SELECT a.artist_id AS artist_id, a.name AS artist_name,
SUM(il.unit_price * il.quantity) AS sales_amount FROM public.artist a
JOIN public.album al ON al.artist_id=a.artist_id
JOIN public.track t ON t.album_id=al.album_id
JOIN public.invoice_line il ON il.track_id=t.track_id
GROUP BY a.artist_id,a.name ORDER BY sales_amount DESC,a.artist_id ASC LIMIT 1"""
AVG_SQL = "SELECT AVG(i.total) AS average_invoice_amount FROM public.invoice i"


@pytest.fixture(autouse=True)
def isolate_plans():
    planner._PLANS.clear()
    yield
    planner._PLANS.clear()


def request(question, docs=None, session="fusion-test", **kwargs):
    return ChatRequest(session_id=session, message=question,
                       scope=SourceScope(route="hybrid", db_id="chinook", doc_ids=docs or []), **kwargs)


def chunk(text, doc_id="project-metric-manual"):
    return {"evidence_id": "E1", "doc_id": doc_id, "doc_title": "真实来源",
            "section_path": ["指标定义"], "page": None, "bbox": None, "text": text,
            "chunk_id": "source-chunk", "score": 1}


def document(doc_id="project-metric-manual", entity="chinook:business-metrics"):
    return {"doc_id": doc_id, "title": "真实来源", "entity_ref": entity,
            "content_hash": "a" * 64, "format": "docx", "ingestion_status": "prepared"}


@pytest.mark.parametrize("question,kind", [
    ("销售额最高的艺术家是谁？介绍一下他的音乐风格。", "sql_to_doc"),
    ("2024年销售额最高的艺术家是谁？介绍背景。", "sql_to_doc"),
    ("按口径手册客单价的定义，计算2024年美国客户的客单价。", "doc_to_sql"),
    ("客户有多少？", "unsupported"),
])
def test_explicit_bounded_route(question, kind):
    assert planner.classify_route(request(question)) == kind


def test_auto_plain_source_and_no_gold_dependency():
    assert planner.classify_route(ChatRequest(message="客户有多少", scope=SourceScope(route="auto"))) == "sql"
    assert planner.classify_route(ChatRequest(message="文档说什么", scope=SourceScope(route="auto", doc_ids=["d"]))) == "doc"


def test_artist_sql_plan_proves_actual_top1_and_ids():
    planner.validate_fusion_sql(ARTIST_SQL, CATALOG, {"kind": "sql_to_doc"})
    planner.validate_fusion_sql(ARTIST_SQL.replace("ORDER BY sales_amount DESC", "ORDER BY SUM(il.unit_price*il.quantity) DESC"),
                                CATALOG, {"kind": "sql_to_doc"})


@pytest.mark.parametrize("sql", [
    ARTIST_SQL.replace("LIMIT 1", "LIMIT 10"),
    ARTIST_SQL.replace("a.artist_id AS artist_id", "90 AS artist_id"),
    ARTIST_SQL.replace("a.name AS artist_name", "'Iron Maiden' AS artist_name"),
    ARTIST_SQL.replace("il.unit_price * il.quantity", "il.unit_price"),
    ARTIST_SQL.replace("sales_amount DESC,a.artist_id ASC", "a.artist_id DESC,a.artist_id ASC"),
    ARTIST_SQL.replace("sales_amount DESC,a.artist_id ASC", "sales_amount DESC"),
    ARTIST_SQL.replace("GROUP BY", "WHERE a.artist_id=90 GROUP BY"),
])
def test_artist_guard_rejects_fake_or_incorrect_transferred_entity(sql):
    with pytest.raises(SQLValidationError):
        planner.validate_fusion_sql(sql, CATALOG, {"kind": "sql_to_doc"})


def avg_context(aggregate="AVG"):
    return {"kind": "doc_to_sql", "definition": {"aggregate": aggregate, "column": "invoice.total"}}


def test_document_expression_actually_controls_query_guard():
    planner.validate_fusion_sql(AVG_SQL, CATALOG, avg_context())
    with pytest.raises(SQLValidationError):
        planner.validate_fusion_sql(AVG_SQL.replace("AVG", "SUM"), CATALOG, avg_context())
    # Same generic guard would accept SUM only when the extracted plan says SUM.
    # Production additionally checks that the manual agrees with approved rules.
    planner.validate_fusion_sql(AVG_SQL.replace("AVG", "SUM"), CATALOG, avg_context("SUM"))


@pytest.mark.parametrize("sql", [
    "SELECT SUM(total)/COUNT(DISTINCT customer_id) FROM public.invoice",
    "SELECT AVG(unit_price) FROM public.invoice_line",
    "SELECT COALESCE(AVG(total),0) FROM public.invoice",
    "SELECT customer_id, AVG(total) FROM public.invoice GROUP BY customer_id",
    "SELECT AVG(i.total) FROM public.invoice i JOIN public.invoice j ON j.customer_id=i.customer_id",
    "SELECT AVG(total)+100 FROM public.invoice",
    "SELECT AVG(total)*100 FROM public.invoice",
    "SELECT CAST(AVG(total) AS INTEGER) FROM public.invoice",
    "SELECT ROUND(AVG(total),0) FROM public.invoice",
    "SELECT AVG(total),42 FROM public.invoice",
    "SELECT CAST(AVG(total) AS DECIMAL(12,0)) FROM public.invoice",
])
def test_document_guard_preserves_approved_grain_and_nulls(sql):
    with pytest.raises(SQLValidationError):
        planner.validate_fusion_sql(sql, CATALOG, avg_context())


def test_document_guard_allows_only_amount_presentation_without_new_algorithm():
    planner.validate_fusion_sql("SELECT ROUND(AVG(total),2) FROM public.invoice", CATALOG, avg_context())
    planner.validate_fusion_sql("SELECT CAST(AVG(total) AS DECIMAL(12,2)) FROM public.invoice", CATALOG, avg_context())


def test_artist_document_mapping_requires_id_name_and_scope():
    docs = [document("right", "chinook:artist:90:Iron Maiden"),
            document("wrong-id", "chinook:artist:50:Iron Maiden"),
            document("wrong-name", "chinook:artist:90:Metallica")]
    assert [d["doc_id"] for d in planner._artist_documents(docs, 90, "Iron Maiden", [])] == ["right"]
    assert planner._artist_documents(docs, 90, "Iron Maiden", ["wrong-id"]) == []


def test_missing_winner_document_keeps_database_proof_and_never_calls_another_doc(monkeypatch):
    monkeypatch.setattr(planner, "load_documents", lambda *a: [document("artist-u2", "chinook:artist:150:U2")])
    monkeypatch.setattr(planner, "retrieve", lambda *a, **k: pytest.fail("No matching artist means no retrieval"))
    calls = []
    def sql_runner(req, trace, settings, llm, generation_context):
        calls.append(req)
        assert req.scope.route == "hybrid" and "前1名" in req.message
        planner.validate_fusion_sql(ARTIST_SQL, CATALOG, generation_context)
        return AnswerEnvelope(trace_id=trace.trace_id, status="SUCCEEDED", answer="SQL",
            sql=ARTIST_SQL, table=[{"artist_id": 90, "artist_name": "Iron Maiden", "sales_amount": "100"}],
            intent=IntentContract(route="sql", task_type="ranking"))
    result = planner.run_hybrid(request("销售额最高的艺术家是谁？介绍他的音乐风格"), TraceRecorder(),
                                Settings(db_url=""), object(), sql_runner)
    assert result.status == "EMPTY_RESULT" and result.sql == ARTIST_SQL
    assert result.metadata["fusion"]["transferred_entity"]["artist_name"] == "Iron Maiden"
    assert result.evidences == [] and "没有该艺术家" in result.answer
    assert len(calls) == 1


def test_retrieved_definition_quote_reaches_sql_generation_and_is_cited(monkeypatch):
    source = "本项目客单价指平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。"
    doc = document()
    monkeypatch.setattr(planner, "load_documents", lambda *a: [doc])
    monkeypatch.setattr(planner, "verify_document_hash", lambda *a: None)
    monkeypatch.setattr(planner, "retrieve", lambda *a, **k: ([chunk(source)], {"candidate_count": 1}))
    class Model:
        def complete_json(self, system, user, response_model, trace):
            assert source in json.loads(user)["evidences"][0]["text"]
            return planner.MetricDefinition(metric_name="平均每张发票金额", aggregate="AVG", column="invoice.total",
                grain="invoice", unit="数据库金额单位", evidence_id="E1", definition_quote=source)
    context_seen = []
    def sql_runner(req, trace, settings, llm, generation_context):
        context_seen.append(generation_context)
        planner.validate_fusion_sql(AVG_SQL, CATALOG, generation_context)
        return AnswerEnvelope(trace_id=trace.trace_id, status="SUCCEEDED", answer="查询结果：5。", sql=AVG_SQL,
                              table=[{"average_invoice_amount": "5"}], intent=IntentContract(route="sql"))
    result = planner.run_hybrid(request("按口径手册定义计算2024年美国客户的客单价"), TraceRecorder(),
                                Settings(db_url=""), Model(), sql_runner)
    assert result.status == "SUCCEEDED"
    assert context_seen[0]["definition"]["definition_quote"] == source
    assert result.evidences[0].text == source and "[E1]" in result.answer
    assert result.metadata["fusion"]["definition_used_in_generation"] is True


@pytest.mark.parametrize("quote,aggregate,column", [
    ("编造的完整定义AVG(invoice.total)，每张发票权重相同。", "AVG", "invoice.total"),
    ("本项目客单价指平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。", "SUM", "invoice.total"),
    ("本项目客单价指平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。", "AVG", "invoice.unknown"),
])
def test_unsubstantiated_document_definition_stops_before_sql(monkeypatch, quote, aggregate, column):
    source = "本项目客单价指平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。"
    monkeypatch.setattr(planner, "load_documents", lambda *a: [document()])
    monkeypatch.setattr(planner, "verify_document_hash", lambda *a: None)
    monkeypatch.setattr(planner, "retrieve", lambda *a, **k: ([chunk(source)], {}))
    class Model:
        def complete_json(self, *a, **k):
            return planner.MetricDefinition(metric_name="客单价", aggregate=aggregate, column=column,
                grain="invoice", unit="金额单位", evidence_id="E1", definition_quote=quote)
    result = planner.run_hybrid(request("按口径手册定义计算2024年美国客户的客单价"), TraceRecorder(),
        Settings(db_url=""), Model(), lambda *a, **k: pytest.fail("Invalid source must not generate or execute SQL"))
    assert result.status == "FAILED"


def test_clarification_resume_reuses_definition_and_original_scope(monkeypatch):
    source = "本项目客单价指平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。"
    req = request("按口径手册定义计算美国客户某年的客单价")
    definition = planner.MetricDefinition(metric_name="客单价", aggregate="AVG", column="invoice.total",
        grain="invoice", unit="金额单位", evidence_id="E1", definition_quote=source)
    context, evidences = planner._definition_context(definition, [chunk(source)], CATALOG, Settings(db_url=""), document())
    planner._remember(req, planner.StoredPlan("doc_to_sql", req.scope.model_dump(mode="json"), req.message, req.message, context, evidences))
    monkeypatch.setattr(planner, "load_documents", lambda *a: [document()])
    monkeypatch.setattr(planner, "verify_document_hash", lambda *a: None)
    monkeypatch.setattr(planner, "retrieve", lambda *a, **k: pytest.fail("No repeated definition retrieval on resume"))
    def sql_runner(subrequest, trace, settings, llm, generation_context):
        assert subrequest.scope == req.scope and subrequest.message == "2024年"
        assert subrequest.clarification_id == "card"
        return AnswerEnvelope(trace_id=trace.trace_id, status="SUCCEEDED", answer="5", sql=AVG_SQL,
                              intent=IntentContract(route="sql", intent_version=2))
    result = planner.run_hybrid(request("2024年", session=req.session_id, clarification_id="card", intent_version=1),
                                TraceRecorder(), Settings(db_url=""), object(), sql_runner)
    assert result.status == "SUCCEEDED" and result.intent.route == "hybrid"
    assert result.evidences and any(s.name == "fusion_resume" for s in result.steps)


@pytest.mark.parametrize("sql,should_execute", [(AVG_SQL, True), (AVG_SQL.replace("AVG", "SUM"), False)])
def test_integrated_sql_pipeline_sends_definition_and_validates_before_execution(monkeypatch, sql, should_execute):
    import qa_agent.clarify.service as service
    import qa_agent.sql.executor as executor
    from qa_agent.pipeline import _sql
    intent = IntentContract(route="sql", metric="average_invoice_amount")
    analysis = SimpleNamespace(time_scope=None, task_type="aggregate", region_scope=None, order=None)
    state = SimpleNamespace(intent=intent, analysis=analysis, bindings=[], original_question="发票平均金额是多少",
                            invalidated=[], resolutions=[])
    decision = SimpleNamespace(level="L0", issues=[], assumptions=[], derived={})
    gate = SimpleNamespace(state=state, decision=decision, question=state.original_question, card=None)
    monkeypatch.setattr(service, "run_gate", lambda *a, **k: gate)
    monkeypatch.setattr(service, "finish_gate", lambda *a, **k: None)
    monkeypatch.setattr(service, "public_metadata", lambda *a: {})
    executions, prompts = [], []
    def execute(*a, **kwargs):
        executions.append(a[0])
        return SimpleNamespace(columns=["average_invoice_amount"], rows=[["5"]], row_count=1,
                               table=[{"average_invoice_amount": "5"}], truncated=False)
    monkeypatch.setattr(executor, "execute_sql", execute)
    class Model:
        def complete_json(self, system_prompt, user_prompt, response_model, trace):
            prompts.append(json.loads(user_prompt))
            return SQLGeneration(sql=sql, tables_used=["invoice"])
    trace = TraceRecorder()
    context = avg_context()
    result = _sql(request(state.original_question), trace,
                  Settings(db_url="fixture", nlu_enabled=False, sql_repair_attempts=0), Model(),
                  generation_context=context)
    assert prompts[0]["verified_fusion_context"] == context
    assert bool(executions) is should_execute
    assert result.status == ("SUCCEEDED" if should_execute else "FAILED")
    guard = next(step for step in trace.steps if step.name == "fusion_plan_validate")
    assert guard.status == ("ok" if should_execute else "error")
