"""D4 patch safety tests: scripted model proposals, never benchmark predictions."""
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from qa_agent.clarify.extractor import extract_intent
from qa_agent.clarify.rules import SemanticIntent, explicit_period, RuleEngine
from qa_agent.clarify.service import extract_patches, run_gate, finish_gate, public_metadata, is_followup, execution_question
from qa_agent.clarify.state import SessionStore, IntentPatch, PatchResponse, apply_patches
from qa_agent.nlu.linker import LinkResult, LinkedMention
from qa_agent.schemas import ChatRequest
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import validate_value_bindings, SQLValidationError
from qa_agent.clarify.sql_guard import validate_current_patch_contract

ROOT=Path(__file__).resolve().parents[1]
CATALOG=load_catalog(ROOT/'data/catalog/chinook.yaml')


def linked(message,field=None,value=None):
    if field is None:
        return LinkResult(message,message,[],[],[])
    text='德国' if value=='Germany' else value
    mention=LinkedMention('mention-1',text,[0,len(text)],'resolved',[field])
    binding={'column':field,'operator':'=','value':value,'mention_id':'mention-1','source':'verified_value_index'}
    return LinkResult(message,message,[mention],[binding],[])


def answered(tmp_path,analysis,bindings=None,question='2023年发票销售额'):
    store=SessionStore(tmp_path)
    state=store.start('s',{},question,analysis,bindings)
    from qa_agent.clarify.state import prepare_card, transition
    prepare_card(state,RuleEngine().evaluate(question,analysis))
    transition(state,'ANSWERED')
    return state


class Model:
    def __init__(self,*patches,semantic=None):
        self.patches=patches
        self.semantic=semantic
    def complete_json(self,*args,**kwargs):
        return self.semantic if self.semantic is not None else PatchResponse(patches=list(self.patches))


def test_missing_growth_measure_never_becomes_invented_record_set():
    result=extract_intent('同比增长多少？',CATALOG,Model(semantic=SemanticIntent(task_type='growth',scope_missing=True,comparison={'type':'yoy'})))
    issues=RuleEngine().evaluate('同比增长多少？',result).issues
    assert {issue.field for issue in issues}=={'metric','time_scope.current'}


def test_true_undefined_deictic_set_still_requires_scope():
    result=extract_intent('这批客户同比增长多少？',CATALOG,Model(semantic=SemanticIntent(task_type='growth',scope_missing=True,comparison={'type':'yoy'})))
    assert result.scope_missing is True


@pytest.mark.parametrize('message',['2023年销售额占比是多少？','2024年发票金额的比例是多少？','请查2023年账单金额占比是多少？'])
def test_bare_amount_share_cannot_invent_all_library_numerator(message):
    result=extract_intent(message,CATALOG,Model(semantic=SemanticIntent(task_type='ratio',metric='invoice_revenue',
                         numerator='2023年销售额',evidence_spans={'numerator':'2023年销售额'})))
    assert result.numerator is None and 'numerator' not in result.evidence_spans
    assert 'numerator' in {issue.field for issue in RuleEngine().evaluate(message,result).issues}


def test_explicit_full_library_numerator_and_denominator_remain_legal():
    message='2023年全部发票金额占同期全部发票金额的比例是多少？'
    result=extract_intent(message,CATALOG,Model(semantic=SemanticIntent(task_type='ratio',metric='invoice_revenue',
                         numerator='2023年全部发票金额',denominator='同期全部发票金额')))
    assert result.numerator=='2023年全部发票金额'
    assert not RuleEngine().evaluate(message,result).issues


def test_country_change_cannot_rewrite_measure_or_drop_other_objects(tmp_path):
    artist={'column':'artist.name','operator':'=','value':'Metallica'}
    country={'column':'invoice.billing_country','operator':'=','value':'USA'}
    state=answered(tmp_path,SemanticIntent(metric='detail_revenue',time_scope=explicit_period('2023年'),filters=[artist,country]),[artist,country])
    new={**country,'value':'Germany'}
    patches=extract_patches('换成德国。',state,linked('换成德国。','invoice.billing_country','Germany'),Model(
        IntentPatch(op='set',path='metric',value='customer_count',evidence='德国'),
        IntentPatch(op='set',path='task_type',value='ranking',evidence='德国'),
        IntentPatch(op='set',path='filters',value=[new],evidence='德国')))
    apply_patches(state,patches,user_message='换成德国。')
    assert state.analysis.metric=='detail_revenue' and state.analysis.task_type=='lookup'
    assert artist in state.bindings and any(all(item.get(key)==value for key,value in new.items()) for item in state.bindings)
    assert state.analysis.time_scope['current']['start']=='2023-01-01'
    assert state.intent.intent_version==2


def test_explicit_object_replacement_preserves_country_period_and_measure(tmp_path):
    artist={'column':'artist.name','operator':'=','value':'Metallica'}
    country={'column':'invoice.billing_country','operator':'=','value':'Germany'}
    state=answered(tmp_path,SemanticIntent(metric='detail_revenue',time_scope=explicit_period('2022年'),filters=[artist,country]),[artist,country])
    message='改成流派 Metal。'
    value={'column':'genre.name','operator':'=','value':'Metal'}
    patches=extract_patches(message,state,linked(message,'genre.name','Metal'),Model(IntentPatch(op='set',path='filters',value=[value],evidence='流派 Metal')))
    apply_patches(state,patches,user_message=message)
    assert {item['column'] for item in state.bindings}=={'genre.name','invoice.billing_country'}
    assert state.analysis.metric=='detail_revenue' and state.analysis.time_scope['current']['start']=='2022-01-01'
    assert {'schema','fields','result'}<=set(state.invalidated)


def test_real_current_country_evidence_survives_model_omitting_filter_patch(tmp_path):
    old={'column':'genre.name','operator':'=','value':'Metal'}
    state=answered(tmp_path,SemanticIntent(metric='detail_revenue',filters=[old]),[old])
    message='期间改成2023年，限定账单国为德国。'
    patches=extract_patches(message,state,linked(message,'invoice.billing_country','Germany'),Model())
    apply_patches(state,patches,user_message=message)
    assert {item['column']:item['value'] for item in state.bindings}=={'genre.name':'Metal','invoice.billing_country':'Germany'}
    assert state.analysis.time_scope['current']['start']=='2023-01-01'
    assert state.resolutions[-1]['previous_filters']==[old]


def test_topn_actual_requested_size_is_not_executor_display_cap(tmp_path):
    state=answered(tmp_path,SemanticIntent(task_type='ranking',top_n=3,rank_object='track',metric='purchased_quantity'))
    patches=extract_patches('改成前500首。',state,linked('改成前500首。'),Model())
    apply_patches(state,patches,user_message='改成前500首。')
    assert state.analysis.top_n==500
    query='SELECT track_id,SUM(quantity) FROM public.invoice_line GROUP BY track_id ORDER BY track_id LIMIT '
    validate_current_patch_contract(query+'500',CATALOG,state.analysis,state.resolutions)
    for limit in (3,200):
        with pytest.raises(SQLValidationError,match='LIMIT 500'):
            validate_current_patch_contract(query+str(limit),CATALOG,state.analysis,state.resolutions)


@pytest.mark.parametrize('sql',[
    "SELECT SUM(i.total) FROM public.invoice i WHERE i.billing_country='USA' AND i.billing_country='Canada'",
    "SELECT SUM(i.total) FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id AND i.billing_country='USA' WHERE i.billing_country='Canada'",
    "SELECT i.billing_country,SUM(i.total) FROM public.invoice i GROUP BY i.billing_country HAVING i.billing_country='USA'",
    "SELECT SUM(i.total) FROM public.invoice i WHERE LOWER(i.billing_country)='usa'",
])
def test_retired_same_field_value_cannot_return_in_filter_atoms(tmp_path,sql):
    old={'column':'invoice.billing_country','operator':'=','value':'USA'}
    new={**old,'value':'Canada'}
    state=answered(tmp_path,SemanticIntent(metric='invoice_revenue',filters=[old]),[old])
    apply_patches(state,[IntentPatch(op='set',path='filters',value=[new],evidence='加拿大')],user_message='换成加拿大。')
    with pytest.raises(SQLValidationError,match='旧筛选'):
        validate_current_patch_contract(sql,CATALOG,state.analysis,state.resolutions)
    # The same physical field may remain as a projection/grouping and may use
    # its current allowed value. Retired-filter protection must not ban fields.
    validate_current_patch_contract("SELECT i.billing_country,SUM(i.total) FROM public.invoice i WHERE i.billing_country='Canada' GROUP BY i.billing_country",CATALOG,state.analysis,state.resolutions)


def test_removed_country_and_replaced_artist_are_both_retired(tmp_path):
    artist={'column':'artist.name','operator':'=','value':'Metallica'}
    country={'column':'invoice.billing_country','operator':'=','value':'USA'}
    state=answered(tmp_path,SemanticIntent(metric='detail_revenue',filters=[artist,country]),[artist,country])
    apply_patches(state,[IntentPatch(op='set',path='filters',value=[country,{'column':'genre.name','operator':'=','value':'Metal'}],evidence='流派 Metal')],user_message='改成流派 Metal。')
    from qa_agent.clarify.state import transition
    transition(state,'EXECUTING');transition(state,'ANSWERED')
    apply_patches(state,[IntentPatch(op='remove',path='filters',value=[country],evidence='去掉账单国家限制')],user_message='去掉账单国家限制。')
    sqls=("SELECT SUM(il.unit_price*il.quantity) FROM public.invoice_line il JOIN public.track t ON t.track_id=il.track_id JOIN public.album a ON a.album_id=t.album_id JOIN public.artist ar ON ar.artist_id=a.artist_id WHERE ar.name='Metallica'",
          "SELECT SUM(il.unit_price*il.quantity) FROM public.invoice_line il JOIN public.invoice i ON i.invoice_id=il.invoice_id WHERE i.billing_country='USA'")
    for sql in sqls:
        with pytest.raises(SQLValidationError,match='旧筛选'):
            validate_current_patch_contract(sql,CATALOG,state.analysis,state.resolutions)
    question=execution_question(state)
    assert question.startswith('根据以下当前已合并的执行合同')
    assert '历史首轮原文（仅供保留未修改的返回字段' in question


def test_ratio_role_keys_do_not_collapse_and_local_guard_remains_separate(tmp_path):
    old={'column':'customer.country','operator':'=','value':'Germany','binding_scope':'numerator'}
    denominator={**old,'binding_scope':'denominator'}
    state=answered(tmp_path,SemanticIntent(task_type='ratio',metric='invoice_revenue',time_scope=explicit_period('2023年'),
                   numerator='德国居住客户的销售额',denominator='同期德国居住客户的销售额',filters=[old,denominator]),[old,denominator])
    apply_patches(state,[IntentPatch(op='remove',path='filters',value=[denominator],evidence='分母改成全部发票金额')],user_message='分母改成全部发票金额。')
    assert state.bindings==[old]
    validate_current_patch_contract("SELECT SUM(CASE WHEN c.country='Germany' THEN i.total END)/NULLIF(SUM(i.total),0) FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id",CATALOG,state.analysis,state.resolutions)


@pytest.mark.parametrize('metric,source,correct,wrong',[
    ('purchased_quantity','public.invoice_line il','SUM(il.quantity)','SUM(il.unit_price*il.quantity)'),
    ('detail_revenue','public.invoice_line il','SUM(il.unit_price*il.quantity)','SUM(il.quantity)'),
    ('invoice_count','public.invoice i','COUNT(i.invoice_id)','SUM(i.total)'),
    ('average_invoice_amount','public.invoice i','AVG(i.total)','SUM(i.total)'),
])
def test_simple_patched_measure_matches_physical_expression_not_alias(metric,source,correct,wrong):
    analysis=SemanticIntent(task_type='lookup',metric=metric)
    history=[{'message':'改指标','previous_filters':[], 'patches':[{'path':'metric','op':'set','value':metric}]}]
    validate_current_patch_contract(f'SELECT {correct} AS amount FROM {source}',CATALOG,analysis,history)
    with pytest.raises(SQLValidationError,match='当前补丁指标'):
        validate_current_patch_contract(f'SELECT {wrong} AS {metric} FROM {source}',CATALOG,analysis,history)


def test_replacing_multivalue_filter_keeps_current_value_allowed():
    old={'column':'invoice.billing_country','operator':'IN','value':['USA','Canada']}
    new={'column':'invoice.billing_country','operator':'=','value':'Canada'}
    analysis=SemanticIntent(task_type='aggregation',metric='invoice_count',filters=[new])
    history=[{'previous_filters':[old],'patches':[{'path':'filters','op':'set','value':[new]}]}]
    validate_current_patch_contract("SELECT COUNT(invoice_id) FROM public.invoice WHERE billing_country='Canada'",CATALOG,analysis,history)
    with pytest.raises(SQLValidationError,match='旧筛选'):
        validate_current_patch_contract("SELECT COUNT(invoice_id) FROM public.invoice WHERE billing_country IN ('USA','Canada')",CATALOG,analysis,history)


def test_ranking_metric_change_refreshes_derived_sort_preserving_ties(tmp_path):
    analysis=SemanticIntent(task_type='ranking',metric='purchased_quantity',rank_object='track',top_n=5,
                            order={'field':'purchased_quantity','direction':'desc','tie_breaker':'track.track_id ASC'})
    state=answered(tmp_path,analysis)
    apply_patches(state,[IntentPatch(op='set',path='metric',value='detail_revenue',evidence='销售额')],user_message='指标改成销售额。')
    assert state.analysis.order=={'field':'detail_revenue','direction':'desc','tie_breaker':'track.track_id ASC'}
    assert 'order' in state.invalidated
    # Independently specified sort keys are not a derived metric reference.
    state=answered(tmp_path/'independent',analysis.model_copy(update={'order':{'field':'track.track_id','direction':'asc'}}))
    apply_patches(state,[IntentPatch(op='set',path='metric',value='detail_revenue',evidence='销售额')],user_message='指标改成销售额。')
    assert state.analysis.order=={'field':'track.track_id','direction':'asc'}


def test_extra_aggregate_is_not_requested_measure_and_complex_comparisons_exit():
    history=[{'message':'换指标','previous_filters':[],'patches':[{'path':'metric','op':'set','value':'average_invoice_amount'}]}]
    analysis=SemanticIntent(task_type='aggregation',metric='average_invoice_amount')
    with pytest.raises(SQLValidationError,match='额外投影'):
        validate_current_patch_contract('SELECT AVG(total),SUM(total) FROM public.invoice',CATALOG,analysis,history)
    analysis.task_type='growth'
    validate_current_patch_contract('SELECT SUM(total)/NULLIF(COUNT(invoice_id),0)-1 FROM public.invoice',CATALOG,analysis,history)
    analysis.task_type='aggregation'
    validate_current_patch_contract('WITH a AS (SELECT AVG(total) value FROM public.invoice) SELECT value FROM a',CATALOG,analysis,history)


def test_literal_primary_desc_and_tie_asc_do_not_share_one_order_field():
    model=Model(semantic=SemanticIntent(task_type='ranking',metric='purchased_quantity',rank_object='track',top_n=3,
                                      order={'field':'track_id','direction':'asc'}))
    question='2023年按购买数量降序排名前3的曲目，返回曲目编号和购买数量；并列按曲目编号升序。'
    result=extract_intent(question,CATALOG,model)
    assert result.order=={'field':'purchased_quantity','direction':'desc',
                          'tie_breakers':[{'field':'track.track_id','direction':'asc'}]}
    # Equal metric values could hide this SQL's wrong primary ordering in EX.
    wrong='SELECT track_id,SUM(quantity) AS value FROM public.invoice_line GROUP BY track_id ORDER BY track_id ASC LIMIT 3'
    with pytest.raises(SQLValidationError,match='主排序'):
        validate_current_patch_contract(wrong,CATALOG,result,[])
    correct='SELECT track_id,SUM(quantity) AS value FROM public.invoice_line GROUP BY track_id ORDER BY value DESC,track_id ASC LIMIT 3'
    validate_current_patch_contract(correct,CATALOG,result,[])


def test_undeclared_topn_direction_is_not_a_new_desc_business_default():
    result=extract_intent('2023年按购买数量排名前3的曲目；并列按曲目编号升序。',CATALOG,
                         Model(semantic=SemanticIntent(task_type='ranking',metric='purchased_quantity',rank_object='track',top_n=3,
                                                       order={'field':'track_id','direction':'asc'})))
    assert result.order['field']=='purchased_quantity' and result.order['direction'] is None
    assert result.order['tie_breakers']==[{'field':'track.track_id','direction':'asc'}]


def test_independent_explicit_id_primary_is_not_replaced_by_metric_order():
    analysis=SemanticIntent(task_type='ranking',metric='purchased_quantity',rank_object='track',top_n=3,
                            order={'field':'track.track_id','direction':'asc'})
    correct='SELECT track_id,SUM(quantity) AS value FROM public.invoice_line GROUP BY track_id ORDER BY track_id ASC LIMIT 3'
    validate_current_patch_contract(correct,CATALOG,analysis,[])
    with pytest.raises(SQLValidationError,match='独立排序'):
        validate_current_patch_contract(correct.replace('ORDER BY track_id ASC','ORDER BY value DESC,track_id ASC'),CATALOG,analysis,[])


def test_pressure_schema_uses_actual_catalog_and_fk_not_public_shortcut():
    schema='qa_pressure_fixture'
    tables=[]
    for table in CATALOG.tables:
        foreign_keys=deepcopy(table.foreign_keys)
        for item in foreign_keys:
            item['references']['schema']=schema
        tables.append(replace(table,schema=schema,foreign_keys=foreign_keys))
    catalog=replace(CATALOG,tables=tuple(tables))
    analysis=SemanticIntent(task_type='ranking',metric='purchased_quantity',rank_object='track',top_n=3,
                            order={'field':'purchased_quantity','direction':'desc',
                                   'tie_breakers':[{'field':'track.track_id','direction':'asc'}]})
    correct=f'SELECT il.track_id,SUM(il.quantity) AS value FROM {schema}.invoice_line il GROUP BY il.track_id ORDER BY value DESC,il.track_id ASC LIMIT 3'
    validate_current_patch_contract(correct,catalog,analysis,[])
    with pytest.raises(SQLValidationError):
        validate_current_patch_contract(correct.replace(schema+'.invoice_line','public.invoice_line'),catalog,analysis,[])


def test_explicit_direction_question_version_preserves_original_and_all_gold():
    from scripts.run_d4_multiturn import new_cases
    available=new_cases(include_legacy=True)
    legacy=next(item for item in available if item['id']=='d4-dialog-04')
    explicit=next(item for item in available if item['id']=='d4-dialog-04-v2')
    assert legacy['turns'][0]['message']=='2023年按购买数量排名前3的曲目，返回曲目编号和购买数量；并列按曲目编号升序。'
    assert explicit['turns'][0]['message']==legacy['turns'][0]['message'].replace('按购买数量排名','按购买数量降序排名')
    assert [item['message'] for item in explicit['turns'][1:]]==[item['message'] for item in legacy['turns'][1:]]
    assert [item['gold_sql'] for item in explicit['turns']]==[item['gold_sql'] for item in legacy['turns']]
    assert [item['id'] for item in new_cases()]==['d4-dialog-01','d4-dialog-02','d4-dialog-03','d4-dialog-04-v2','d4-dialog-05']


def test_metric_and_country_edits_survive_disk_reload_and_invalidate_execution(tmp_path):
    state=answered(tmp_path,SemanticIntent(metric='invoice_revenue',time_scope=explicit_period('2023年')))
    patches=extract_patches('改看发票张数。',state,linked('改看发票张数。'),Model(IntentPatch(op='set',path='metric',value='invoice_revenue',evidence='发票张数')))
    apply_patches(state,patches,user_message='改看发票张数。')
    store=SessionStore(tmp_path);store.save(state)
    restored=SessionStore(tmp_path).get('s')
    assert restored.analysis.metric=='invoice_count'
    assert restored.analysis.time_scope['current']['end']=='2024-01-01'
    assert restored.intent.intent_version==2 and 'schema' in restored.invalidated


def test_scope_switch_cannot_drop_country_through_empty_whole_list(tmp_path):
    old={'column':'invoice.billing_country','operator':'=','value':'Canada'}
    employee={'column':'employee.first_name','operator':'=','value':'Jane'}
    state=answered(tmp_path,SemanticIntent(metric='invoice_revenue',time_scope=explicit_period('2023年'),filters=[old,employee]),[old,employee])
    message='改按客户所在地统计。'
    patches=extract_patches(message,state,linked(message),Model(
        IntentPatch(op='set',path='region_scope',value='customer.country',evidence='客户所在地'),
        IntentPatch(op='set',path='filters',value=[],evidence='客户所在地')))
    apply_patches(state,patches,user_message=message)
    assert employee in state.bindings
    assert {'column':'customer.country','operator':'=','value':'Canada'} in state.bindings


@pytest.mark.parametrize('model_removes_filter',[True,False])
def test_explicit_country_filter_cancellation_ignores_spurious_scope_null(tmp_path,model_removes_filter):
    country={'column':'customer.country','operator':'=','value':'Canada'}
    employee={'column':'employee.first_name','operator':'=','value':'Jane'}
    state=answered(tmp_path,SemanticIntent(metric='invoice_count',region_scope='customer.country',filters=[country,employee]),[country,employee])
    message='去掉客户所在地限制。'
    proposals=[IntentPatch(op='set',path='region_scope',value=None,evidence=message)]
    if model_removes_filter:
        proposals.append(IntentPatch(op='remove',path='filters',value=country,evidence=message))
    patches=extract_patches(message,state,linked(message),Model(*proposals))
    apply_patches(state,patches,user_message=message)
    assert state.bindings==[employee]
    assert state.analysis.region_scope=='customer.country'
    assert state.intent.intent_version==2


def test_negated_country_cancellation_never_authorizes_a_remove(tmp_path):
    country={'column':'customer.country','operator':'=','value':'Canada'}
    state=answered(tmp_path,SemanticIntent(filters=[country]),[country])
    message='不要去掉客户所在地限制。'
    from qa_agent.clarify.state import SessionConflict
    with pytest.raises(SessionConflict):
        extract_patches(message,state,linked(message),Model(IntentPatch(op='remove',path='filters',value=country,evidence=message)))


@pytest.mark.parametrize('message',['改看发票张数。','加上账单国为德国。','去掉账单国家限制。','期间改成2024年。','2024年呢？'])
def test_incremental_messages_recognized(message):
    assert is_followup(message)


def test_complete_new_question_not_forced_into_previous_contract():
    assert not is_followup('2024年加拿大客户有多少？')


def ratio_bindings():
    return [
        {'column':'customer.country','operator':'=','value':'Germany','binding_scope':'numerator','scope_evidence':'德国居住客户的销售额'},
        {'column':'invoice.billing_country','operator':'=','value':'Germany','binding_scope':'denominator','scope_evidence':'分母改成2023年账单国为德国的销售额。'}]


RATIO="SELECT SUM(CASE WHEN c.country='Germany' THEN i.total END)/NULLIF(SUM(CASE WHEN i.billing_country='Germany' THEN i.total END),0) AS share FROM invoice i JOIN customer c ON i.customer_id=c.customer_id WHERE i.invoice_date>='2023-01-01' AND i.invoice_date<'2024-01-01'"
CONTEXT={'task_type':'ratio','metric':'invoice_revenue','numerator':'Germany居住客户的销售额','denominator':'2023年账单国为Germany的销售额','region_scope':'customer.country','time_scope':explicit_period('2023年')}


def test_explicit_restricted_denominator_is_proven_without_global_filter():
    validate_value_bindings(RATIO,CATALOG,ratio_bindings(),ratio_context=CONTEXT)


@pytest.mark.parametrize('sql',[
    RATIO.replace("i.billing_country='Germany'","c.country='Germany'"),
    RATIO.replace("c.country='Germany'","c.country='Brazil'"),
    RATIO.replace("NULLIF(SUM(CASE WHEN i.billing_country='Germany' THEN i.total END),0)","NULLIF(SUM(i.total),0)"),
    RATIO.replace("i.invoice_date<'2024-01-01'","i.invoice_date<'2024-01-01' AND i.billing_country='Germany'"),
    RATIO.replace("i.customer_id=c.customer_id","i.customer_id=c.customer_id OR TRUE"),
    RATIO.replace("NULLIF(SUM(CASE WHEN i.billing_country='Germany' THEN i.total END),0)","SUM(CASE WHEN i.billing_country='Germany' THEN i.total END)"),
])
def test_ratio_changed_scope_or_unsafe_sql_rejected(sql):
    with pytest.raises(SQLValidationError):
        validate_value_bindings(sql,CATALOG,ratio_bindings(),ratio_context=CONTEXT)


def test_restricted_denominator_needs_genuine_operand_evidence():
    bindings=ratio_bindings();bindings[1]['scope_evidence']=''
    with pytest.raises(SQLValidationError):
        validate_value_bindings(RATIO,CATALOG,bindings,ratio_context=CONTEXT)


def test_operand_change_preserves_other_operand_and_period(tmp_path):
    numerator={**ratio_bindings()[0],'value':'Germany','mention_id':'old'}
    state=answered(tmp_path,SemanticIntent(task_type='ratio',metric='invoice_revenue',numerator='Germany居住客户的销售额',denominator='同期全部发票金额',region_scope='customer.country',time_scope=explicit_period('2023年'),filters=[numerator]),[numerator])
    message='分母改成2023年账单国为德国的销售额。'
    patches=extract_patches(message,state,linked(message,'invoice.billing_country','Germany'),Model(
        IntentPatch(op='set',path='denominator',value=message,evidence=message),
        IntentPatch(op='set',path='region_scope',value='invoice.billing_country',evidence='账单国')))
    apply_patches(state,patches,user_message=message)
    from qa_agent.clarify.service import _refresh_ratio_numerator_binding
    _refresh_ratio_numerator_binding(state,patches,linked(message,'invoice.billing_country','Germany'),message)
    assert numerator in state.bindings
    assert len(state.bindings)==2 and state.analysis.region_scope=='customer.country'
    assert state.analysis.numerator=='Germany居住客户的销售额'
    assert state.analysis.time_scope['current']['start']=='2023-01-01'
    assert state.bindings[-1]['binding_scope']=='denominator'


def test_all_new_development_labels_have_six_turns_and_safe_reference_sql():
    from scripts.run_d4_multiturn import new_cases
    from qa_agent.sql.validator import validate_sql
    from qa_agent.sql.repair_guard import validate_chinook_fk_joins
    cases=new_cases()
    assert len(cases)==5 and all(case['split']=='dev' and len(case['turns'])==6 for case in cases)
    for case in cases:
        for turn in case['turns']:
            checked=validate_sql(turn['gold_sql'],CATALOG)
            validate_chinook_fk_joins(checked.sql,CATALOG)
            assert turn['expected']['current']['start'] in checked.sql
            assert turn['expected']['current']['end'] in checked.sql


def test_new_denominator_uses_approved_invoice_default_not_numerator_residence(tmp_path):
    numerator=ratio_bindings()[0]
    state=answered(tmp_path,SemanticIntent(task_type='ratio',metric='invoice_revenue',numerator='Germany居住客户的销售额',denominator='同期全部发票金额',region_scope='customer.country',time_scope=explicit_period('2023年'),filters=[numerator]),[numerator])
    message='分母改成德国的发票销售额。'
    patches=extract_patches(message,state,linked(message,'invoice.billing_country','Germany'),Model(IntentPatch(op='set',path='denominator',value=message,evidence=message)))
    apply_patches(state,patches,user_message=message)
    from qa_agent.clarify.service import _refresh_ratio_numerator_binding
    _refresh_ratio_numerator_binding(state,patches,linked(message,'invoice.billing_country','Germany'),message)
    assert state.bindings[-1]['column']=='invoice.billing_country'
    assert state.bindings[-1]['scope_basis']=='oct12_approved_invoice_default'
    context={**CONTEXT,'denominator':state.analysis.denominator}
    validate_value_bindings(RATIO,CATALOG,state.bindings,ratio_context=context)


def test_model_cannot_install_forged_scope_metadata_on_a_grounded_value(tmp_path):
    original={'column':'invoice.billing_country','operator':'=','value':'Germany','source':'verified_value_index'}
    state=answered(tmp_path,SemanticIntent(filters=[original]),[original])
    message='换成德国。'
    forged={**original,'binding_scope':'denominator','scope_evidence':'不存在的账单国原文','scope_basis':'retained_operand_scope'}
    proposals=extract_patches(message,state,linked(message,'invoice.billing_country','Germany'),Model(IntentPatch(op='set',path='filters',value=[forged],evidence='德国')))
    binding=next(patch.value[0] for patch in proposals if patch.path=='filters')
    assert 'binding_scope' not in binding and 'scope_basis' not in binding


def test_explicit_comparison_cancellation_preserves_current_country_and_metric(tmp_path):
    country={'column':'invoice.billing_country','operator':'=','value':'Canada'}
    analysis=SemanticIntent(task_type='growth',metric='average_invoice_amount',comparison={'type':'yoy'},time_scope={**explicit_period('2024年'),'base':{**period_for_test(2023),'derived_from':'explicit current period and yoy'}},filters=[country])
    state=answered(tmp_path,analysis,[country])
    message='取消同比。'
    patches=extract_patches(message,state,linked(message),Model(IntentPatch(op='remove',path='comparison',evidence='取消同比')))
    apply_patches(state,patches,user_message=message)
    assert state.analysis.task_type=='aggregation' and state.analysis.comparison is None
    assert state.analysis.metric=='average_invoice_amount' and state.bindings==[country]
    assert state.analysis.time_scope['current']==analysis.time_scope['current'] and 'base' not in state.analysis.time_scope
    assert state.intent.intent_version==2 and {'derived_period','result'}<=set(state.invalidated)
    explanatory=extract_patches('不是同比，只是解释术语。',state,linked('不是同比，只是解释术语。'),Model())
    assert not any(patch.path in {'task_type','comparison','time_scope'} for patch in explanatory)


def period_for_test(year):
    return {'start':f'{year}-01-01','end':f'{year+1}-01-01'}
