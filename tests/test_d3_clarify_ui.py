"""Check actual Streamlit resume controls without pretending mocked answers are EX."""
from pathlib import Path

import httpx
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from qa_agent.schemas import ChatRequest

APP=Path(__file__).resolve().parents[1]/'ui/app.py'
pytestmark=pytest.mark.skipif('clarification_id' not in ChatRequest.model_fields,
                            reason='D3 shared UI integration is pending; current D2 source is preserved')


def pending():
    return {'trace_id':'ui-d3-pending','status':'NEEDS_CLARIFICATION','answer':'请明确年份。',
            'clarification':{'clarification_id':'card-one','intent_version':1,'level':'L2',
                'question':'请明确当前比较期间。','reason':'没有年度默认。','resume_supported':True,
                'options':[{'id':'year:2024','label':'2024年'}]},'metadata':{'clarify':{'level':'L2','intent_version':1}}}


def succeeded(version=2, switches=False):
    value={'trace_id':'ui-d3-answer-'+str(version),'status':'SUCCEEDED','answer':'查询结果：5。',
           'sql':'SELECT COUNT(*) AS n FROM customer','table':[{'n':5}],
           'metadata':{'clarify':{'level':'L0','intent_version':version,'assumptions':[]}}}
    if switches:
        value['metadata']['clarify']={'level':'L1' if version==1 else 'L0','intent_version':version,
            'assumptions':['热门曲目按购买数量统计（已确认默认口径）。'] if version==1 else [],
            'switch':{'clarification_id':'switch-'+str(version),'intent_version':version,'options':[
                {'id':'by_quantity','label':'按购买数量'},{'id':'by_revenue','label':'按销售额'}]}}
    return value


def app_fixture(monkeypatch,responses):
    calls=[]
    def get(url,**kwargs):
        data={'status':'ok','stage':'D3','llm_configured':True,'database_ready':True,'aw_database_ready':True} if url.endswith('/health') else {'documents':[]}
        return httpx.Response(200,json=data,request=httpx.Request('GET',url))
    def post(url,**kwargs):
        calls.append(kwargs['json'])
        result=responses[len(calls)-1]
        return httpx.Response(200,json=result,request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx,'get',get);monkeypatch.setattr(httpx,'post',post)
    st.cache_data.clear()
    app=AppTest.from_file(str(APP)).run()
    app.text_area[0].set_value('发票销售额同比增长多少？')
    app.button[0].click().run()
    return app,calls


def test_option_button_sends_trusted_card_id_version_and_session_once(monkeypatch):
    app,calls=app_fixture(monkeypatch,[pending(),succeeded()])
    next(button for button in app.button if button.label=='2024年').click().run()
    assert not app.exception and len(calls)==2
    assert calls[1]['clarification_id']=='card-one' and calls[1]['intent_version']==1
    assert calls[1]['choice_id']=='year:2024' and calls[1]['session_id']==calls[0]['session_id']
    assert 'patches' not in calls[1] and 'expected_level' not in calls[1]
    app.run()
    assert len(calls)==2
    st.cache_data.clear()


def test_free_input_sends_actual_message_and_same_card_version(monkeypatch):
    app,calls=app_fixture(monkeypatch,[pending(),succeeded()])
    next(item for item in app.text_input if item.label=='补充说明').set_value('2024年')
    next(button for button in app.button if button.label=='提交补充').click().run()
    assert not app.exception and len(calls)==2
    assert calls[1]['message']=='2024年' and calls[1]['clarification_id']=='card-one'
    assert calls[1]['intent_version']==1 and calls[1].get('choice_id') is None
    st.cache_data.clear()


def test_l1_metric_can_switch_twice_with_new_version(monkeypatch):
    app,calls=app_fixture(monkeypatch,[succeeded(1,True),succeeded(2,True),succeeded(3,True)])
    next(button for button in app.button if button.label=='切换：按销售额').click().run()
    assert len(calls)==2 and calls[-1]['intent_version']==1
    next(button for button in app.button if button.label=='切换：按购买数量').click().run()
    assert not app.exception and len(calls)==3 and calls[-1]['intent_version']==2
    assert calls[-1]['clarification_id']=='switch-2' and calls[-1]['choice_id']=='by_quantity'
    st.cache_data.clear()


def test_country_label_uses_confirmed_source_even_when_result_alias_is_old_name(monkeypatch):
    result=succeeded()
    result['sql']='SELECT c.country AS billing_country FROM customer c'
    result['table']=[{'billing_country':'Canada'}]
    result['metadata']['clarify']['region_scope']='customer.country'
    app,calls=app_fixture(monkeypatch,[result])
    assert not app.exception and len(calls)==1
    assert any(item.value=='当前国家口径：客户所在地（customer.country）' for item in app.caption)
    st.cache_data.clear()
