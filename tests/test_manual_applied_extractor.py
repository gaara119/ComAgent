"""DEV-regression failures: direct byte sorting and approved scope provenance."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from qa_agent.clarify import extractor
from qa_agent.clarify.rules import RuleEngine, SemanticIntent, explicit_period
from qa_agent.sql.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[1]
QUESTION = ('找出文件大小已记录的曲目中，字节数最大的前3首，返回曲目编号、名称和字节数；'
            '按字节数降序，并列按曲目编号升序。')


class Model:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def complete_json(self, *args, **kwargs):
        self.calls += 1
        return self.result.model_copy(deep=True)


def catalog():
    return load_catalog(ROOT / 'data/catalog/chinook.yaml')


def byte_intent(**changes):
    values = dict(task_type='ranking', metric=None, rank_object='track', top_n=3,
                  order={'field': 'bytes', 'direction': 'desc'},
                  evidence_spans={'metric': '字节数'})
    values.update(changes)
    return SemanticIntent(**values)


def test_complete_byte_attribute_lookup_keeps_n_primary_tie_and_null_qualifier():
    result = extractor.extract_intent(QUESTION, catalog(), Model(byte_intent()))
    decision = RuleEngine().evaluate(QUESTION, result)
    assert result.task_type == 'lookup' and result.metric is None and result.top_n == 3
    assert result.order == {'field': 'bytes', 'direction': 'desc',
                            'tie_breakers': [{'field': 'track.track_id', 'direction': 'asc'}]}
    assert '文件大小已记录' in result.evidence_spans['attribute_lookup']
    assert decision.level == 'L0' and not decision.issues


@pytest.mark.parametrize('question, n, direction', [
    ('按字节数升序取前5首曲目，返回曲目编号和字节数。', 5, 'asc'),
    ('找出文件大小已知的曲目中，字节数最小的前2首；并列按曲目编号降序。', 2, 'asc'),
    ('找出文件字节数最大的7首曲目。', 7, 'desc'),
])
def test_real_field_lookup_is_not_a_top3_or_desc_special_case(question, n, direction):
    proof = extractor.explicit_track_byte_top(question, catalog(), expected_n=n,
                                               expected_order={'field': 'track.bytes', 'direction': direction})
    assert proof and proof['top_n'] == n and proof['order']['direction'] == direction


@pytest.mark.parametrize('suffix', [
    '同时统计销售额。', '按国家分组汇总。', '再按购买数量排名。',
    '只看2024年美国售出的曲目。', '同时计算SUM(total)。', '返回编号和余额。',
    '且查这些客户的客单价。', '按字节数升序。', '并列按未知字段升序。',
])
def test_unparsed_constraints_or_conflicting_order_never_bypass_gate(suffix):
    question = QUESTION.rstrip('。') + '；' + suffix
    assert extractor.explicit_track_byte_top(question, catalog()) is None
    result = extractor.extract_intent(question, catalog(), Model(byte_intent()))
    assert result.task_type == 'ranking'
    if result.metric is None:
        assert any(issue.id == 'missing:metric' for issue in RuleEngine().evaluate(question, result).issues)


@pytest.mark.parametrize('question', [
    '这批曲目中字节数最大的前3首有哪些？',
    '按字节数排序取前3首曲目。',
    '按字节数降序取前0首曲目。',
    '按字节数降序取前5001首曲目。',
    '客户按字节数降序取前3首曲目。',
])
def test_scope_direction_range_and_object_must_be_fully_proven(question):
    assert extractor.explicit_track_byte_top(question, catalog()) is None


@pytest.mark.parametrize('changes', [
    {'top_n': 10}, {'order': {'field': 'bytes', 'direction': 'asc'}},
    {'order': {'field': 'unit_price', 'direction': 'desc'}},
    {'rank_object': 'customer'}, {'metric': 'detail_revenue'}, {'task_type': 'growth'},
])
def test_conflicting_model_shape_or_existing_business_metric_is_not_reclassified(changes):
    result = extractor.extract_intent(QUESTION, catalog(), Model(byte_intent(**changes)))
    assert result.task_type != 'lookup'


def test_proof_checks_actual_catalog_table_and_projection_columns():
    missing = SimpleNamespace(database='chinook', tables=[
        SimpleNamespace(name='track', schema='public', columns=[SimpleNamespace(name='bytes')])])
    assert extractor.explicit_track_byte_top(QUESTION, missing) is None
    assert extractor.explicit_track_byte_top(QUESTION, SimpleNamespace(database='AdventureWorks', tables=[])) is None
    assert extractor.explicit_track_byte_top(QUESTION, SimpleNamespace(database='chinook', tables=[])) is None


BRAZIL = {'column': 'invoice.billing_country', 'operator': '=', 'value': 'Brazil'}


def growth_intent(**changes):
    values = dict(task_type='growth', metric='invoice_revenue', comparison={'type': 'yoy'},
                  time_scope=explicit_period('2024年'))
    values.update(changes)
    return SemanticIntent(**values)


def test_program_selected_billing_default_is_l1_with_source_note():
    question = '2024年巴西的销售额同比2023年增长了多少？'
    result = extractor.extract_intent(question, catalog(), Model(growth_intent()), bindings=[BRAZIL])
    decision = RuleEngine().evaluate(question, result)
    assert result.region_scope == 'invoice.billing_country'
    assert result.default_assumptions == result.assumptions
    assert len(result.default_assumptions) == 1 and decision.level == 'L1'


@pytest.mark.parametrize('scope_word, expected', [
    ('账单国', 'invoice.billing_country'), ('客户所在地', 'customer.country'),
])
def test_explicit_region_scope_has_priority_and_is_not_a_default(scope_word, expected):
    question = f'2024年巴西{scope_word}的销售额同比2023年增长了多少？'
    result = extractor.extract_intent(question, catalog(), Model(growth_intent()), bindings=[BRAZIL])
    decision = RuleEngine().evaluate(question, result)
    assert result.region_scope == expected and not result.default_assumptions
    assert not result.assumptions and decision.level == 'L0'


def test_default_marker_cannot_hide_a_missing_current_period():
    question = '巴西的销售额同比增长多少？'
    result = extractor.extract_intent(question, catalog(), Model(growth_intent(time_scope=None)), bindings=[BRAZIL])
    decision = RuleEngine().evaluate(question, result)
    assert result.default_assumptions and decision.level == 'L2'
    assert any(issue.field == 'time_scope.current' for issue in decision.issues)


def test_fast_path_program_default_is_also_l1_without_model_call():
    question = '2024年巴西的销售额是多少？'
    model = Model(SemanticIntent())
    result = extractor.extract_intent(question, catalog(), model, bindings=[BRAZIL])
    assert model.calls == 0 and result.region_scope == 'invoice.billing_country'
    assert result.default_assumptions == result.assumptions
    assert RuleEngine().evaluate(question, result).level == 'L1'


def test_non_default_explanation_does_not_make_every_assumption_l1():
    result = SemanticIntent(assumptions=['用户明确要求字段，解释其输出单位。'])
    assert RuleEngine().evaluate('列出曲目编号。', result).level == 'L0'

