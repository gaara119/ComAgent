"""Test the isolated proof against the actual failed SQL and scope bypasses."""
import importlib.util
from pathlib import Path
import pytest

from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import SQLValidationError

spec = importlib.util.spec_from_file_location("oct12_ratio_candidate", Path(__file__).with_name("ratio_guard_candidate.py"))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
CATALOG = load_catalog(get_settings().catalog_path)
BINDINGS = [{"column":"invoice.billing_country","operator":"=","value":"Brazil"}]
CONTEXT = {"task_type":"ratio","metric":"invoice_revenue","denominator":"同期全部发票金额",
           "time_scope":{"current":{"start":"2024-01-01","end":"2025-01-01"}}}

def query(start, end):
    return "SELECT SUM(CASE WHEN billing_country='Brazil' THEN total ELSE 0 END)/NULLIF(SUM(total),0) AS share FROM invoice WHERE invoice_date >= " + start + " AND invoice_date < " + end

@pytest.mark.parametrize("format", ["'{}'", "CAST('{}' AS DATE)", "CAST('{} 00:00:00' AS TIMESTAMP)", "TIMESTAMP '{}T00:00:00.000000'", "CAST('{} 00:00:00.000' AS TIMESTAMP(6))"])
def test_equivalent_static_midnight_is_allowed(format):
    assert candidate.validate_invoice_share(query(format.format("2024-01-01"), format.format("2025-01-01")), CATALOG, BINDINGS, CONTEXT)

@pytest.mark.parametrize("start", ["TIMESTAMP '2024-01-01 00:00:01'", "TIMESTAMP '2024-01-01 12:00:00'", "TIMESTAMP '2024-01-01 00:00:00.000001'", "TIMESTAMPTZ '2024-01-01 00:00:00+08:00'", "'2024-01-01 00:00:00+00:00'", "DATE_TRUNC('year', NOW())", "CAST('2024-01-01' AS TEXT)", "TIMESTAMP '2024-01-02 00:00:00'"])
def test_non_equivalent_or_unproven_boundary_is_rejected(start):
    with pytest.raises(SQLValidationError):
        candidate.validate_invoice_share(query(start, "TIMESTAMP '2025-01-01 00:00:00'"), CATALOG, BINDINGS, CONTEXT)

def test_global_country_filter_still_rejected_with_midnight_dates():
    with pytest.raises(SQLValidationError):
        candidate.validate_invoice_share(query("TIMESTAMP '2024-01-01 00:00:00'", "TIMESTAMP '2025-01-01 00:00:00'") + " AND billing_country='Brazil'", CATALOG, BINDINGS, CONTEXT)

def test_exact_real_failure_sql_passes_narrow_proof():
    import json
    root = Path(__file__).resolve().parents[4]
    record = json.loads((root / "eval/artifacts/oct12/ui-live/run-003/invoice-ratio-raw.json").read_text(encoding="utf-8"))
    response = record.get("response", record)
    actual = next(step["output_summary"]["sql"] for step in response["steps"] if step["name"] == "sql_gen" and step["status"] == "ok")
    assert candidate.validate_invoice_share(actual, CATALOG, BINDINGS, CONTEXT)
