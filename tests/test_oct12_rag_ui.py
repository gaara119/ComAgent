"""Oct 12 safeguards; fixtures are module/UI tests, not live model results."""
from pathlib import Path

import httpx
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from qa_agent.rag.answer import CitationError, DocumentAnswer, answer_from_chunks, citation_coverage_diagnostics
from qa_agent.schemas import AnswerEnvelope, IntentContract
from qa_agent.trace import TraceRecorder
import ui.app as ui_app
from ui.app import clarification_reason, result_display_table, rewrite_explanation


APP = Path(ui_app.__file__)


def chunk(text="Revenue 1234", evidence_id="E1"):
    return {"evidence_id": evidence_id, "doc_id": "doc", "doc_title": "Document", "page": 1,
            "section_path": [], "text": text, "bbox": None}


class RepeatedAnswer:
    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    def complete_json(self, *args):
        self.calls += 1
        return self.answer.model_copy(deep=True)


def test_unverified_numeric_body_keeps_actual_citations_and_never_a_third_generation():
    model = RepeatedAnswer(DocumentAnswer(status="SUCCEEDED", answer="Revenue 9999 [E1]", citation_ids=["E1"]))
    trace = TraceRecorder()
    answer, used = answer_from_chunks("revenue", [chunk()], model, trace)
    assert model.calls == 2
    assert answer.answer.startswith("【未核实】") and "Revenue 9999 [E1]" in answer.answer
    assert answer._validation_warnings[0]["validation_attempts"] == 2
    assert used == [chunk()]
    assert len([s for s in trace.steps if s.name == "rag_regenerate"]) == 1
    assert any(s.name == "rag_unverified" and s.status == "warn" for s in trace.steps)
    # Model-facing JSON cannot manufacture local verification results.
    assert "_validation_warnings" not in DocumentAnswer.model_json_schema()["properties"]
    assert "_validation_warnings" not in answer.model_dump()


def test_unverified_number_rule_cannot_bypass_forged_source_ids():
    model = RepeatedAnswer(DocumentAnswer(status="SUCCEEDED", answer="9999 [E99]", citation_ids=["E99"]))
    with pytest.raises(CitationError) as exc:
        answer_from_chunks("revenue", [chunk()], model, TraceRecorder())
    assert model.calls == 2 and exc.value.code == "rag_citation_invalid"


def test_numeric_failure_does_not_mask_unsupported_attribution():
    model = RepeatedAnswer(DocumentAnswer(status="SUCCEEDED", answer="Forbes reported revenue 9999 [E1]",
                                         citation_ids=["E1"]))
    with pytest.raises(CitationError) as exc:
        answer_from_chunks("revenue", [chunk()], model, TraceRecorder())
    assert model.calls == 2 and exc.value.code == "rag_attribution_invalid"


def test_local_unverified_notice_does_not_count_as_an_uncited_document_claim():
    model = RepeatedAnswer(DocumentAnswer(status="SUCCEEDED", answer="Revenue 9999 [E1]", citation_ids=["E1"]))
    answer, _ = answer_from_chunks("revenue", [chunk()], model, TraceRecorder())
    assert citation_coverage_diagnostics(answer)["potential_uncited_statement_count"] == 0
    answer.answer += "\nThe company has another unsupported business claim."
    assert citation_coverage_diagnostics(answer)["potential_uncited_statement_count"] == 1


def test_service_returns_unverified_metadata_and_cited_evidence(monkeypatch):
    import qa_agent.rag.service as service
    import qa_agent.documents as documents
    from qa_agent.config import Settings
    monkeypatch.setattr(service, "get_settings", lambda: Settings(db_url="", rag_answer_mode="llm"))
    monkeypatch.setattr(service, "load_documents", lambda path: [
        {"doc_id": "doc", "title": "Document", "content_hash": "fixture", "language": "en"}])
    monkeypatch.setattr(documents, "verify_document_hash", lambda document: None)
    monkeypatch.setattr(service, "retrieve", lambda *args, **kwargs: ([{**chunk(), "chunk_id": "one", "score": 1}], {}))
    model = RepeatedAnswer(DocumentAnswer(status="SUCCEEDED", answer="Revenue 9999 [E1]", citation_ids=["E1"]))
    monkeypatch.setattr(service, "JsonLLM", lambda settings: model)
    result = service.run_doc_qa(question="revenue", doc_id="doc", trace_id="oct12-unit-rag",
                                intent=IntentContract(route="doc"))
    assert result.status == "SUCCEEDED" and result.error is None
    assert result.metadata["validation_status"] == "unverified"
    assert result.metadata["validation_retries"] == 1
    assert result.metadata["faithfulness_uncertain"] is True
    assert result.metadata["semantic_faithfulness"] == "not_verified"
    assert result.metadata["warnings"][0]["code"] == "rag_number_invalid"
    assert result.evidences[0].text == "Revenue 1234"


def test_rewrite_description_uses_real_stage_score_without_internal_candidate_id():
    patch = {"original": "巴稀", "replacement": "Brazil", "method": "pinyin", "evidence_ref": "v-95ff"}
    nlu = {"mentions": [{"original_text": "巴稀", "canonical_value": "Brazil", "selected_candidate_id": "v-95ff",
                         "candidates": [{"candidate_id": "v-95ff", "score": .97}]}]}
    assert rewrite_explanation(patch, nlu) == "巴稀 → Brazil（拼音匹配 0.97）"
    # A missing score must stay missing rather than copying the plan's example.
    assert rewrite_explanation(patch, {}) == "巴稀 → Brazil（拼音匹配）"
    assert clarification_reason("候选关系获准不等于允许自动绑定；请明确本次筛选。") == (
        "这个名称可能指不同对象，请选择本次查询所指的对象。")


def result(table, task="lookup", formatting=None, sql=None):
    return AnswerEnvelope(trace_id="oct12-ui-unit", status="SUCCEEDED", answer="result", table=table,
                          intent=IntentContract(route="sql", task_type=task),
                          metadata={"result_format": formatting or {}}, sql=sql)


def test_percentage_display_preserves_raw_results_and_handles_scales_nulls_negative():
    raw = [{"share": "0.04216533923932024362", "growth_rate": -.25, "amount": 1234, "unknown": None}]
    answer = result(raw, formatting={"share": {"kind": "percentage", "scale": 100},
                                    "growth_rate": {"kind": "percentage", "scale": 100},
                                    "unknown": {"kind": "percentage", "scale": 100}})
    assert result_display_table(answer) == [{"share": "4.22%", "growth_rate": "-25.00%", "amount": 1234, "unknown": None}]
    assert answer.table == raw
    assert result_display_table(result([{"pct": 4.22}], formatting={"pct": {"kind": "percentage", "scale": 1}})) == [{"pct": "4.22%"}]


def test_legacy_percentage_inference_uses_sql_scale_and_never_guesses_missing_sql():
    raw = [{"ratio": .1, "sales_amount": 100, "invoice_count": 2}]
    assert result_display_table(result(raw)) == raw
    assert result_display_table(result(raw, task="ratio")) == raw
    sql = "SELECT SUM(total) / 1000 AS ratio, SUM(total) AS sales_amount, COUNT(*) AS invoice_count FROM invoice"
    # A model alias and task tag do not establish that literal1000 is an
    # authorized total/budget in the same unit. Keep the original legacy SQL
    # as a negative regression, rather than inventing percentage semantics.
    assert result_display_table(result(raw, task="ratio", sql=sql)) == raw
    # Explicit unknown format must not be overridden by a compatibility guess.
    assert result_display_table(result(raw, task="ratio", sql=sql, formatting={"ratio": {"kind": "number"}})) == raw
    scaled = "SELECT SUM(total) * 100 / 1000 AS ratio FROM invoice"
    assert result_display_table(result([{"ratio": 10}], task="ratio", sql=scaled)) == [{"ratio": 10}]
    ratio = "SUM(CASE WHEN billing_country='Brazil' THEN total END) / NULLIF(SUM(total),0)"
    proved = f"SELECT {ratio} AS ratio, SUM(total) AS sales_amount, COUNT(*) AS invoice_count FROM invoice"
    assert result_display_table(result(raw, task="ratio", sql=proved)) == [{"ratio": "10.00%", "sales_amount": 100, "invoice_count": 2}]
    assert result_display_table(result(raw, task="ratio", sql=proved, formatting={"ratio": {"kind": "number"}})) == raw
    for actual_scaled_ratio in (f"100 * ({ratio})", "SUM(CASE WHEN billing_country='Brazil' THEN total END) * 100 / NULLIF(SUM(total),0)"):
        sql = f"SELECT {actual_scaled_ratio} AS ratio FROM invoice"
        assert result_display_table(result([{"ratio": 10}], task="ratio", sql=sql)) == [{"ratio": "10.00%"}]
    denominator_scaled = "SELECT SUM(CASE WHEN billing_country='Brazil' THEN total END) / NULLIF(SUM(total)*100,0) AS ratio FROM invoice"
    assert result_display_table(result([{"ratio": .1}], task="ratio", sql=denominator_scaled)) == [{"ratio": .1}]
    assert raw == [{"ratio": .1, "sales_amount": 100, "invoice_count": 2}]


def test_ui_shows_unverified_warning_and_percentages_without_requery(monkeypatch):
    calls = []
    def get(url, **kwargs):
        data = {"status": "ok", "database_ready": True} if url.endswith("/health") else {"documents": []}
        return httpx.Response(200, json=data, request=httpx.Request("GET", url))
    def post(url, **kwargs):
        calls.append(kwargs["json"])
        payload = result([{"ratio": .042165, "sales_amount": 1234}], task="ratio").model_dump()
        payload.update(answer="【未核实】示例回答。", sql="SELECT 0.042165 AS ratio, 1234 AS sales_amount")
        payload["metadata"].update(faithfulness_uncertain=True, result_format={"ratio": {"kind": "percentage", "scale": 100}})
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "get", get)
    monkeypatch.setattr(httpx, "post", post)
    st.cache_data.clear()
    try:
        app = AppTest.from_file(str(APP)).run()
        app.text_area[0].set_value("占比是多少？")
        app.button[0].click().run()
        assert not app.exception
        assert any("未核实" in warning.value for warning in app.warning)
        assert app.dataframe[0].value.iloc[0]["ratio"] == "4.22%"
        assert app.dataframe[0].value.iloc[0]["sales_amount"] == 1234
        app.run()
        assert len(calls) == 1
    finally:
        st.cache_data.clear()
