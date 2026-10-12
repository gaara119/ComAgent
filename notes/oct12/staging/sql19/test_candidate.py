"""Isolated two-pass review probes for explicit customer attribute sorting."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from qa_agent.clarify.rules import SemanticIntent,RuleEngine
from qa_agent.sql.catalog import load_catalog

spec=importlib.util.spec_from_file_location('oct12_sql19_staged',Path(__file__).with_name('extractor_candidate.py'))
candidate=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=candidate
spec.loader.exec_module(candidate)
candidate.PROMPT_PATH=ROOT/'qa_agent/clarify/prompts/intent_extract.txt'


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
