"""Approved Oct 12 defaults and regressions; no held-out dataset inputs."""
import json
from pathlib import Path

import numpy as np
import pytest

from qa_agent.clarify.extractor import extract_intent
from qa_agent.clarify.rules import RuleEngine, SemanticIntent, explicit_period
from qa_agent.clarify.service import is_followup, run_gate, finish_gate
from qa_agent.clarify.state import IntentPatch, PatchResponse, SessionStore
from qa_agent.config import Settings
from qa_agent.nlu.linker import Mention, ValueLinker
from qa_agent.nlu.value_index import ValueIndex, ValueRecord, record_id
from qa_agent.schemas import ChatRequest
from qa_agent.sql.catalog import load_catalog

ROOT=Path(__file__).resolve().parents[1]


def index_rows():
    return ValueIndex([ValueRecord(record_id(column,value),column,value,surface,'user-authorized-oct12',kind,'fixture')
                      for column,value,surface,kind in [
                          ('invoice.billing_country','USA','老美','alias'),
                          ('customer.country','USA','老美','alias'),
                          ('invoice.billing_country','France','法国','alias'),
                          ('customer.country','France','法国','alias'),
                          ('invoice.billing_country','Germany','德国','alias'),
                          ('customer.country','Germany','德国','alias')]])


class NoModel:
    def complete_json(self,*args,**kwargs):
        raise AssertionError('Clear question does not need a model call')


@pytest.mark.parametrize('word',['每年','每月','今年','去年','本季度'])
def test_time_words_do_not_enter_candidate_cards(word):
    linker=ValueLinker(index_rows(),Settings(db_url=''),llm=NoModel())
    result=linker.link(word,mentions=[Mention(word,0,len(word),('invoice.billing_country',))])
    assert not result.ambiguous and not result.bindings
    assert result.mentions[0].candidates==[]


def test_real_multiyear_question_has_no_every_year_country_mention():
    result=ValueLinker(index_rows(),Settings(db_url=''),llm=NoModel()).link(
        '2022年和2023年，Chinook 每年的发票销售额分别是多少？')
    assert not result.mentions and not result.bindings


def test_zero_fuzzy_and_point43_vector_do_not_reach_llm():
    vector=np.asarray([[0.43,np.sqrt(1-0.43**2)]],dtype=np.float32)
    index=ValueIndex([ValueRecord(record_id('invoice.billing_country','Brazil'),
                                  'invoice.billing_country','Brazil','Brazil','actual_catalog')],vector)
    result=ValueLinker(index,Settings(db_url=''),llm=NoModel(),
                       encode=lambda texts:np.asarray([[1.,0.]],dtype=np.float32)).link(
        '并非实体',mentions=[Mention('并非实体',0,4,('invoice.billing_country',))])
    assert result.mentions[0].candidates==[] and not result.ambiguous
    assert all(not stage.get('candidates') for stage in result.mentions[0].stages)


@pytest.mark.parametrize('question,column',[('老美有几张发票？','invoice.billing_country'),
                                           ('老美客户有多少人？','customer.country')])
def test_approved_laomei_is_direct_l0(tmp_path,question,column):
    result=ValueLinker(index_rows(),Settings(db_url=''),llm=NoModel()).link(question)
    assert result.bindings[0]['value']=='USA' and result.bindings[0]['column']==column
    gate=run_gate(ChatRequest(message=question,session_id='clear'),
                  load_catalog(ROOT/'data/catalog/chinook.yaml'),NoModel(),result,store=SessionStore(tmp_path))
    assert gate.decision.level=='L0' and gate.card is None and gate.state.switch_card is None


@pytest.mark.parametrize('semantic,question',[
    (SemanticIntent(task_type='ranking',rank_object='track',top_n=5),'最热门5首曲目'),
    (SemanticIntent(task_type='aggregation',metric='repeat_customer_count'),'复购客户有多少'),
    (SemanticIntent(task_type='ranking',rank_object='customer',metric='invoice_revenue'),'客户金额排名')])
def test_missing_period_defaults_all_existing_data(semantic,question):
    decision=RuleEngine().evaluate(question,semantic,available_years=[2022,2024])
    assert not decision.issues and decision.analysis.time_scope['all_data'] is True
    assert decision.derived['time_scope']['available_years']==[2022,2024]


def test_who_default_is_customer_revenue_but_track_popular_stays_quantity():
    who=RuleEngine().evaluate('谁买得最多？',SemanticIntent())
    assert who.analysis.rank_object=='customer' and who.analysis.metric=='invoice_revenue'
    track=RuleEngine().evaluate('最热门5首曲目',SemanticIntent(task_type='ranking',rank_object='track',top_n=5))
    assert track.analysis.metric=='purchased_quantity'


def test_confirmed_period_is_never_replaced_by_all_data_default():
    decision=RuleEngine().evaluate('谁买得最多？',SemanticIntent(
        task_type='ranking',rank_object='customer',metric='invoice_revenue',time_scope=explicit_period('2023年')))
    assert decision.analysis.time_scope['current']['start']=='2023-01-01'
    assert not decision.analysis.time_scope.get('all_data')


def test_relative_growth_period_has_one_issue_and_available_year_choices():
    decision=RuleEngine().evaluate('今年销售额同比',SemanticIntent(
        task_type='growth',metric='invoice_revenue',comparison={'type':'yoy'},time_ambiguous=True),available_years=[2023,2024])
    periods=[issue for issue in decision.issues if issue.field=='time_scope.current']
    assert len(periods)==1 and [option['id'] for option in periods[0].options]==['year:2023','year:2024']


def test_default_denominator_is_restricted_to_invoice_amount():
    sales=RuleEngine().evaluate('法国销售额占比',SemanticIntent(task_type='ratio',metric='invoice_revenue',numerator='法国销售额'))
    assert '同期全部发票金额' in sales.analysis.denominator
    assert sales.derived['denominator']['scope']=='all_invoices_same_period'
    count=RuleEngine().evaluate('法国客户数量占比',SemanticIntent(task_type='ratio',metric='customer_count',numerator='法国客户数量'))
    assert count.analysis.denominator is None and count.level=='L2'
    explicit=RuleEngine().evaluate('法国销售额占德国销售额',SemanticIntent(
        task_type='ratio',metric='invoice_revenue',numerator='法国销售额',denominator='德国销售额'))
    assert explicit.analysis.denominator=='德国销售额'


def test_explicit_numerator_and_residence_scope_survive_model_omission(tmp_path):
    class Model:
        def complete_json(self,*args,**kwargs):
            return SemanticIntent(task_type='ratio',metric='invoice_revenue',numerator=None,denominator=None)
    question='2024年法国居住客户的销售额占比是多少？'
    linked=ValueLinker(index_rows(),Settings(db_url='')).link(question)
    semantic=extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(),bindings=linked.bindings)
    assert semantic.numerator and '法国居住客户' in semantic.numerator
    assert semantic.region_scope=='customer.country'
    gate=run_gate(ChatRequest(message=question,session_id='ratio'),load_catalog(ROOT/'data/catalog/chinook.yaml'),
                  Model(),linked,store=SessionStore(tmp_path))
    assert not gate.decision.issues and gate.state.bindings[0]['column']=='customer.country'
    assert gate.state.bindings[0]['binding_scope']=='numerator'
    assert '同期全部发票金额' in gate.question


def test_numerator_followup_refreshes_provenance_without_losing_year_or_denominator(tmp_path):
    class Model:
        def complete_json(self,system_prompt,user_prompt,response_model,trace=None):
            if response_model is SemanticIntent:
                return SemanticIntent(task_type='ratio',metric='invoice_revenue')
            return PatchResponse(patches=[IntentPatch(op='set',path='numerator',value='德国居住客户的销售额',evidence='德国居住客户的销售额')])
    catalog=load_catalog(ROOT/'data/catalog/chinook.yaml')
    store=SessionStore(tmp_path)
    linker=ValueLinker(index_rows(),Settings(db_url=''))
    initial='2024年法国居住客户的销售额占比是多少？'
    first=run_gate(ChatRequest(message=initial,session_id='s'),catalog,Model(),linker.link(initial),store=store)
    finish_gate(first,succeeded=True,store=store)
    second_message='分子换成德国居住客户的销售额。'
    assert is_followup(second_message)
    second=run_gate(ChatRequest(message=second_message,session_id='s'),catalog,Model(),linker.link(second_message),store=store)
    assert second.state.bindings[0]['value']=='Germany' and second.state.bindings[0]['binding_scope']=='numerator'
    assert 'Germany' in second.state.analysis.numerator
    assert second.state.analysis.time_scope['current']['start']=='2024-01-01'
    assert second.state.analysis.denominator==first.state.analysis.denominator
    assert second.state.intent.intent_version==first.state.intent.intent_version+1


def test_aw_never_receives_chinook_defaults():
    result=RuleEngine().evaluate('谁买得最多？',SemanticIntent(task_type='ranking'),db_id='adventureworks')
    assert result.level=='L2' and result.analysis.rank_object is None and result.analysis.metric is None


def test_album_artist_typo_uses_artist_name_instead_of_album_title():
    rows=[ValueRecord(record_id(column,value),column,value,value,'actual_catalog')
          for column,value in [('artist.name','Metallica'),('artist.name','Iron Maiden'),('album.title','Metallica')]]
    result=ValueLinker(ValueIndex(rows),Settings(db_url=''),llm=NoModel()).link('Metallcia 有多少张专辑？')
    assert result.bindings[0]['column']=='artist.name' and result.bindings[0]['value']=='Metallica'
    assert result.bindings[0]['method']=='fuzzy'


def test_english_media_format_link_uses_media_type_lookup_field():
    rows=[ValueRecord(record_id(column,value),column,value,value,'actual_catalog')
          for column,value in [('media_type.name','Protected AAC audio file'),('track.name','Example track')]]
    result=ValueLinker(ValueIndex(rows),Settings(db_url=''),llm=NoModel()).link(
        'Chinook 里 Protected AAC audio file 这种 format 有多少首曲目？')
    assert result.bindings[0]['column']=='media_type.name' and result.bindings[0]['value']=='Protected AAC audio file'


def test_explicit_missing_genre_is_preserved_instead_of_nearby_vector_choice():
    vectors=np.asarray([[1.,0.]],dtype=np.float32)
    rows=[ValueRecord(record_id('genre.name','Rock'),'genre.name','Rock','Rock','actual_catalog')]
    result=ValueLinker(ValueIndex(rows,vectors),Settings(db_url=''),llm=NoModel(),
                       encode=lambda texts:np.asarray([[1.,0.]],dtype=np.float32)).link(
        '查询 genre 为 Vaporwave 的曲目数量；如果数据库里根本没有这个流派，请直接报告没有记录。')
    assert result.mentions and result.mentions[0].original_text=='Vaporwave'
    assert result.mentions[0].status=='unmatched' and not result.bindings
    assert result.rewritten_question.startswith('查询 genre 为 Vaporwave ')


def test_complete_sp03_14_keeps_both_years_when_model_only_extracts_last_one(tmp_path):
    class Model:
        def complete_json(self,*args,**kwargs):
            return SemanticIntent(task_type='aggregation',metric='invoice_revenue',time_scope=explicit_period('2023年'),grouping=['year'])
    question='2022年和2023年，Chinook 每年的发票销售额分别是多少？'
    linked=ValueLinker(index_rows(),Settings(db_url=''),llm=NoModel()).link(question)
    gate=run_gate(ChatRequest(message=question,session_id='years'),load_catalog(ROOT/'data/catalog/chinook.yaml'),
                  Model(),linked,store=SessionStore(tmp_path))
    assert gate.card is None and gate.decision.level=='L0'
    assert gate.state.analysis.time_scope['current']['start']=='2022-01-01'
    assert gate.state.analysis.time_scope['current']['end']=='2024-01-01'
    assert gate.state.analysis.time_scope['years']==[2022,2023]


def test_sp03_06_real_supplement_fills_current_once_and_derives_prior_year(tmp_path):
    class Model:
        def complete_json(self,system_prompt,user_prompt,response_model,trace=None):
            if response_model is SemanticIntent:
                return SemanticIntent(task_type='growth',metric=None,comparison={'type':'yoy'},time_ambiguous=True)
            # Program must use the actual first/current year, even if the model
            # mistakenly extracts only the second year as current.
            return PatchResponse(patches=[IntentPatch(op='set',path='time_scope',
                value=explicit_period('2023年'),evidence='2023年')])
    catalog=load_catalog(ROOT/'data/catalog/chinook.yaml')
    store=SessionStore(tmp_path)
    linker=ValueLinker(index_rows(),Settings(db_url=''))
    question='销售额同比增长多少？'
    first=run_gate(ChatRequest(message=question,session_id='growth'),catalog,Model(),linker.link(question),store=store)
    assert first.card and first.decision.level=='L2'
    assert len([issue for issue in first.decision.issues if issue.field=='time_scope.current'])==1
    reply='2024年，和2023年比。'
    second=run_gate(ChatRequest(message=reply,session_id='growth',clarification_id=first.card['clarification_id'],
                               intent_version=first.state.intent.intent_version),catalog,Model(),linker.link(reply),store=store)
    assert second.card is None and second.decision.level=='L0'
    assert second.state.analysis.metric=='invoice_revenue'
    assert second.state.analysis.time_scope['current']['start']=='2024-01-01'
    assert second.state.analysis.time_scope['base']['start']=='2023-01-01'
    assert explicit_period('2024年和2023年同比') is None


def test_model_cannot_reset_confirmed_2023_period_during_customer_metric_followup(tmp_path):
    class Model:
        def complete_json(self,system_prompt,user_prompt,response_model,trace=None):
            if response_model is SemanticIntent:
                return SemanticIntent(task_type='ranking',rank_object='customer',metric='invoice_revenue',top_n=3)
            return PatchResponse(patches=[IntentPatch(op='set',path='metric',value='invoice_revenue',evidence='发票金额'),
                                           IntentPatch(op='set',path='time_scope',value=None,evidence='发票金额')])
    catalog=load_catalog(ROOT/'data/catalog/chinook.yaml')
    store=SessionStore(tmp_path)
    linker=ValueLinker(index_rows(),Settings(db_url=''))
    question='2023年客户谁买得最多，前3名？'
    first=run_gate(ChatRequest(message=question,session_id='rank'),catalog,Model(),linker.link(question),store=store)
    finish_gate(first,succeeded=True,store=store)
    reply='那按发票金额排名。'
    second=run_gate(ChatRequest(message=reply,session_id='rank'),catalog,Model(),linker.link(reply),store=store)
    assert second.state.analysis.time_scope['current']['start']=='2023-01-01'
    assert not second.state.analysis.time_scope.get('all_data')


def test_metric_only_followup_cannot_drop_existing_yoy_task_or_year(tmp_path):
    class Model:
        def complete_json(self,system_prompt,user_prompt,response_model,trace=None):
            if response_model is SemanticIntent:
                return SemanticIntent(task_type='growth',metric='invoice_revenue',comparison={'type':'yoy'})
            return PatchResponse(patches=[IntentPatch(op='set',path='metric',value='average_invoice_amount',evidence='客单价'),
                                           IntentPatch(op='set',path='task_type',value='lookup',evidence='客单价'),
                                           IntentPatch(op='set',path='time_scope',value=None,evidence='客单价')])
    catalog=load_catalog(ROOT/'data/catalog/chinook.yaml');store=SessionStore(tmp_path)
    linker=ValueLinker(index_rows(),Settings(db_url=''))
    question='2024年销售额同比增长多少？'
    first=run_gate(ChatRequest(message=question,session_id='yoy'),catalog,Model(),linker.link(question),store=store)
    finish_gate(first,succeeded=True,store=store)
    reply='那改成客单价。'
    second=run_gate(ChatRequest(message=reply,session_id='yoy'),catalog,Model(),linker.link(reply),store=store)
    assert second.state.analysis.task_type=='growth' and second.state.analysis.comparison['type']=='yoy'
    assert second.state.analysis.time_scope['current']['start']=='2024-01-01'
    assert second.state.analysis.metric=='average_invoice_amount'


def test_amount_denominator_default_is_invalidated_when_followup_changes_to_customer_count(tmp_path):
    from qa_agent.clarify.state import apply_patches, prepare_card, transition
    state=SessionStore(tmp_path).start('count',{},'法国销售额占比',SemanticIntent(
        task_type='ratio',metric='invoice_revenue',numerator='法国销售额'))
    prepare_card(state,RuleEngine().evaluate(state.original_question,state.analysis))
    transition(state,'ANSWERED')
    apply_patches(state,[IntentPatch(op='set',path='metric',value='customer_count',evidence='客户数量')],
                  user_message='改成客户数量')
    result=RuleEngine().evaluate(state.original_question,state.analysis)
    assert result.analysis.denominator is None and result.level=='L2'
