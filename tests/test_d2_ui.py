from pathlib import Path
import httpx
import streamlit as st
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/"ui/app.py"


def test_each_real_step_can_expand_and_redraw_does_not_request_model(monkeypatch):
    calls=[]
    def get(url,**kwargs):
        value={"status":"ok","llm_configured":True} if url.endswith("/health") else {"documents":[]}
        return httpx.Response(200,json=value,request=httpx.Request("GET",url))
    def post(url,**kwargs):
        calls.append(kwargs["json"])
        value={"trace_id":"d2-ui-fixture","status":"SUCCEEDED","answer":"查询结果：5。", "sql":"SELECT COUNT(*) FROM customer",
               "table":[{"n":5}],"rewritten_question":"来自 Brazil 的客户有多少位？",
               "metadata":{"nlu":{"original_question":"来自Brasil的客户有多少位？", "patches":[
                   {"original":"Brasil","replacement":"Brazil","method":"fuzzy","evidence_ref":"v-test"}]}},
               "steps":[{"name":"value_link_fuzzy","status":"ok","latency_ms":17,
                          "output_summary":{"selected_value":"Brazil","system_prompt":"full prompt must be hidden"}},
                        {"name":"rewrite_optional","status":"skipped","latency_ms":0,"output_summary":{"reason":"not required"}}]}
        return httpx.Response(200,json=value,request=httpx.Request("POST",url))
    monkeypatch.setattr(httpx,"get",get)
    monkeypatch.setattr(httpx,"post",post)
    st.cache_data.clear()
    app=AppTest.from_file(str(APP)).run()
    app.text_area[0].set_value("来自Brasil的客户有多少位？")
    app.button[0].click().run()
    assert not app.exception
    assert len(app.expander)==3
    assert len(app.toggle)==2
    assert any("Brasil → Brazil" in item.value for item in app.text)
    app.toggle[0].set_value(True).run()
    assert not app.exception and len(calls)==1
    assert any("selected_value" in item.value for item in app.code)
    assert not any("full prompt must be hidden" in item.value for item in app.code)
    assert any("未执行" in item.value for item in app.markdown)
    st.cache_data.clear()
