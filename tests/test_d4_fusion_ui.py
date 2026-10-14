"""AppTest UI fixtures, separate from live browser/model observations."""
from pathlib import Path
import httpx
import streamlit as st
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "ui/app.py"


def test_hybrid_source_shows_real_two_steps_and_does_not_call_again_on_rerender(monkeypatch):
    calls = []
    docs = [{"doc_id": "artist-iron-maiden", "title": "Iron Maiden简介", "format": "html", "ready": True,
             "entity_ref": "chinook:artist:90:Iron Maiden", "content_hash": "a" * 64}]
    def get(url, **kwargs):
        value = {"status": "ok", "database_ready": True, "llm_configured": True} if url.endswith("/health") else {"documents": docs}
        if url.endswith("/file"):
            return httpx.Response(200, content=b"source", request=httpx.Request("GET", url))
        return httpx.Response(200, json=value, request=httpx.Request("GET", url))
    def post(url, **kwargs):
        calls.append(kwargs["json"])
        assert calls[-1]["scope"]["route"] == "hybrid"
        value = {"trace_id": "d4-ui-hybrid-fixture", "status": "SUCCEEDED", "answer": "Iron Maiden [E1]",
            "sql": "SELECT artist_id FROM artist LIMIT 1", "table": [{"artist_id": 90}],
            "evidences": [{"evidence_id": "E1", "doc_id": "artist-iron-maiden", "doc_title": "Iron Maiden简介",
                           "section_path": ["公开背景"], "text": "重金属乐队"}],
            "metadata": {"fusion": {"kind": "sql_to_doc", "completed_stages": 2,
                "original_scope": calls[-1]["scope"], "plan_stages": ["数据库排名", "对应艺术家文档检索与回答"],
                "transferred_entity": {"artist_id": 90, "artist_name": "Iron Maiden"}}},
            "steps": [{"name": "fusion_entity_transfer", "status": "ok", "latency_ms": 1}]}
        return httpx.Response(200, json=value, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "get", get)
    monkeypatch.setattr(httpx, "post", post)
    st.cache_data.clear()
    app = AppTest.from_file(str(APP)).run()
    app.radio[0].set_value("数据库与文档").run()
    assert not app.exception and len(app.multiselect[0].options) == 1
    app.text_area[0].set_value("销售额最高的艺术家是谁？介绍音乐风格")
    next(button for button in app.button if button.label == "提交问题").click().run()
    assert not app.exception
    assert any("跨源执行" in item.value for item in app.markdown)
    assert any("数据库结果传给文档检索：Iron Maiden" in item.value for item in app.caption)
    assert len(app.expander) == 3 and len(calls) == 1
    app.toggle[0].set_value(True).run()
    assert not app.exception and len(calls) == 1
    st.cache_data.clear()


def test_schema_reason_and_disconnected_warning_use_response_metadata(monkeypatch):
    def get(url, **kwargs):
        value = {"status": "ok", "database_ready": True, "aw_database_ready": True} if url.endswith("/health") else {"documents": []}
        return httpx.Response(200, json=value, request=httpx.Request("GET", url))
    def post(url, **kwargs):
        value = {"trace_id": "d4-ui-pruning-fixture", "status": "SUCCEEDED", "answer": "SQL",
            "sql": "SELECT COUNT(*) FROM customer", "table": [{"n": 1}],
            "metadata": {"schema_linker": {"selected_tables": ["sales.customer"],
                "reasons": {"sales.customer": ["实际模型保留理由"]}, "excluded_tables": {"humanresources.employee": "实际排除理由"},
                "disconnected_components": [["sales.customer"], ["humanresources.employee"]]}}}
        return httpx.Response(200, json=value, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "get", get)
    monkeypatch.setattr(httpx, "post", post)
    st.cache_data.clear()
    app = AppTest.from_file(str(APP)).run()
    app.selectbox[0].set_value("AdventureWorks").run()
    app.text_area[0].set_value("客户数是多少")
    next(button for button in app.button if button.label == "提交问题").click().run()
    assert not app.exception
    assert any("所选表及理由" in item.value for item in app.markdown)
    assert any("不同关联分量" in item.value for item in app.warning)
    assert len(app.dataframe) == 3
    st.cache_data.clear()
