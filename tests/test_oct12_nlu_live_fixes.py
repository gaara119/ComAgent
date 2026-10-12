"""Actual runtime regressions for Gudian and employee-owned name fields."""
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.config import Settings
from qa_agent.nlu.value_index import ValueIndex,ValueRecord,record_id

from qa_agent.nlu import linker as staged


class NoModel:
    def complete_json(self,*args,**kwargs):
        raise AssertionError('Exact/pinyin proof should not call a model')


@pytest.mark.parametrize('connector',['这个','这种','这一种','的',''])
def test_gudian_uses_existing_approved_classical_alias(connector):
    index=ValueIndex([ValueRecord(record_id('genre.name','Classical'),'genre.name','Classical',
                                  '古典','existing-approved-fixture','alias','existing-id')])
    result=staged.ValueLinker(index,Settings(db_url=''),llm=NoModel()).link(f'Gudian {connector}流派的曲目有多少首？')
    assert result.bindings[0]['column']=='genre.name' and result.bindings[0]['value']=='Classical'
    assert result.bindings[0]['method']=='pinyin' and result.patches[0].original=='Gudian'


def test_employee_name_qualifier_does_not_bind_customer_lookalike():
    rows=[ValueRecord(record_id(column,value),column,value,value,'existing-index')
          for column,value in [('employee.first_name','Jane'),('employee.last_name','Peacock'),
                               ('customer.first_name','Janne'),('customer.last_name','Leacock')]]
    result=staged.ValueLinker(ValueIndex(rows),Settings(db_url=''),llm=NoModel()).link(
        '名字叫Jane、姓氏为Peacock的员工负责几位客户？')
    assert {item['column'] for item in result.bindings}=={'employee.first_name','employee.last_name'}
    assert {item['value'] for item in result.bindings}=={'Jane','Peacock'}
    assert not result.patches


def test_absent_employee_name_index_skips_linking_preserves_literals():
    rows=[ValueRecord(record_id(column,value),column,value,value,'existing-index')
          for column,value in [('employee.country','Canada'),('customer.first_name','Janne'),('customer.last_name','Leacock')]]
    question='名字叫Jane、姓氏为Peacock的员工负责几位客户？'
    result=staged.ValueLinker(ValueIndex(rows),Settings(db_url=''),llm=NoModel()).link(question)
    assert result.mentions==[] and not result.bindings and result.rewritten_question==question


def test_customer_name_after_employee_relation_is_not_reassigned():
    rows=[ValueRecord(record_id(column,value),column,value,value,'existing-index')
          for column,value in [('employee.first_name','Jane'),('employee.last_name','Peacock'),
                               ('customer.first_name','Robert')]]
    result=staged.ValueLinker(ValueIndex(rows),Settings(db_url=''),llm=NoModel()).link(
        '员工负责的客户名字为Robert，客户有几位？')
    assert result.bindings[0]['column']=='customer.first_name' and result.bindings[0]['value']=='Robert'


def test_actual_verified_index_for_both_real_failures():
    index=ValueIndex.load(ROOT/'data/indexes/values-oct12-approved')
    gudian=staged.ValueLinker(index,Settings(db_url=''),llm=NoModel()).link('Gudian 这个流派的曲目有多少首？')
    assert gudian.bindings[0]['value']=='Classical' and gudian.bindings[0]['method']=='pinyin'
    employee=staged.ValueLinker(index,Settings(db_url=''),llm=NoModel()).link(
        '名字叫Jane、姓氏为Peacock的员工负责几位客户？')
    assert {row['column'] for row in employee.bindings}=={'employee.first_name','employee.last_name'}
    assert not employee.patches
