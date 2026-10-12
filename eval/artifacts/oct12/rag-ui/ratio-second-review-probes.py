"""Independent AST proof probes for the staged midnight-boundary fix."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from sqlglot import parse_one
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import SQLValidationError

candidate_path = ROOT / "notes/oct12/staging/ratio/ratio_guard_candidate.py"
spec = importlib.util.spec_from_file_location("ratio_independent_review", candidate_path)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

cases = [
    ("'2024-01-01'", "2024-01-01"),
    ("CAST(CAST('2024-01-01 00:00:00' AS DATE) AS TIMESTAMP)", "2024-01-01"),
    ("CAST('2024-01-01T00:00:00.000' AS TIMESTAMP WITHOUT TIME ZONE)", "2024-01-01"),
    ("CAST(CAST('2024-01-01 00:00:00+00:00' AS TIMESTAMPTZ) AS TIMESTAMP)", None),
    ("CAST(CAST('2024-01-01' AS TEXT) AS TIMESTAMP)", None),
    ("DATE '2024-02-30'", None),
    ("TIMESTAMP '2024-01-01 00:00:00.000001'", None),
    ("DATE_TRUNC('day', DATE '2024-01-01')", None),
    ("TIMESTAMP '2024-01-01 00:00:00Z'", None),
]
rows = []
for expression, expected in cases:
    actual = candidate._period_literal_date(parse_one(expression, read="postgres"))
    rows.append({"expression": expression, "expected": expected, "actual": actual, "pass": actual == expected})

catalog = load_catalog(ROOT / "data/catalog/chinook.yaml")
bindings = [{"column": "invoice.billing_country", "operator": "=", "value": "Brazil"}]
context = {"task_type": "ratio", "metric": "invoice_revenue", "denominator": "同期全部发票金额",
           "time_scope": {"current": {"start": "2024-01-01", "end": "2025-01-01"}}}
base = ("SELECT SUM(CASE WHEN billing_country='Brazil' THEN total ELSE 0 END)/NULLIF(SUM(total),0) "
        "AS share FROM invoice WHERE invoice_date >= TIMESTAMP '2024-01-01 00:00:00' "
        "AND invoice_date < TIMESTAMP '2025-01-01 00:00:00'")
for name, sql in [
    ("midnight_does_not_allow_reversed_period", base.replace("< TIMESTAMP '2025-01-01", "< TIMESTAMP '2023-01-01")),
    ("midnight_does_not_allow_country_in_denominator", base + " AND billing_country='Brazil'"),
    ("midnight_does_not_allow_changed_numerator", base.replace("CASE WHEN billing_country='Brazil'", "CASE WHEN billing_country='USA'")),
]:
    try:
        candidate.validate_invoice_share(sql, catalog, bindings, context)
        rejected, error = False, None
    except SQLValidationError as exc:
        rejected, error = True, str(exc)
    rows.append({"id": name, "expected_rejected": True, "actual_rejected": rejected, "pass": rejected, "error": error})

report = {"state": "PASS" if all(row["pass"] for row in rows) else "FAIL",
          "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
          "kind": "实际本地AST与guard隔离探针；不是数据库实测或模型成绩",
          "checks": len(rows), "model_requests": 0, "holdout_predictions": 0,
          "business_files_modified": False, "probes": rows}
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["state"] == "PASS" else 1)
