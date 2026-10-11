"""Offline candidate counterexamples, no API/DB or held dataset reads."""
from dataclasses import replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parent))
from customer_ratio_candidate import validate_customer_invoice_ratio_candidate, verified_country_binding_surfaces
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import SQLValidationError, validate_value_bindings

ROOT=Path(__file__).resolve().parents[6]
CATALOG=load_catalog(ROOT/'data/catalog/chinook.yaml')
B=[{'column':'customer.country','operator':'=','value':'France'}]
NUM='法国居住客户的销售额'
DEN='2024年所有发票销售额'
C={'task_type':'ratio','numerator':NUM,'denominator':DEN,'question':'2024年法国居住客户的销售额占比是多少？',
   'time_scope':{'current':{'start':'2024-01-01','end':'2025-01-01'}},'region_scope':'customer.country',
   'verified_binding_surfaces':[{'column':'customer.country','value':'France','surfaces':['法国','France']}],
   'confirmed_resolutions':[{'message':'分母就用2024年所有发票销售额。','patches':[{'path':'denominator','op':'set','value':DEN,'evidence':'分母就用2024年所有发票销售额。'}]}]}
FROM=" FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id WHERE i.invoice_date>='2024-01-01' AND i.invoice_date<'2025-01-01'"
FRACTION="SELECT SUM(CASE WHEN c.country='France' THEN i.total ELSE 0 END)/NULLIF(SUM(i.total),0) AS share"+FROM
PERCENT="SELECT CASE WHEN SUM(i.total)=0 THEN NULL ELSE ROUND(SUM(CASE WHEN c.country='France' THEN i.total ELSE 0 END)*100.0/SUM(i.total),2) END AS share_percent"+FROM


@pytest.mark.parametrize('sql',[FRACTION,PERCENT,FRACTION.replace("c.country='France'","('France'=c.country)"),FRACTION.replace(' ELSE 0',''),FRACTION+" AND i.invoice_date>='2024-01-01'"])
def test_local_numerator_and_global_denominator_good(sql):
    assert validate_customer_invoice_ratio_candidate(sql,CATALOG,B,C)


@pytest.mark.parametrize('sql',[
 FRACTION+" AND c.country='France'",
 FRACTION+" AND i.invoice_date>='2024-07-01'",
 FRACTION.replace("c.country='France'","c.country='Germany'"),
 FRACTION.replace("c.country='France'","c.country='France' AND i.customer_id=1"),
 FRACTION.replace("c.country='France'","c.country='France' OR i.total>0"),
 FRACTION.replace('THEN i.total','THEN 1'),
 FRACTION.replace('ELSE 0','ELSE 1'),
 FRACTION.replace('NULLIF(SUM(i.total),0)','NULLIF(SUM(i.total),NULL)'),
 FRACTION.replace('NULLIF(SUM(i.total),0)','SUM(i.total)'),
 FRACTION.replace('i.customer_id=c.customer_id','i.invoice_id=c.customer_id'),
 FRACTION.replace('JOIN public.customer','LEFT JOIN public.customer'),
 FRACTION.replace('JOIN public.customer','CROSS JOIN public.customer'),
 FRACTION.replace('i.customer_id=c.customer_id','i.customer_id=c.customer_id AND c.country=\'France\''),
 FRACTION.replace('SUM(i.total),0','SUM(i.invoice_id),0'),
 FRACTION.replace("i.invoice_date>='2024-01-01'","i.invoice_date>='2023-01-01'"),
 FRACTION.replace("'2024-01-01'","CAST('2024-01-01' AS TIMESTAMPTZ)"),
 FRACTION+' LIMIT 0',
 FRACTION.replace('SELECT ','SELECT 123, ',1),
 PERCENT.replace('*100.0','*50.0'),
 PERCENT.replace('SUM(i.total)=0','SUM(i.total) IS NULL'),
 PERCENT.replace('THEN NULL','THEN 0'),
 "WITH q AS ("+FRACTION+") SELECT * FROM q",
 FRACTION+" OR i.total>0",
])
def test_narrow_mode_fails_closed(sql):
    with pytest.raises(SQLValidationError):validate_customer_invoice_ratio_candidate(sql,CATALOG,B,C)


@pytest.mark.parametrize('context',[
 {**C,'confirmed_resolutions':[]},
 {**C,'denominator':'2024年所有法国发票销售额'},
 {**C,'denominator':'2023年所有发票销售额'},
 {**C,'numerator':'德国居住客户的销售额'},
 {**C,'region_scope':'invoice.billing_country'},
 {**C,'verified_binding_surfaces':[]},
 {**C,'verified_binding_surfaces':[{'column':'customer.country','value':'Germany','surfaces':['法国']}]},
 {**C,'confirmed_resolutions':[{'message':'按法国客户算。','patches':[{'op':'set','path':'denominator','value':DEN,'evidence':'全部'}]}]},
 {**C,'confirmed_resolutions':C['confirmed_resolutions']+[{'message':'分母改成德国的发票金额。','patches':[{'op':'set','path':'denominator','value':'德国发票金额','evidence':'分母改成德国的发票金额。'}]}]},
])
def test_current_real_denominator_provenance_required(context):
    with pytest.raises(SQLValidationError):validate_customer_invoice_ratio_candidate(FRACTION,CATALOG,B,context)


@pytest.mark.parametrize('kind',['no_pk','no_fk','nullable_fk'])
def test_schema_must_prove_nonduplicating_and_nonmissing_join(kind):
    tables=[]
    for t in CATALOG.tables:
        if kind=='no_pk' and t.name=='customer':t=replace(t,primary_key=())
        if kind=='no_fk' and t.name=='invoice':t=replace(t,foreign_keys=())
        if kind=='nullable_fk' and t.name=='invoice':t=replace(t,columns=tuple(replace(c,nullable=True) if c.name=='customer_id' else c for c in t.columns))
        tables.append(t)
    with pytest.raises(SQLValidationError):validate_customer_invoice_ratio_candidate(FRACTION,replace(CATALOG,tables=tuple(tables)),B,C)


def test_original_normal_filter_guard_still_rejects_select_country_literal():
    assert not validate_customer_invoice_ratio_candidate("SELECT 1",CATALOG,B,{**C,'task_type':'lookup'})
    with pytest.raises(SQLValidationError):validate_value_bindings("SELECT country='France' FROM customer",CATALOG,B)


def test_other_real_bindings_cannot_be_dropped():
    with pytest.raises(SQLValidationError):validate_customer_invoice_ratio_candidate(FRACTION,CATALOG,B+[{'column':'invoice.billing_city','operator':'=','value':'Paris'}],C)


def test_different_actual_customer_country_binding_cannot_reuse_old_numerator():
    with pytest.raises(SQLValidationError):
        validate_customer_invoice_ratio_candidate(FRACTION.replace('France','Germany'),CATALOG,
            [{'column':'customer.country','operator':'=','value':'Germany'}],
            {**C,'verified_binding_surfaces':[{'column':'customer.country','value':'Germany','surfaces':['德国']}]})


def test_single_global_fraction_differs_from_wrong_where_in_independent_fixture():
    import sqlite3
    con=sqlite3.connect(':memory:')
    con.executescript("CREATE TABLE invoice(invoice_id INTEGER,customer_id INTEGER,invoice_date TEXT,total NUMERIC);"
                      "CREATE TABLE customer(customer_id INTEGER,country TEXT);"
                      "INSERT INTO customer VALUES(1,'France'),(2,'Germany');"
                      "INSERT INTO invoice VALUES(1,1,'2024-03-01',30),(2,2,'2024-05-01',70);")
    sql=FRACTION.replace('public.','').replace('THEN i.total','THEN i.total*1.0')
    assert con.execute(sql).fetchone()[0]==0.3
    assert con.execute(sql+" AND c.country='France'").fetchone()[0]==1.0
    assert validate_customer_invoice_ratio_candidate(FRACTION,CATALOG,B,C)
    with pytest.raises(SQLValidationError):validate_customer_invoice_ratio_candidate(FRACTION+" AND c.country='France'",CATALOG,B,C)
    con.close()


def test_pending_and_conditional_aliases_cannot_supply_direct_numerator_proof():
    from types import SimpleNamespace
    from qa_agent.nlu.value_index import ValueRecord
    index=SimpleNamespace(records=[
        ValueRecord('x','customer.country','France','法国','review','alias','approved-fr'),
        ValueRecord('x','customer.country','France','法兰西','draft','pending','pending-fr'),
        ValueRecord('x','customer.country','France','法兰西候选','review','conditional_alias','conditional-fr'),
    ])
    for reference in ('pending-fr','conditional-fr','other-ref'):
        surfaces=verified_country_binding_surfaces(index,[{**B[0],'evidence_ref':reference}])
        assert surfaces[0]['surfaces']==['France']
    assert verified_country_binding_surfaces(index,[{**B[0],'evidence_ref':'approved-fr'}])[0]['surfaces']==['France','法国']


def test_latest_numerator_change_cannot_reuse_old_source_text():
    context={**C,'confirmed_resolutions':C['confirmed_resolutions']+[
        {'message':'分子改成德国居住客户的销售额。','patches':[{'op':'set','path':'numerator','value':'德国居住客户的销售额','evidence':'德国居住客户的销售额'}]}]}
    with pytest.raises(SQLValidationError):validate_customer_invoice_ratio_candidate(FRACTION,CATALOG,B,context)
