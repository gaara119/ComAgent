"""Allow proven identical midnight bounds while rejecting scope changes."""
import pytest
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.ratio_guard import validate_invoice_share
from qa_agent.sql.validator import SQLValidationError

@pytest.fixture
def catalog():
    return load_catalog(get_settings().catalog_path)

BINDINGS=[{"column":"invoice.billing_country","operator":"=","value":"Brazil"}]
CONTEXT={"task_type":"ratio","metric":"invoice_revenue","denominator":"同期全部发票金额",
         "time_scope":{"current":{"start":"2024-01-01","end":"2025-01-01"}}}

def query(start,end):
    return "SELECT SUM(CASE WHEN billing_country='Brazil' THEN total ELSE 0 END)/NULLIF(SUM(total),0) AS share FROM invoice WHERE invoice_date >= "+start+" AND invoice_date < "+end

@pytest.mark.parametrize("format",["'{}'","CAST('{}' AS DATE)","CAST('{} 00:00:00' AS TIMESTAMP)","TIMESTAMP '{}T00:00:00.000000'","CAST('{} 00:00:00.000' AS TIMESTAMP(6))"])
def test_static_equivalent_midnight_allowed(catalog,format):
    assert validate_invoice_share(query(format.format("2024-01-01"),format.format("2025-01-01")),catalog,BINDINGS,CONTEXT)

@pytest.mark.parametrize("start",["TIMESTAMP '2024-01-01 00:00:01'","TIMESTAMP '2024-01-01 12:00:00'","TIMESTAMP '2024-01-01 00:00:00.000001'","TIMESTAMPTZ '2024-01-01 00:00:00+08:00'","'2024-01-01 00:00:00+00:00'","DATE_TRUNC('year', NOW())","CAST('2024-01-01' AS TEXT)","TIMESTAMP '2024-01-02 00:00:00'"])
def test_non_equivalent_or_unproven_boundaries_rejected(catalog,start):
    with pytest.raises(SQLValidationError):
        validate_invoice_share(query(start,"TIMESTAMP '2025-01-01 00:00:00'"),catalog,BINDINGS,CONTEXT)

def test_country_where_still_rejected(catalog):
    with pytest.raises(SQLValidationError):
        validate_invoice_share(query("TIMESTAMP '2024-01-01 00:00:00'","TIMESTAMP '2025-01-01 00:00:00'")+" AND billing_country='Brazil'",catalog,BINDINGS,CONTEXT)

def test_midnight_proof_does_not_allow_wrong_numerator(catalog):
    with pytest.raises(SQLValidationError):
        validate_invoice_share(query("TIMESTAMP '2024-01-01 00:00:00'","TIMESTAMP '2025-01-01 00:00:00'").replace("billing_country='Brazil'","billing_country='France'"),catalog,BINDINGS,CONTEXT)
