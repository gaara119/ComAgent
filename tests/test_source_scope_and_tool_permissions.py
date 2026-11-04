"""Offline tool-source authority, including saved-plan permission restoration."""
from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from qa_agent.config import get_settings
from qa_agent.context import RuntimeContext,bind_context
from qa_agent.schemas import AnswerEnvelope,ChatRequest,IntentContract
from qa_agent.trace import TraceRecorder

ROOT=Path(__file__).resolve().parents[1];DRAFT=ROOT/'qa_agent'

def load(monkeypatch,name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules,name,module);spec.loader.exec_module(module);return module

@pytest.fixture
def wired(monkeypatch):
    scope=load(monkeypatch,'qa_agent.source_scope',DRAFT/'source_scope.py')
    comp=load(monkeypatch,'qa_agent.fusion.composed',DRAFT/'fusion/composed.py')
    import qa_agent.fusion
    monkeypatch.setattr(qa_agent.fusion,'composed',comp,raising=False)
    monkeypatch.setattr(comp,'load_documents',lambda *a:[])
    from qa_agent.sql.catalog import load_catalog
    catalog=load_catalog(ROOT/'data/catalog/chinook.yaml')
    monkeypatch.setattr('qa_agent.sql.catalog.load_catalog',lambda *a:catalog)
    monkeypatch.setattr('qa_agent.sql.source_authority.validate_explicit_sources',lambda *a:[])
    monkeypatch.setattr('qa_agent.sql.source_authority.validate_composed_source_coverage',lambda *a:{'verified':True})
    monkeypatch.setattr('qa_agent.fusion.plan_contract.normalize_definition_plan',lambda q,p,a,**kw:(p,[]))
    class Store:
        saved=None
        written=None
        def load(self,*a,**kw):return self.saved
        def discard(self,*a):pass
        def save(self,req,ctx,data):self.written=data
    store=Store();monkeypatch.setattr(comp,'DEFAULT_COMPOSED_STORE',store)
    return scope,comp,store

class Planner:
    def __init__(self,comp,tools):self.comp=comp;self.tools=tools;self.calls=[]
    def complete_json(self,system,user,response_model,trace=None):
        self.calls.append(json.loads(user));assert response_model is self.comp.ToolPlan
        return self.comp.ToolPlan(steps=[{'step_id':'s'+str(i+1),'tool':t,'question':'本地离线工具问题'}for i,t in enumerate(self.tools)])

@pytest.mark.parametrize('question,mode',[
    ('只依据“这份会话正文”回答重点市场。','context_only'),
    ('只依据这份文档的正文解释客单价。','documents_only'),
    ('仅按指标手册中的客单价定义计算2025年美国客户客单价。','local_mixed'),
    ('仅按正文给的六国名单统计数据库发票。','local_mixed'),
    ('只依据这份正文回答，另外只用数据库回答。','conflict'),
])
def test_actual_source_phrases_and_local_definition_scope(wired,question,mode):
    result=wired[0].source_restriction(question);assert result.mode==mode,result
    for evidence in result.evidence:assert evidence in question

@pytest.mark.parametrize('allowed,bad',[({'context','doc'},'sql'),({'sql','doc'},'context')])
def test_forbidden_proposed_tool_is_rejected_before_any_tool(wired,monkeypatch,allowed,bad):
    scope,comp,store=wired;calls=[]
    def forbidden(*a,**kw):calls.append(True);raise AssertionError('forbidden tool reached')
    monkeypatch.setattr(comp,'_context_answer',forbidden)
    model=Planner(comp,[bad]);restriction=scope.SourceRestriction('allowed_set',allowed_tools=tuple(allowed))
    result=comp.run_composed(ChatRequest(message='只依据允许来源回答',scope={'route':'auto'}),TraceRecorder(),get_settings(),model,forbidden,source_contract=restriction)
    assert result.status=='FAILED'and '来源之外' in result.answer and not calls
    assert set(model.calls[0]['allowed_tools'])==allowed


def test_context_document_allowlist_can_execute_only_context_without_loading_SQL_catalog(wired,monkeypatch):
    scope,comp,store=wired;catalog=[]
    def forbidden(*a):catalog.append(True);raise AssertionError('SQL catalogue forbidden')
    monkeypatch.setattr('qa_agent.sql.catalog.load_catalog',forbidden)
    monkeypatch.setattr(comp,'_context_answer',lambda *a:{'answer':'仅本地真实正文引用','source':'user_session_context','quotes':[{'text':'定义','char_start':0}]})
    model=Planner(comp,['context'])
    result=comp.run_composed(ChatRequest(message='只依据这份正文和文档回答。'),TraceRecorder(),get_settings(),model,None,
        source_contract=scope.SourceRestriction('allowed_set',allowed_tools=('context','doc')))
    assert result.status=='SUCCEEDED'and result.intent.route=='doc'and not catalog
    assert result.metadata['source_scope']=='context'and result.evidences==[]and result.sql is None


def saved(comp,restriction,tools):
    return {'plan':{'steps':[{'step_id':'s'+str(i+1),'tool':tool,'question':'真实已保存问题'}for i,tool in enumerate(tools)]},
        'original_question':'只依据保存的允许来源回答','outputs':{},'evidences':[],'sql_results':[],
        'next_evidence_id':1,'next_index':0,'document_hashes':{},'clarification_id':'saved-card','intent_version':1,
        'source_restriction':restriction.public()}


def test_resume_restores_original_permissions_and_blocks_unallowed_cached_tool(wired):
    scope,comp,store=wired
    store.saved=saved(comp,scope.SourceRestriction('allowed_set',allowed_tools=('context','doc')),['sql'])
    calls=[]
    result=comp.run_composed(ChatRequest(message='按刚才说的',clarification_id='saved-card',intent_version=1),TraceRecorder(),get_settings(),None,lambda *a,**k:calls.append(True))
    assert result.status=='FAILED'and '来源之外'in result.answer and not calls


def test_new_restriction_cannot_resume_old_forbidden_tools(wired):
    scope,comp,store=wired
    store.saved=saved(comp,scope.SourceRestriction(),['sql'])
    calls=[]
    result=comp.run_composed(ChatRequest(message='按刚才说的',clarification_id='saved-card',intent_version=1),TraceRecorder(),get_settings(),None,lambda *a,**k:calls.append(True),
        source_contract=scope.SourceRestriction('allowed_set',allowed_tools=('context','doc')))
    assert result.status=='FAILED'and not calls


def test_source_contract_persists_when_actual_SQL_tool_needs_clarification(wired):
    scope,comp,store=wired
    restriction=scope.SourceRestriction('allowed_set',evidence=('只依据数据库和手册',),allowed_tools=('sql','doc'))
    def sql(req,trace,*args,**kw):
        return AnswerEnvelope(trace_id=trace.trace_id,status='NEEDS_CLARIFICATION',answer='本地缺少期间',
            clarification={'clarification_id':'new-card','intent_version':2})
    result=comp.run_composed(ChatRequest(message='只依据数据库和手册计算'),TraceRecorder(),get_settings(),Planner(comp,['sql']),sql,source_contract=restriction)
    assert result.status=='NEEDS_CLARIFICATION'
    assert store.written['source_restriction']==restriction.public()


def test_context_answer_payload_is_exact_source_not_history_or_clock(wired,monkeypatch):
    scope,comp,store=wired;brief='这是本会话实际提交的唯一样本文本。'
    ctx=RuntimeContext(session_id='offline014',reference_datetime='2026-10-15T00:00:00+08:00',timezone='Asia/Shanghai',
        text=brief,context_id='actual-context',content_sha256=sha256(brief.encode()).hexdigest(),
        history=[{'user':'旧问题','assistant':'虚构旧答案999','sql':'SELECT 999'}])
    class Model:
        def complete_json(self,system,user,model,trace=None):
            payload=json.loads(user)
            assert set(payload['context'])=={'passages','context_id','content_sha256'}
            assert ''.join(item['text'] for item in payload['context']['passages'])==brief
            return model(answer='来自本会话正文。',quotes=[brief])
    with bind_context(ctx):output=comp._context_answer('只依据正文回答',Model(),TraceRecorder())
    assert output['quotes']==[{'text':brief,'char_start':0,'char_end':len(brief)}]


def test_old_value_candidate_id_retires_with_old_field_reference(monkeypatch):
    helper=load(monkeypatch,'isolated_binding014',DRAFT/'clarify/binding_provenance.py')
    old={'column':'invoice.billing_country','operator':'=','value':'France','candidate_id':'old-billing-candidate',
        'evidence_ref':'old-billing-alias','source':'verified_value_index','method':'exact',
        'field_owner_proof':{'column':'invoice.billing_country','evidence':'法国发票'}}
    migrated,events=helper.migrate_region_bindings([old],'customer.country','按客户所在地国家',2,[old])
    binding=migrated[0]
    assert 'candidate_id'not in binding and binding['source']=='explicit_user_scope_change'
    assert binding['value_origin']['candidate_id']=='old-billing-candidate'
    assert binding['value_origin']['evidence_ref']=='old-billing-alias'
    assert binding['value_origin']['role']=='value_only_not_current_field_authorization'


@pytest.mark.parametrize('question',[
    '只依据这份正文中的客户名单，计算客户总数，不要调用其他工具或引用外部来源。',
    '只依据这份正文中的活跃客户定义计算2025年客户数，不要引用数据库或任何外部资料。',
])
def test_explicit_no_external_tools_has_priority_over_definition_inference(wired,question):
    restriction=wired[0].source_restriction(question)
    assert restriction.mode=='context_only'and restriction.allowed_tools==('context',)


@pytest.mark.parametrize('question',[
    '只依据这份正文中的客户名单，计算客户总数。',
    '仅按正文中的客户定义计算2025年客户数。',
])
def test_body_self_contained_calculation_does_not_authorize_database(wired,question):
    restriction=wired[0].source_restriction(question)
    assert restriction.mode=='context_only'and restriction.allowed_tools==('context',)


@pytest.mark.parametrize('question,tools',[
    ('只依据正文和数据库回答，但不要查询数据库。',{'context'}),
    ('只依据正文和数据库回答，但不要引用数据库。',{'context'}),
    ('只依据正文和所选文档回答，但不要引用所选文档。',{'context'}),
    ('只依据所选文档和数据库回答，但不要查询数据库。',{'doc'}),
    ('只依据正文和数据库回答，不要只查询数据库。',{'context','sql'}),
])
def test_specific_source_denials_reduce_allowed_upper_bound_without_negated_only(wired,question,tools):
    restriction=wired[0].source_restriction(question)
    assert set(restriction.allowed_tools)==tools,restriction


def test_restricted_nonSQL_planner_sees_only_actual_body_not_old_SQL_facts(wired,monkeypatch):
    scope,comp,store=wired;brief='本文只说明当前会话定义。'
    ctx=RuntimeContext(session_id='offline014',text=brief,context_id='ctx014',content_sha256='0'*64,
        reference_datetime='2026-10-15T00:00:00+08:00',timezone='Asia/Shanghai',
        history=[{'assistant':'旧SQL数字98765','sql':'SELECT 98765'}])
    monkeypatch.setattr(comp,'_context_answer',lambda *a:{'source':'user_session_context','answer':'实际正文内容'})
    model=Planner(comp,['context'])
    with bind_context(ctx):
        result=comp.run_composed(ChatRequest(message='只依据正文和文档回答。'),TraceRecorder(),get_settings(),model,None,
            source_contract=scope.SourceRestriction('allowed_set',allowed_tools=('context','doc')))
    assert result.status=='SUCCEEDED'
    assert set(model.calls[0]['session_context'])=={'user_brief','context_id','content_sha256'}
    assert '98765'not in json.dumps(model.calls[0],ensure_ascii=False)


@pytest.mark.parametrize('question,tools',[
    ('不要查询数据库，只依据正文回答。',{'context'}),
    ('不要查询数据库；请只依据正文回答。',{'context'}),
    ('不要看文档，只看正文回答。',{'context'}),
    ('只依据正文和数据库回答，但不要调用数据库。',{'context'}),
    ('只依据正文和数据库和文档回答，不要查询数据库和文档。',{'context'}),
    ('只依据正文和数据库回答，但不要只查询数据库。',{'context','sql'}),
])
def test_source_denial_objects_never_cross_clause_or_positive_predicate(wired,question,tools):
    restriction=wired[0].source_restriction(question)
    assert set(restriction.allowed_tools)==tools,restriction
