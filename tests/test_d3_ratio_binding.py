"""Strict numerator-scope AST proofs must not weaken normal WHERE bindings."""
from pathlib import Path

import pytest
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import SQLValidationError, validate_value_bindings

ROOT=Path(__file__).resolve().parents[1]
CATALOG=load_catalog(ROOT/'data/catalog/chinook.yaml')
BINDINGS=[{'column':'invoice.billing_country','operator':'=','value':'Brazil'}]
CONTEXT={'task_type':'ratio','numerator':'2024年账单国家为Brazil的发票金额',
         'denominator':'同年所有发票金额','question':'2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？',
         'time_scope':{'current':{'start':'2024-01-01','end':'2025-01-01'}},'region_scope':'invoice.billing_country'}
VALID="SELECT SUM(CASE WHEN i.billing_country = 'Brazil' THEN i.total ELSE 0 END) / NULLIF(SUM(i.total),0) AS ratio FROM public.invoice i WHERE i.invoice_date >= '2024-01-01' AND i.invoice_date < '2025-01-01'"


def test_same_period_explicit_all_invoice_denominator_allows_bound_numerator_case():
    validate_value_bindings(VALID,CATALOG,BINDINGS,ratio_context=CONTEXT)
    validate_value_bindings(VALID.replace(' ELSE 0',''),CATALOG,BINDINGS,ratio_context=CONTEXT)
    validate_value_bindings(VALID.replace("i.billing_country = 'Brazil'","('Brazil' = i.billing_country)"),CATALOG,BINDINGS,ratio_context=CONTEXT)
    validate_value_bindings(VALID+" AND i.invoice_date >= '2024-01-01'",CATALOG,BINDINGS,ratio_context=CONTEXT)


def test_case_value_is_rejected_without_server_confirmed_ratio_context():
    with pytest.raises(SQLValidationError):validate_value_bindings(VALID,CATALOG,BINDINGS)


@pytest.mark.parametrize('sql',[
    VALID.replace("= 'Brazil'","= 'Canada'"),
    VALID.replace("= 'Brazil'","!= 'Brazil'"),
    VALID.replace("i.billing_country = 'Brazil'","i.billing_country = 'Brazil' OR i.total > 0"),
    VALID.replace('THEN i.total','THEN 1'),
    VALID.replace('ELSE 0','ELSE 1'),
    VALID.replace("i.invoice_date >= '2024-01-01'","i.invoice_date >= '2023-01-01'"),
    VALID.replace("i.invoice_date < '2025-01-01'","i.invoice_date <= '2025-01-01'"),
    VALID+" AND i.billing_country = 'Brazil'",
    VALID.replace("i.invoice_date >= '2024-01-01' AND i.invoice_date < '2025-01-01'","(i.invoice_date >= '2024-01-01' AND i.invoice_date < '2025-01-01') OR i.total > 0"),
    VALID.replace('NULLIF(SUM(i.total),0)','NULLIF(SUM(i.invoice_id),0)'),
    VALID.replace('NULLIF(SUM(i.total),0)','NULLIF(SUM(i.total),NULL)'),
    VALID+" AND i.invoice_date >= '2024-07-01'",
    VALID.replace("i.billing_country = 'Brazil'","i.billing_country = 'Brazil' AND i.customer_id = 1"),
    VALID.replace("i.billing_country = 'Brazil'","i.billing_country = 'Brazil' AND i.invoice_date >= '2024-07-01'"),
    "SELECT CASE WHEN billing_country='Brazil' THEN 1 ELSE 0 END AS ratio FROM invoice",
])
def test_scoped_mode_rejects_wrong_values_bypasses_periods_and_denominator(sql):
    with pytest.raises(SQLValidationError):validate_value_bindings(sql,CATALOG,BINDINGS,ratio_context=CONTEXT)


@pytest.mark.parametrize('context',[
    {**CONTEXT,'task_type':'lookup'},
    {**CONTEXT,'numerator':'2024年账单国家为Canada的发票金额'},
    {**CONTEXT,'denominator':'Brazil的发票金额'},
    {**CONTEXT,'time_scope':None},
    {**CONTEXT,'region_scope':'customer.country'},
    {**CONTEXT,'question':'2024年账单国家为Brazil的发票金额占全部发票金额的比例是多少？'},
])
def test_unconfirmed_scopes_cannot_disable_plain_mandatory_country_filter(context):
    with pytest.raises(SQLValidationError):validate_value_bindings(VALID,CATALOG,BINDINGS,ratio_context=context)


def test_unrelated_verified_binding_is_not_removed_by_ratio_context():
    bindings=BINDINGS+[{'column':'invoice.billing_city','operator':'=','value':'São Paulo'}]
    with pytest.raises(SQLValidationError):validate_value_bindings(VALID,CATALOG,bindings,ratio_context=CONTEXT)


def test_original_lookup_still_requires_mandatory_where_filter():
    with pytest.raises(SQLValidationError):
        validate_value_bindings("SELECT billing_country='Brazil' AS matched FROM invoice",CATALOG,BINDINGS)
    validate_value_bindings("SELECT SUM(total) FROM invoice WHERE billing_country='Brazil'",CATALOG,BINDINGS)
