"""Exercise the demo's source routing and evidence interaction without model calls."""
from __future__ import annotations

import base64
from pathlib import Path

import httpx
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "ui" / "app.py"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jw1cAAAAASUVORK5CYII=")


@pytest.fixture
def api_mock(monkeypatch):
    calls = []
    documents = [{"doc_id": "annual-report", "title": "年度报告", "format": "pdf", "language": "zh", "page_count": 5, "content_hash": "fixture-hash", "ready": True}]
    def get(url, **kwargs):
        request = httpx.Request("GET", url)
        if url.endswith("/health"):
            return httpx.Response(200, json={"status": "ok", "stage": "D1", "database_ready": True, "llm_configured": True}, request=request)
        if url.endswith("/api/documents"):
            return httpx.Response(200, json={"documents": documents}, request=request)
        if "/pages/" in url:
            calls.append(("page", url))
            return httpx.Response(200, content=PNG, request=request)
        if url.endswith("/file"):
            return httpx.Response(200, content=b"%PDF-1.4 fixture", request=request)
        return httpx.Response(404, request=request)
    def post(url, *, json, **kwargs):
        calls.append(("chat", json))
        result = {"trace_id": "fixture-trace", "status": "SUCCEEDED", "answer": "测试回答", "metadata": {"latency_ms": 123}, "steps": [{"name": "route", "status": "ok", "latency_ms": 1}]}
        if json["scope"]["route"] == "sql":
            result.update(sql='SELECT COUNT(*) FROM "customer"', table=[{"customer_count": 59}])
        else:
            result.update(answer="报告内容见 [E1]。", evidences=[{"evidence_id": "E1", "doc_id": "annual-report", "doc_title": "年度报告", "page": 3, "text": "测试原文：收入保持增长。", "section_path": ["经营情况"]}])
        return httpx.Response(200, json=result, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "get", get)
    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setenv("QA_API_BASE_URL", "http://127.0.0.1:8000")
    st.cache_data.clear()
    yield calls
    st.cache_data.clear()


def test_sql_form_uses_shared_api_contract(api_mock):
    app = AppTest.from_file(str(APP)).run(timeout=15)
    assert not app.exception
    app.text_area[0].set_value("客户共有多少位？")
    app.button[0].click().run(timeout=15)
    assert not app.exception
    payload = next(value for kind, value in api_mock if kind == "chat")
    assert payload["scope"] == {"route": "sql", "db_id": "chinook", "doc_ids": []}
    assert payload["message"] == "客户共有多少位？"
    assert len(app.dataframe) == 1
    assert any('COUNT(*)' in item.value for item in app.code)
    assert [panel.label for panel in app.expander] == ["SQL 与结果", "引用来源", "处理步骤与耗时"]
    assert any("数据库：chinook" in item.value for item in app.caption)
    assert len(app.expander[0].get("dataframe")) == 1
    assert any("本次查询没有文档引用" in item.value for item in app.caption)


def test_doc_form_shows_actual_evidence_page_and_clears_old_scope(api_mock):
    app = AppTest.from_file(str(APP)).run(timeout=15)
    app.text_area[0].set_value("客户共有多少位？")
    app.button[0].click().run(timeout=15)
    app.radio[0].set_value("指定文档").run(timeout=15)
    assert not app.dataframe  # A SQL answer cannot be mistaken for a document answer.
    assert [panel.label for panel in app.expander] == ["SQL 与结果", "引用来源", "处理步骤与耗时"]
    assert not app.code
    assert not any("数据库：chinook" in item.value for item in app.caption)
    app.text_area[0].set_value("报告的经营情况是什么？")
    app.button[0].click().run(timeout=15)
    assert not app.exception
    payload = [value for kind, value in api_mock if kind == "chat"][-1]
    assert payload["scope"] == {"route": "doc", "db_id": None, "doc_ids": ["annual-report"]}
    assert any("测试原文" in element.value for element in app.text)
    assert any(url.endswith("/pages/3") for kind, url in api_mock if kind == "page")
    assert any("#page=3" in element.value for element in app.markdown)
    assert [panel.label for panel in app.expander] == ["SQL 与结果", "引用来源", "处理步骤与耗时"]
    assert any("本次文档查询未执行数据库 SQL" in item.value for item in app.caption)
    assert any("测试原文" in element.value for element in app.expander[1].get("text"))
    reference = next(button for button in app.button if button.label.startswith("[E1]"))
    reference.click().run(timeout=15)
    assert not app.exception
    assert len([value for kind, value in api_mock if kind == "chat"]) == 2


@pytest.mark.parametrize("source", ["数据库", "指定文档"])
def test_idle_source_has_three_panels_without_invented_results(api_mock, source):
    app = AppTest.from_file(str(APP)).run(timeout=15)
    if source == "指定文档":
        app.radio[0].set_value(source).run(timeout=15)
    assert not app.exception
    assert [panel.label for panel in app.expander] == ["SQL 与结果", "引用来源", "处理步骤与耗时"]
    assert not app.code
    assert not app.dataframe
    assert not app.text
    assert not any("请求编号：" in item.value for item in app.caption)
    assert not any(kind == "chat" for kind, value in api_mock)


def test_blank_question_does_not_send_a_model_request(api_mock):
    app = AppTest.from_file(str(APP)).run(timeout=15)
    app.button[0].click().run(timeout=15)
    assert not app.exception
    assert any("请先输入问题" in item.value for item in app.warning)
    assert not any(kind == "chat" for kind, value in api_mock)
