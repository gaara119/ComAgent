"""Isolated strict-before date probes; no provider or database requests."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from qa_agent.clarify import extractor
from qa_agent.clarify.rules import SemanticIntent
from qa_agent.sql.catalog import load_catalog

spec=importlib.util.spec_from_file_location('oct12_sql22_staged',Path(__file__).with_name('rules_candidate.py'))
candidate=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=candidate
spec.loader.exec_module(candidate)

@pytest.mark.parametrize('question',[
    '列出 2004 年 1 月 1 日之前入职的员工编号、名字（仅 first_name，不包含姓氏 last_name）和入职日期，按员工编号升序。',
    '2004年1月1日之前入职的员工。','2004-01-01之前入职的员工。',
    '早于 2004 年 1 月 1 日入职的员工。','小于2004-01-01的入职日期。',
    '严格早于2004年1月1日入职的员工。'])
def test_literal_strict_before_has_only_open_upper_bound(question):
    current=candidate.explicit_period(question)['current']
    assert current['end']=='2004-01-01' and current['grain']=='before'
    assert 'start' not in current and '0001' not in str(current)
    assert current['label'] in question


@pytest.mark.parametrize('question',[
    '2004年1月1日及之前入职。','早于或等于2004年1月1日入职。',
    '小于等于2004年1月1日的日期。','2004年1月1日之前（含当天）入职。',
    '2004年1月1日之前或当天入职。','不早于2004年1月1日入职。',
    '不小于2004年1月1日的日期。','2004年1月1日之后入职。',
    '2004年1月1日以后入职。','晚于2004年1月1日入职。',
    '2004年1月1日次日之前入职。','2004年1月1日的翌日之前入职。',
    '2004年1月1日前一天之前入职。','日期<=2004-01-01。',
    '2004年2月30日之前入职。','2003年2月29日之前入职。',
    '0000年1月1日之前入职。','2004年13月1日之前入职。'])
def test_unsupported_or_invalid_date_comparisons_are_not_closed_window(question):
    assert candidate.explicit_period(question) is None


@pytest.mark.parametrize('question,expected',[
    ('2004 年 1 月 1 日入职。',{'start':'2004-01-01','end':'2004-01-02','grain':'custom'}),
    ('2004年2月29日入职。',{'start':'2004-02-29','end':'2004-03-01','grain':'custom'}),
    ('2004年12月31日入职。',{'start':'2004-12-31','end':'2005-01-01','grain':'custom'}),
    ('2003年12月1日至2004年1月1日入职。',{'start':'2003-12-01','end':'2004-01-02','grain':'custom'}),
    ('2003 年 12 月 1 日至 2004 年 1 月 1 日入职。',{'start':'2003-12-01','end':'2004-01-02','grain':'custom'}),
    ('2003年12月1日至2004年1月1日（不含）入职。',{'start':'2003-12-01','end':'2004-01-01','grain':'custom'}),
    ('2004 年 2 月入职。',{'start':'2004-02-01','end':'2004-03-01','grain':'month'}),
    ('2004年12月入职。',{'start':'2004-12-01','end':'2005-01-01','grain':'month'}),
    ('2004年入职。',{'start':'2004-01-01','end':'2005-01-01','grain':'year'}),
])
def test_genuine_complete_day_range_month_and_year_keep_existing_meaning(question,expected):
    current=candidate.explicit_period(question)['current']
    assert {key:current[key] for key in expected}==expected


def test_open_bound_not_shifted_by_local_clock_or_fabricated_floor():
    current=candidate.explicit_period('2004年1月1日之前')['current']
    assert current=={'end':'2004-01-01','grain':'before','label':'2004年1月1日之前'}


def test_same_actual_provider_response_no_longer_overwritten_by_month(monkeypatch):
    monkeypatch.setattr(extractor,'explicit_period',candidate.explicit_period)
    class Model:
        def complete_json(self,*args,**kwargs):
            return SemanticIntent(task_type='lookup',time_scope={'current':{'start':'0001-01-01','end':'2004-01-01','grain':'custom'}},
                filters=[{'field':'employee.hire_date','operator':'<','value':'2004-01-01'}],
                order={'field':'employee.employee_id','direction':'asc'})
    question='列出 2004 年 1 月 1 日之前入职的员工编号、名字和入职日期，按员工编号升序。'
    actual=extractor.extract_intent(question,load_catalog(ROOT/'data/catalog/chinook.yaml'),Model(),bindings=[])
    assert actual.task_type=='lookup' and actual.time_scope['current']['end']=='2004-01-01'
    assert actual.time_scope['current']['grain']=='before' and 'start' not in actual.time_scope['current']
    decision=candidate.RuleEngine(ROOT/'qa_agent/clarify/clarify_rules.yaml').evaluate(question,actual)
    assert decision.level=='L0' and not decision.issues


def test_open_before_cannot_fake_growth_base():
    scope=candidate.explicit_period('2004年1月1日之前销售额同比增长多少？')
    assert candidate.derive_base(scope['current'],'yoy') is None
    actual=candidate.RuleEngine(ROOT/'qa_agent/clarify/clarify_rules.yaml').evaluate('2004年1月1日之前销售额同比增长多少？',
        candidate.SemanticIntent(task_type='growth',metric='invoice_revenue',time_scope=scope,comparison={'type':'yoy'}))
    assert actual.level=='L2' and any(issue.field=='time_scope.base' for issue in actual.issues)
    assert not (actual.analysis.time_scope or {}).get('base')


def test_no_new_relative_period_or_year_comparison_default():
    assert candidate.explicit_period('去年之前入职的员工。') is None
    assert candidate.explicit_period('今年之前入职的员工。') is None
    assert candidate.explicit_comparison_period('2024年，和2023年比。','yoy')['current']['start']=='2024-01-01'
