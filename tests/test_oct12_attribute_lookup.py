"""Isolated two-pass review probes for explicit customer attribute sorting."""
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.clarify.rules import SemanticIntent,RuleEngine
from qa_agent.sql.catalog import load_catalog

from qa_agent.clarify import extractor as candidate


class Model:
    def __init__(self,result=None):
        self.result=result or SemanticIntent(task_type='ranking',metric=None,rank_object='customer',top_n=5,
            order={'field':'last_name','direction':'desc','tie_breaker':{'field':'customer_id','direction':'asc'}})
    def complete_json(self,*args,**kwargs):
        return self.result.model_copy(deep=True)


def test_pass1_complete_sql19_preserves_fields_n_and_is_clear_lookup():
    question='按姓氏降序取前 5 位客户，返回编号、名字和姓氏；姓氏相同时按客户编号升序。'
    model=Model()
    semantic=candidate.extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),model)
    decision=RuleEngine().evaluate(question,semantic)
    assert semantic.task_type=='lookup' and semantic.metric is None and semantic.top_n==5
    assert semantic.order==model.result.order
    assert decision.level=='L0' and not decision.issues and decision.analysis.time_scope is None
    assert not decision.analysis.assumptions


@pytest.mark.parametrize('question',['按名字升序取前5位客户。','按客户编号降序列出前3名客户。'])
def test_pass1_supported_actual_customer_attributes(question):
    assert candidate.explicit_customer_attribute_top(question,load_catalog(ROOT/'data/catalog/chinook.yaml'))


@pytest.mark.parametrize('question',[
    '按姓氏降序取前5位客户，同时计算购买金额。',
    '按姓氏降序取前5位客户的平均客单价同比。',
    '按姓氏降序取前5位客户的数量。',
    '按姓氏降序取前5位客户，按国家分组汇总。',
    '员工按姓氏降序取前5位客户。',
    '客户谁买得最多，前5位？',
    '前5位客户的销售额是多少？',
    '按姓氏取前5位客户。',
    '按姓氏降序取客户。',
    '按未知属性降序取前5位客户。',
    '按姓氏降序取前0位客户。',
    '按姓氏降序取前10000位客户。'])
def test_pass2_business_or_unproven_requests_do_not_bypass_metric_gate(question):
    assert not candidate.explicit_customer_attribute_top(question,load_catalog(ROOT/'data/catalog/chinook.yaml'))


def test_pass2_aw_is_not_changed_by_chinook_attribute_rule():
    catalog=SimpleNamespace(database='AdventureWorks',tables=[])
    assert not candidate.explicit_customer_attribute_top('按姓氏降序取前5位客户。',catalog)


def test_pass2_unknown_real_column_is_not_invented():
    catalog=SimpleNamespace(database='chinook',tables=[SimpleNamespace(name='customer',schema='public',
                                                                    columns=[SimpleNamespace(name='customer_id')])])
    assert not candidate.explicit_customer_attribute_top('按姓氏降序取前5位客户。',catalog)


def test_pass2_existing_metric_or_growth_task_is_not_reclassified():
    question='按姓氏降序取前5位客户。'
    catalog=load_catalog(ROOT/'data/catalog/chinook.yaml')
    revenue=candidate.extract_intent(question,catalog,Model(SemanticIntent(task_type='ranking',metric='invoice_revenue',rank_object='customer',top_n=5)))
    assert revenue.task_type=='ranking' and revenue.metric=='invoice_revenue'
    growth=candidate.extract_intent(question,catalog,Model(SemanticIntent(task_type='growth',metric=None)))
    assert growth.task_type=='growth'


@pytest.mark.parametrize('suffix',[
    '统计营收总和。','按 revenue 再排名。','同时统计收入。','同时计算sales revenue。',
    '同时展示姓氏频率。','统计收益。','计算订单金额。','展示客单价。','统计sales。',
    '按amount排名。','calculate COUNT(customer_id)。','SUM(total)。','显示姓氏人数。'])
def test_independent_review_business_bypasses_are_rejected(suffix):
    question='按姓氏降序取前5位客户，'+suffix
    assert not candidate.explicit_customer_attribute_top(question,load_catalog(ROOT/'data/catalog/chinook.yaml'))


@pytest.mark.parametrize('object_name',['artist','艺术家','invoice','employee','customer.country','unknown'])
def test_other_model_ranking_objects_are_not_silently_reclassified(object_name):
    question='按姓氏降序取前5位客户。'
    semantic=candidate.extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),
        Model(SemanticIntent(task_type='ranking',metric=None,rank_object=object_name,top_n=5,
            order={'field':'last_name','direction':'desc'})))
    assert semantic.task_type=='ranking'


@pytest.mark.parametrize('object_name',[None,'customer','客户','顾客'])
def test_real_customer_ranking_object_spellings_are_bounded(object_name):
    question='按姓氏降序取前5位客户。'
    semantic=candidate.extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),
        Model(SemanticIntent(task_type='ranking',metric=None,rank_object=object_name,top_n=5,
            order={'field':'last_name','direction':'desc'})))
    assert semantic.task_type=='lookup' and semantic.rank_object in {None,'customer'}


def test_mixed_english_real_attributes_and_projection_are_proven():
    question='按last_name DESC取前5位客户，输出customer_id和first_name和last_name；last_name相同时按customer_id ASC。'
    assert candidate.explicit_customer_attribute_top(question,load_catalog(ROOT/'data/catalog/chinook.yaml'))


def test_unknown_projected_attribute_does_not_bypass():
    assert not candidate.explicit_customer_attribute_top('按姓氏降序取前5位客户，返回编号、余额。',load_catalog(ROOT/'data/catalog/chinook.yaml'))


@pytest.mark.parametrize('top_n',[None,3,6])
def test_missing_or_wrong_model_n_is_not_hidden_by_lookup(top_n):
    original=SemanticIntent(task_type='ranking',metric=None,rank_object='customer',top_n=top_n,
                            order={'field':'last_name','direction':'desc'})
    semantic=candidate.extract_intent('按姓氏降序取前5位客户。',load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(original))
    assert semantic.task_type=='ranking' and semantic.top_n==top_n and semantic.order==original.order


@pytest.mark.parametrize('order',[None,{},
    {'field':'first_name','direction':'desc'},
    {'field':'customer.country','direction':'desc'},
    {'field':'unknown','direction':'desc'},
    {'field':'last_name','direction':'asc'},
    {'field':'last_name'},
    {'direction':'desc'}])
def test_missing_or_wrong_model_primary_order_is_not_hidden_by_lookup(order):
    original=SemanticIntent(task_type='ranking',metric=None,rank_object='customer',top_n=5,order=order)
    semantic=candidate.extract_intent('按姓氏降序取前5位客户。',load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(original))
    assert semantic.task_type=='ranking' and semantic.top_n==5 and semantic.order==order


def test_qualified_real_model_order_retains_original_order():
    original=SemanticIntent(task_type='ranking',metric=None,rank_object='customer',top_n=5,
                            order={'field':'customer.last_name','direction':'DESC'})
    semantic=candidate.extract_intent('按姓氏降序取前5位客户。',load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(original))
    assert semantic.task_type=='lookup' and semantic.order==original.order and semantic.top_n==5


def test_whole_question_boundaries_still_reject_mixed_business_model_with_correct_n_order():
    question='按姓氏降序取前5位客户，同时统计营收总和。'
    semantic=candidate.extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),Model())
    assert semantic.task_type=='ranking' and semantic.metric is None and semantic.top_n==5
