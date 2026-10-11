"""Counterexamples for the actual D3 regenerated-SQL period-loss failure."""
from pathlib import Path

import pytest

from qa_agent.clarify.sql_guard import validate_confirmed_invoice_period
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import SQLValidationError

CATALOG=load_catalog(Path(__file__).resolve().parents[1]/'data/catalog/chinook.yaml')
CURRENT={'start':'2023-01-01','end':'2024-01-01'}


@pytest.mark.parametrize('sql',[
    "SELECT SUM(total) FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01'",
    "SELECT SUM(i.total) FROM public.invoice i JOIN customer c ON c.customer_id=i.customer_id WHERE c.country='Canada' AND i.invoice_date >= CAST('2023-01-01 00:00:00' AS TIMESTAMP) AND i.invoice_date < DATE '2024-01-01'",
    "SELECT SUM(i.total) FROM invoice i WHERE '2023-01-01' <= i.invoice_date AND '2024-01-01' > i.invoice_date",
    "SELECT SUM(total) FROM invoice WHERE (invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01' AND billing_country='Canada') OR (invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01' AND billing_country='USA')",
])
def test_equivalent_confirmed_period_alias_cast_and_both_or_branches(sql):
    validate_confirmed_invoice_period(sql,CATALOG,CURRENT)


@pytest.mark.parametrize('sql',[
    "SELECT SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id WHERE c.country='Canada'",
    "SELECT SUM(total), '2023-01-01', '2024-01-01' FROM invoice",
    "SELECT SUM(total) FROM invoice WHERE (invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01') OR billing_country='Canada'",
    "SELECT SUM(total) FROM invoice WHERE invoice_date >= '2024-01-01' AND invoice_date < '2025-01-01'",
    "SELECT SUM(total) FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01' AND invoice_date >= '2023-06-01'",
    "SELECT SUM(a.total) FROM invoice a JOIN invoice b ON a.customer_id=b.customer_id WHERE a.invoice_date >= '2023-01-01' AND a.invoice_date < '2024-01-01'",
    "SELECT SUM(total) FROM invoice WHERE invoice_id IN (SELECT invoice_id FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01')",
    "SELECT SUM(total) FROM invoice WHERE invoice_date >= CAST('2023-01-01 12:00:00' AS TIMESTAMP) AND invoice_date < '2024-01-01'",
    "SELECT COUNT(*) FROM customer",
    "SELECT SUM(x.total) FROM (SELECT total,invoice_date FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01') x WHERE x.invoice_date >= '2023-06-01'",
    "WITH x AS (SELECT total,invoice_date FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01') SELECT SUM(total) FROM x WHERE invoice_date >= '2023-06-01'",
])
def test_missing_wrong_narrowed_or_bypassed_period_is_rejected(sql):
    with pytest.raises(SQLValidationError):validate_confirmed_invoice_period(sql,CATALOG,CURRENT)
