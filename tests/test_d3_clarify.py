"""Rule/state safety checks; these scripted labels are not a model benchmark."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from qa_agent.clarify.extractor import extract_intent
from qa_agent.clarify.rules import RuleEngine, SemanticIntent, derive_base, explicit_period
from qa_agent.clarify.service import _ground_patch_filters, run_gate
from qa_agent.clarify.state import (IntentPatch, SessionConflict, SessionStore, apply_choice,
                                    apply_patches, prepare_card, transition, verify_resume)
from qa_agent.nlu.linker import LinkResult, LinkedMention
from qa_agent.schemas import ChatRequest
from qa_agent.sql.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]


def no_link(question="q"):
    return LinkResult(question, question, [], [], [])


def request(message, session="test", **extra):
    base = ChatRequest(message=message, session_id=session)
    return SimpleNamespace(message=base.message, session_id=base.session_id, scope=base.scope,
                           clarification_id=None, intent_version=None, choice_id=None, **extra)


def test_complete_growth_is_l0_and_calendar_base_is_derived():
    result = RuleEngine().evaluate("2024年账单国家为美国的发票销售额同比", SemanticIntent(
        task_type="growth", metric="invoice_revenue", time_scope=explicit_period("2024年"), comparison={"type":"yoy"}))
    assert result.level == "L0"
    assert result.analysis.time_scope["base"]["start"] == "2023-01-01"
    assert result.analysis.time_scope["base"]["end"] == "2024-01-01"


def test_missing_year_is_never_filled_by_available_year_options():
    result = RuleEngine().evaluate("发票销售额同比", SemanticIntent(task_type="growth", metric="invoice_revenue", comparison={"type":"yoy"}), available_years=[2021,2025])
    assert result.level == "L2" and result.analysis.time_scope is None
    assert [item["id"] for item in result.issues[0].options] == ["year:2021","year:2025"]
    assert all("不代表完整年度" in item["label"] for item in result.issues[0].options)


def test_popularity_default_is_scoped_to_tracks_and_not_comparisons():
    engine = RuleEngine()
    popular = SemanticIntent(task_type="ranking", rank_object="track", top_n=5, time_scope=explicit_period("2024年"))
    assert engine.evaluate("2024年最热门5首曲目", popular).level == "L1"
    assert engine.evaluate("2024年最热门5首曲目", popular).analysis.metric == "purchased_quantity"
    object_free = SemanticIntent(task_type="ranking", time_scope=explicit_period("2024年"), top_n=5)
    assert engine.evaluate("2024年谁买得最多", object_free).level == "L2"
    comparison = SemanticIntent(task_type="growth", rank_object="track", time_scope=explicit_period("2024年"), comparison={"type":"yoy"})
    assert engine.evaluate("2024年最热门曲目同比", comparison).level == "L2"
    assert engine.evaluate("2024年最热门曲目同比", comparison).analysis.metric is None


def test_missing_period_and_undated_playlist_switch_pause():
    engine = RuleEngine()
    missing = SemanticIntent(task_type="ranking", rank_object="track", top_n=5)
    assert engine.evaluate("最热门5首曲目", missing).level == "L2"
    snapshot = SemanticIntent(task_type="ranking", rank_object="track", metric="playlist_memberships", top_n=5,
                              time_scope=explicit_period("2024年"))
    result = engine.evaluate("2024年最热门5首曲目", snapshot)
    assert result.level == "L2" and result.issues[0].id == "unsupported:playlist_period"


def test_billing_and_customer_countries_remain_distinct():
    result = RuleEngine().evaluate("2024年美国发票销售额", SemanticIntent(metric="invoice_revenue", region_ambiguous=True))
    assert result.level == "L2"
    assert {item["patch"]["value"] for item in result.issues[0].options} == {"invoice.billing_country","customer.country"}


@pytest.mark.parametrize("text", ["0000年1月", "9999年12月", "2024年0月", "2024年13月"])
def test_invalid_calendar_text_is_rejected_without_exception(text):
    assert explicit_period(text) is None


def test_year_one_cannot_derive_year_zero():
    assert derive_base({"start":"0001-01-01","end":"0002-01-01"}, "yoy") is None


def test_state_persists_hash_paths_and_rejects_stale_card(tmp_path):
    store = SessionStore(tmp_path)
    state = store.start("../bad-path", {"route":"sql","db_id":"chinook","doc_ids":[]}, "销售额同比", SemanticIntent(task_type="growth", metric="invoice_revenue", comparison={"type":"yoy"}))
    card = prepare_card(state, RuleEngine().evaluate(state.original_question, state.analysis, available_years=[2024]))
    store.save(state)
    restored = SessionStore(tmp_path).get(state.session_id)
    assert restored.phase == "WAITING_CLARIFICATION" and store.path(state.session_id).parent == tmp_path
    assert verify_resume(restored, card["clarification_id"], 1, state.scope)
    apply_choice(restored, restored.pending_card, "year:2024")
    assert restored.intent.intent_version == 2
    with pytest.raises(SessionConflict, match="失效"):
        verify_resume(restored, card["clarification_id"], 1, state.scope)


def test_region_patch_preserves_period_and_metric_and_invalidates_only_results(tmp_path):
    store = SessionStore(tmp_path)
    binding = {"column":"customer.country","operator":"=","value":"Brazil"}
    state = store.start("s", {}, "2024年巴西客户数量", SemanticIntent(metric="customer_count", time_scope=explicit_period("2024年"),filters=[binding]), [binding])
    prepare_card(state, RuleEngine().evaluate(state.original_question, state.analysis))
    transition(state,"ANSWERED")
    changed = {**binding, "value":"Canada"}
    apply_patches(state,[IntentPatch(op="set",path="filters",value=[changed],evidence="加拿大")], user_message="改成加拿大")
    assert state.analysis.metric == "customer_count"
    assert state.analysis.time_scope["current"]["start"] == "2024-01-01"
    assert state.invalidated == ["result"]


def test_metric_patch_invalidates_schema_but_preserves_region_period(tmp_path):
    binding={"column":"invoice.billing_country","operator":"=","value":"Canada"}
    state=SessionStore(tmp_path).start("s",{},"2024年加拿大发票金额",SemanticIntent(metric="invoice_revenue",time_scope=explicit_period("2024年"),filters=[binding]),[binding])
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,"ANSWERED")
    apply_patches(state,[IntentPatch(op="set",path="metric",value="average_invoice_amount",evidence="客单价")],user_message="换成客单价")
    assert state.bindings == [binding] and state.analysis.time_scope["current"]["start"] == "2024-01-01"
    assert {"schema","grain","aggregation","fields","result"} <= set(state.invalidated)


def test_time_patch_removes_derived_base_before_recalculation(tmp_path):
    analysis=SemanticIntent(task_type="growth",metric="invoice_revenue",time_scope=explicit_period("2024年"),comparison={"type":"yoy"})
    state=SessionStore(tmp_path).start("s",{},"销售额同比",analysis)
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,"ANSWERED")
    apply_patches(state,[IntentPatch(op="set",path="time_scope",value=explicit_period("2023年"),evidence="2023年")],user_message="改成2023年")
    assert "base" not in state.analysis.time_scope
    result=RuleEngine().evaluate(state.original_question,state.analysis)
    assert result.analysis.time_scope["base"]["start"] == "2022-01-01"


def test_filter_grounding_rejects_operator_flip_and_unrelated_condition_loss(tmp_path):
    old={"column":"customer.country","operator":"=","value":"Brazil"}
    name={"column":"customer.first_name","operator":"=","value":"Luis"}
    state=SessionStore(tmp_path).start("s",{},"客户",SemanticIntent(filters=[old,name]),[old,name])
    with pytest.raises(SessionConflict,match="真实值链接"):
        _ground_patch_filters([IntentPatch(op="set",path="filters",value=[{**old,"operator":"!="},name])],state,no_link())
    new={**old,"value":"Canada"}
    linked=no_link();linked.bindings=[new]
    with pytest.raises(SessionConflict,match="丢失"):
        _ground_patch_filters([IntentPatch(op="set",path="filters",value=[new])],state,linked)


def test_one_value_selection_preserves_other_unresolved_values(tmp_path):
    mention1=LinkedMention("mention-1","摇滚",[0,2],"ambiguous",["genre.name"],candidates=[
        {"candidate_id":"rock","column":"genre.name","standard_value":"Rock"},
        {"candidate_id":"roll","column":"genre.name","standard_value":"Rock And Roll"}])
    mention2=LinkedMention("mention-2","AAC",[3,6],"ambiguous",["media_type.name"],candidates=[
        {"candidate_id":"aac1","column":"media_type.name","standard_value":"AAC audio file"},
        {"candidate_id":"aac2","column":"media_type.name","standard_value":"Protected AAC audio file"}])
    linked=LinkResult("摇滚 AAC曲目","摇滚 AAC曲目",[mention1,mention2],[],[])
    class Model:
        def complete_json(self,*args,**kwargs):return SemanticIntent()
    store=SessionStore(tmp_path)
    first=run_gate(request("摇滚 AAC曲目"),load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(),linked,store=store)
    option=first.card["options"][0]["id"]
    resumed=request("Rock")
    resumed.clarification_id=first.card["clarification_id"];resumed.intent_version=1;resumed.choice_id=option
    second=run_gate(resumed,load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(),no_link(),store=store)
    assert second.decision.level=="L2" and len(second.state.unresolved_values)==1
    assert second.state.unresolved_values[0]["original_text"]=="AAC"
    assert second.state.bindings[0]["value"]=="Rock"


def test_new_question_does_not_inherit_a_previous_country(tmp_path):
    store=SessionStore(tmp_path)
    store.start("s",{},"巴西客户",SemanticIntent(),[{"column":"customer.country","operator":"=","value":"Brazil"}])
    new=store.start("s",{},"全部客户",SemanticIntent())
    assert new.bindings==[] and new.intent.intent_version==2


@pytest.mark.parametrize("question",["最近完整年度的发票金额是多少？","最近一年的发票金额是多少？","这期间的发票金额是多少？"])
def test_model_cannot_invent_a_year_for_vague_date_words(question):
    class Model:
        def complete_json(self,*args,**kwargs):
            return SemanticIntent(metric="invoice_revenue",time_scope=explicit_period("2025年"))
    result=extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),Model())
    assert result.time_scope is None
    if "最近" in question:assert result.time_ambiguous


def test_user_requested_data_latest_year_is_labeled_as_record_year_not_complete():
    class Model:
        def complete_json(self,*args,**kwargs):return SemanticIntent(metric="invoice_revenue")
    result=extract_intent("数据中最近有记录的年份的发票金额是多少？",load_catalog(ROOT/'data/catalog/chinook.yaml'),Model())
    assert result.time_scope["current"]["start"]=="2025-01-01"
    assert any("不代表完整年度" in item for item in result.assumptions)


def test_data_latest_year_phrase_does_not_choose_calendar_over_rolling_year():
    class Model:
        def complete_json(self,*args,**kwargs):return SemanticIntent(metric="invoice_revenue",time_scope=explicit_period("2025年"))
    result=extract_intent("数据中最近一年的发票金额是多少？",load_catalog(ROOT/'data/catalog/chinook.yaml'),Model())
    assert result.time_scope is None and result.time_ambiguous


def test_day_range_and_multiple_months_are_not_overwritten_as_whole_year():
    period=explicit_period("2024年1月1日到2024年3月31日的发票金额")
    assert period['current']['start']=='2024-01-01' and period['current']['end']=='2024-04-01'
    assert period['current']['grain']=='custom'
    assert explicit_period('2024年1月到2024年3月的发票金额') is None


def test_conflicting_year_question_uses_actual_semantic_model():
    class Model:
        called=0
        def complete_json(self,*args,**kwargs):
            self.called+=1
            return SemanticIntent(metric='invoice_revenue',conflicts=['2024年与2023年冲突'])
    model=Model()
    question='统计2024年的发票销售额，但日期必须从2023年1月1日到2023年12月31日。'
    result=extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),model)
    assert model.called==1 and RuleEngine().evaluate(question,result).level=='L2'


def test_metric_switch_can_switch_back_and_confirmed_choice_is_not_a_default(tmp_path):
    store=SessionStore(tmp_path)
    state=store.start('s',{},'2024年最受欢迎5首曲目',SemanticIntent(task_type='ranking',rank_object='track',top_n=5,time_scope=explicit_period('2024年')))
    first=RuleEngine().evaluate(state.original_question,state.analysis)
    assert first.level=='L1'
    prepare_card(state,first);transition(state,'ANSWERED')
    original_card=state.switch_card.copy()
    apply_choice(state,state.switch_card,'by_revenue')
    second=RuleEngine().evaluate(state.original_question,state.analysis)
    assert second.level=='L0' and second.analysis.metric=='detail_revenue'
    assert not second.analysis.default_assumptions
    prepare_card(state,second);transition(state,'ANSWERED')
    assert state.switch_card and state.switch_card['intent_version']==2
    with pytest.raises(SessionConflict):verify_resume(state,original_card['clarification_id'],1,state.scope)
    apply_choice(state,state.switch_card,'by_quantity')
    third=RuleEngine().evaluate(state.original_question,state.analysis)
    assert third.level=='L0' and third.analysis.metric=='purchased_quantity'
    assert any('用户已选择热门曲目口径：按购买数量。'==text for text in third.assumptions)
    assert not any('用户已选择热门曲目口径：按销售额。'==text for text in third.assumptions)


def test_customer_metric_patch_removes_old_amount_default(tmp_path):
    state=SessionStore(tmp_path).start('s',{},'2024年客户谁买得最多',SemanticIntent(task_type='ranking',rank_object='customer',top_n=3,time_scope=explicit_period('2024年')))
    first=RuleEngine().evaluate(state.original_question,state.analysis)
    prepare_card(state,first);transition(state,'ANSWERED')
    assert any('发票金额' in text for text in state.analysis.assumptions)
    apply_patches(state,[IntentPatch(op='set',path='metric',value='average_invoice_amount',evidence='客单价')],user_message='改为客单价')
    assert not any('谁买得最多' in text for text in state.analysis.assumptions)


def test_country_field_change_invalidates_schema_but_preserves_value_period_metric(tmp_path):
    binding={'column':'invoice.billing_country','operator':'=','value':'Brazil'}
    state=SessionStore(tmp_path).start('s',{},'2024年巴西发票金额',SemanticIntent(metric='invoice_revenue',time_scope=explicit_period('2024年'),region_scope='invoice.billing_country',filters=[binding]),[binding])
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,'ANSWERED')
    apply_patches(state,[IntentPatch(op='set',path='region_scope',value='customer.country',evidence='客户所在地')],user_message='改为按客户所在地')
    assert state.bindings[0]['column']=='customer.country' and state.bindings[0]['value']=='Brazil'
    assert state.analysis.metric=='invoice_revenue' and state.analysis.time_scope['current']['start']=='2024-01-01'
    assert {'fields','schema','result'}<=set(state.invalidated)


def test_model_guessing_popular_measure_does_not_hide_registered_l1_default():
    class Model:
        def complete_json(self,*args,**kwargs):
            return SemanticIntent(task_type='ranking',rank_object='track',top_n=5,metric='purchased_quantity')
    question='2024年最受欢迎的5首曲目是哪些？'
    analysis=extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),Model())
    assert analysis.metric is None and RuleEngine().evaluate(question,analysis).level=='L1'


def test_explicit_wrong_yoy_base_is_a_conflict_instead_of_silent_substitution():
    semantic=SemanticIntent(task_type='growth',metric='invoice_revenue',time_scope={**explicit_period('2024年'),'base':{'start':'2022-01-01','end':'2023-01-01'}},comparison={'type':'yoy'})
    decision=RuleEngine().evaluate('2024年相比2022年同比',semantic)
    assert decision.level=='L2' and decision.analysis.time_scope['base']['start']=='2022-01-01'


def test_new_explicit_custom_base_survives_patch_and_sort_patch_preserves_conditions(tmp_path):
    binding={'column':'invoice.billing_country','operator':'=','value':'Brazil'}
    state=SessionStore(tmp_path).start('s',{},'2024年巴西发票金额',SemanticIntent(metric='invoice_revenue',time_scope=explicit_period('2024年'),filters=[binding]),[binding])
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,'ANSWERED')
    period={**explicit_period('2024年'),'base':{'start':'2022-01-01','end':'2023-01-01'}}
    apply_patches(state,[IntentPatch(op='set',path='time_scope',value=period,evidence='2022年'),IntentPatch(op='set',path='comparison',value={'type':'custom'},evidence='2022年')],user_message='比较2022年')
    assert state.analysis.time_scope['base']['start']=='2022-01-01'
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,'ANSWERED')
    apply_patches(state,[IntentPatch(op='set',path='order',value={'field':'invoice.total','direction':'asc'},evidence='升序')],user_message='改为升序')
    assert state.intent.order['direction']=='asc' and state.bindings==[binding]
    assert state.invalidated==['result']


def test_invoice_country_binding_is_not_proof_of_user_billing_scope(tmp_path):
    class Model:
        calls=0
        def complete_json(self,*args,**kwargs):
            self.calls+=1
            return SemanticIntent(metric='invoice_revenue',region_scope='invoice.billing_country')
    binding={'column':'invoice.billing_country','operator':'=','value':'USA'}
    linked=no_link();linked.bindings=[binding]
    model=Model()
    gate=run_gate(request('2024年美国发票金额'),load_catalog(ROOT/'data/catalog/chinook.yaml'),model,linked,store=SessionStore(tmp_path))
    assert model.calls==1 and gate.decision.level=='L2'
    assert gate.state.analysis.region_scope is None


def test_explicit_customer_country_scope_aligns_binding_and_stays_l0(tmp_path):
    class Model:
        def complete_json(self,*args,**kwargs):return SemanticIntent(metric='invoice_revenue')
    linked=no_link();linked.bindings=[{'column':'invoice.billing_country','operator':'=','value':'USA'}]
    gate=run_gate(request('2024年客户所在地国家为USA的发票金额'),load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(),linked,store=SessionStore(tmp_path))
    assert gate.decision.level=='L0' and gate.state.bindings[0]['column']=='customer.country'
    assert gate.state.analysis.time_scope['current']['start']=='2024-01-01'


def test_explicit_change_to_country_scope_is_recognized_as_existing_task_followup():
    from qa_agent.clarify.service import is_followup
    assert is_followup('改按客户所在地统计，其他条件保持不变。')
    assert not is_followup('2024年按客户所在地统计加拿大的发票总额。')


def test_country_scope_change_preserves_unrelated_employee_country_filter(tmp_path):
    billing={'column':'invoice.billing_country','operator':'=','value':'Canada'}
    employee={'column':'employee.country','operator':'=','value':'USA'}
    state=SessionStore(tmp_path).start('s',{},'2024年美国员工所服务的加拿大发票金额',
        SemanticIntent(metric='invoice_revenue',time_scope=explicit_period('2024年'),region_scope='invoice.billing_country',filters=[billing,employee]),[billing,employee])
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,'ANSWERED')
    apply_patches(state,[IntentPatch(op='set',path='region_scope',value='customer.country',evidence='客户所在地')],user_message='改按客户所在地')
    assert employee in state.bindings
    assert {'column':'customer.country','operator':'=','value':'Canada'} in state.bindings
    assert not any(item.get('column')=='customer.country' and item.get('value')=='USA' for item in state.bindings)


def test_public_card_omits_executable_patches_even_inside_nested_issues(tmp_path):
    state=SessionStore(tmp_path).start('s',{},'发票总额同比',SemanticIntent(task_type='growth',metric='invoice_revenue',comparison={'type':'yoy'}))
    decision=RuleEngine().evaluate(state.original_question,state.analysis,available_years=[2024])
    card=prepare_card(state,decision)
    assert card and card['options'] and card['issues']
    assert all('patch' not in option for option in card['options'])
    assert all('patch' not in option for issue in card['issues'] for option in issue['options'])
    assert all('patch' in option for option in state.pending_card['trusted_options'])


def test_explicit_chinese_object_is_canonicalized_without_inventing_missing_object():
    class Model:
        def __init__(self,object_name):self.object_name=object_name
        def complete_json(self,*args,**kwargs):
            return SemanticIntent(task_type='ranking',rank_object=self.object_name,top_n=5)
    catalog=load_catalog(ROOT/'data/catalog/chinook.yaml')
    question='2024年最受欢迎的5首曲目是哪些？'
    semantic=extract_intent(question,catalog,Model('曲目'))
    assert semantic.rank_object=='track' and RuleEngine().evaluate(question,semantic).level=='L1'
    missing=extract_intent('2024年谁买得最多？',catalog,Model(None))
    assert missing.rank_object is None and RuleEngine().evaluate('2024年谁买得最多？',missing).level=='L2'


def test_followup_uses_confirmed_field_scope_but_only_new_country_text(tmp_path):
    from qa_agent.clarify.service import mentions_for_linking
    from qa_agent.nlu.value_index import ValueIndex,ValueRecord,record_id
    from qa_agent.nlu.linker import ValueLinker
    from qa_agent.config import Settings
    index=ValueIndex([ValueRecord(record_id(column,value),column,value,surface,'test-fixture')
        for column,value,surface in [('invoice.billing_country','USA','美国'),('invoice.billing_country','Canada','加拿大'),
                                     ('customer.country','USA','美国'),('customer.country','Canada','加拿大')]])
    store=SessionStore(tmp_path)
    scope=ChatRequest(message='q').scope.model_dump(mode='json')
    old={'column':'invoice.billing_country','operator':'=','value':'USA'}
    store.start('test',scope,'2024年美国发票总额',SemanticIntent(filters=[old],time_scope=explicit_period('2024年')),[old])
    req=request('改成加拿大，其他条件保持不变。')
    mentions=mentions_for_linking(req,index,store)
    linked=ValueLinker(index,Settings(db_url='')).link(req.message,mentions=mentions)
    assert len(linked.bindings)==1 and linked.bindings[0]['column']=='invoice.billing_country'
    assert linked.bindings[0]['operator']=='=' and linked.bindings[0]['value']=='Canada'
    assert all(item.original_text=='加拿大' for item in linked.mentions)
    assert 'USA' not in linked.rewritten_question


def test_explicit_scope_patch_allows_retained_country_value_only_and_preserves_employee(tmp_path):
    from qa_agent.clarify.service import extract_patches
    from qa_agent.clarify.state import PatchResponse
    billing={'column':'invoice.billing_country','operator':'=','value':'Canada'}
    employee={'column':'employee.country','operator':'=','value':'USA'}
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent(filters=[billing,employee]),[billing,employee])
    class Model:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='set',path='region_scope',value='customer.country',evidence='客户所在地'),
            IntentPatch(op='set',path='filters',value=[{**billing,'column':'customer.country'},employee],evidence='客户所在地')])
    patches=extract_patches('改按客户所在地统计',state,no_link(),Model())
    assert patches[1].value[0]['value']=='Canada' and employee in patches[1].value
    with pytest.raises(SessionConflict):
        _ground_patch_filters([IntentPatch(op='set',path='filters',value=[{**billing,'column':'customer.country','operator':'!='},employee])],state,no_link(),derived_scope='customer.country')
    with pytest.raises(SessionConflict):
        _ground_patch_filters([IntentPatch(op='set',path='filters',value=[{**billing,'column':'customer.country','value':'Brazil'},employee])],state,no_link(),derived_scope='customer.country')


def test_model_cannot_change_country_field_from_value_only_evidence(tmp_path):
    from qa_agent.clarify.service import extract_patches
    from qa_agent.clarify.state import PatchResponse
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent())
    class Model:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='set',path='region_scope',value='customer.country',evidence='加拿大')])
    with pytest.raises(SessionConflict):extract_patches('改成加拿大',state,no_link(),Model())


def test_explicit_period_overrides_only_known_nested_current_paths(tmp_path):
    from qa_agent.clarify.service import extract_patches
    from qa_agent.clarify.state import PatchResponse
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent())
    class Model:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='set',path='time_scope.current',value={'start':'2023-01-01'},evidence='2023年')])
    patches=extract_patches('改成2023年',state,no_link(),Model())
    assert not any(patch.path=='time_scope.current' for patch in patches)
    assert next(patch.value for patch in patches if patch.path=='time_scope')['current']['end']=='2024-01-01'
    class Illegal:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='set',path='time_scope.unreviewed_field',value='x',evidence='2023年')])
    illegal=extract_patches('改成2023年',state,no_link(),Illegal())
    with pytest.raises(SessionConflict):apply_patches(state,illegal,user_message='改成2023年')


def test_multiple_confirmed_country_fields_do_not_pick_or_change_both_from_value_only(tmp_path):
    from qa_agent.clarify.service import mentions_for_linking
    from qa_agent.nlu.value_index import ValueIndex,ValueRecord,record_id
    from qa_agent.nlu.linker import ValueLinker
    from qa_agent.config import Settings
    index=ValueIndex([ValueRecord(record_id(column,'Canada'),column,'Canada','加拿大','test-fixture')
        for column in ('customer.country','invoice.billing_country')])
    store=SessionStore(tmp_path)
    scope=ChatRequest(message='q').scope.model_dump(mode='json')
    old=[{'column':'invoice.billing_country','operator':'=','value':'USA'},
         {'column':'customer.country','operator':'=','value':'Brazil'}]
    state=store.start('test',scope,'q',SemanticIntent(filters=old),old)
    req=request('改成加拿大')
    linked=ValueLinker(index,Settings(db_url='')).link(req.message,mentions=mentions_for_linking(req,index,store))
    assert not linked.bindings and linked.ambiguous and len(linked.ambiguous[0].candidates)==2
    assert state.bindings==old
    with pytest.raises(SessionConflict):_ground_patch_filters([IntentPatch(op='set',path='filters',value=[{**item,'value':'Canada'} for item in old])],state,linked)


def test_explicit_country_scope_cannot_merge_two_independent_existing_country_conditions(tmp_path):
    old=[{'column':'invoice.billing_country','operator':'=','value':'USA'},
         {'column':'customer.country','operator':'=','value':'Brazil'}]
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent(filters=old),old)
    with pytest.raises(SessionConflict):apply_patches(state,[IntentPatch(op='set',path='region_scope',value='customer.country',evidence='客户所在地')],user_message='改按客户所在地')
    assert state.bindings==old and state.intent.intent_version==1


def test_scope_migration_model_remove_old_field_does_not_delete_confirmed_value(tmp_path):
    from qa_agent.clarify.service import extract_patches
    from qa_agent.clarify.state import PatchResponse
    billing={'column':'invoice.billing_country','operator':'=','value':'Canada','evidence_ref':'verified'}
    employee={'column':'employee.country','operator':'=','value':'USA'}
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent(filters=[billing,employee],time_scope=explicit_period('2024年')),[billing,employee])
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,'ANSWERED')
    class Model:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='set',path='region_scope',value='customer.country',evidence='客户所在地'),
            IntentPatch(op='remove',path='filters',value=billing,evidence='客户所在地')])
    patches=extract_patches('改按客户所在地统计，其他条件保持不变',state,no_link(),Model())
    assert len(patches)==1 and patches[0].path=='region_scope'
    apply_patches(state,patches,user_message='改按客户所在地统计，其他条件保持不变')
    assert {**billing,'column':'customer.country'} in state.bindings and employee in state.bindings
    assert state.analysis.time_scope['current']['start']=='2024-01-01'


@pytest.mark.parametrize('message',['改成2023年','不要取消账单国家限制'])
def test_unrequested_or_negated_filter_removal_is_rejected(tmp_path,message):
    from qa_agent.clarify.service import extract_patches
    from qa_agent.clarify.state import PatchResponse
    billing={'column':'invoice.billing_country','operator':'=','value':'Canada'}
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent(filters=[billing]),[billing])
    class Model:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='remove',path='filters',value=billing,evidence=message)])
    with pytest.raises(SessionConflict):extract_patches(message,state,no_link(),Model())
    assert state.bindings==[billing]


def test_cancel_named_country_condition_preserves_independent_employee_filter(tmp_path):
    from qa_agent.clarify.service import extract_patches
    from qa_agent.clarify.state import PatchResponse
    billing={'column':'invoice.billing_country','operator':'=','value':'Canada','evidence_ref':'verified'}
    employee={'column':'employee.country','operator':'=','value':'USA'}
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent(filters=[billing,employee]),[billing,employee])
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis));transition(state,'ANSWERED')
    class Model:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='remove',path='filters',value={key:billing[key] for key in ('column','operator','value')},evidence='取消账单国家限制')])
    patches=extract_patches('取消账单国家限制，保留员工条件',state,no_link(),Model())
    apply_patches(state,patches,user_message='取消账单国家限制，保留员工条件')
    assert state.bindings==[employee]


def test_cancel_one_named_condition_cannot_delete_other_employee_country(tmp_path):
    from qa_agent.clarify.service import extract_patches
    from qa_agent.clarify.state import PatchResponse
    billing={'column':'invoice.billing_country','operator':'=','value':'Canada'}
    employee={'column':'employee.country','operator':'=','value':'USA'}
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent(filters=[billing,employee]),[billing,employee])
    class Model:
        def complete_json(self,*args,**kwargs):return PatchResponse(patches=[
            IntentPatch(op='remove',path='filters',value=[billing,employee],evidence='取消账单国家限制')])
    with pytest.raises(SessionConflict):extract_patches('取消账单国家限制，保留员工条件',state,no_link(),Model())
    assert state.bindings==[billing,employee]


@pytest.mark.parametrize('metric,expected',[('invoice_revenue','L0'),(None,'L2')])
def test_trusted_year_choice_resolves_period_ambiguity_but_preserves_other_missing_fields(tmp_path,metric,expected):
    state=SessionStore(tmp_path).start('s',{},'发票同比增长多少',
        SemanticIntent(task_type='growth',metric=metric,comparison={'type':'yoy'},time_ambiguous=True))
    first=RuleEngine().evaluate(state.original_question,state.analysis,available_years=[2024])
    card=prepare_card(state,first)
    assert first.level=='L2' and any(issue.id=='ambiguous:time_scope' for issue in first.issues)
    apply_choice(state,state.pending_card,'year:2024')
    assert not state.analysis.time_ambiguous
    second=RuleEngine().evaluate(state.original_question,state.analysis,available_years=[2024])
    assert second.level==expected and second.analysis.time_scope['current']['start']=='2024-01-01'
    assert second.analysis.time_scope['base']['start']=='2023-01-01'
    if metric is None:assert any(issue.id=='missing:metric' for issue in second.issues)


def test_invalid_trusted_calendar_choice_does_not_clear_ambiguity_or_modify_version(tmp_path):
    state=SessionStore(tmp_path).start('s',{},'q',SemanticIntent(time_ambiguous=True))
    card={'trusted_options':[{'id':'bad-period','label':'无效日期','patch':{'op':'set','path':'time_scope','value':{'current':{'start':'2024-13-01','end':'2025-01-01'}}}}]}
    with pytest.raises(SessionConflict):apply_choice(state,card,'bad-period')
    assert state.analysis.time_ambiguous and state.intent.intent_version==1 and state.analysis.time_scope is None


def test_explicit_playlist_snapshot_cancellation_keeps_its_confirmation_note(tmp_path):
    state=SessionStore(tmp_path).start('s',{},'2024年最受欢迎5首曲目',SemanticIntent(
        task_type='ranking',rank_object='track',top_n=5,metric='playlist_memberships',time_scope=explicit_period('2024年')))
    first=RuleEngine().evaluate(state.original_question,state.analysis)
    prepare_card(state,first)
    apply_choice(state,state.pending_card,'playlist_snapshot')
    assert state.analysis.time_scope is None
    assert '用户明确取消期间约束，歌单次数按当前收录快照统计。' in state.analysis.assumptions
