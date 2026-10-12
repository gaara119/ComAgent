"""Read-only verification of the two explicitly requested developer golds."""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.executor import execute_sql


QUERIES = {
    "role_and_transaction": "SELECT current_user AS role_name, current_setting('transaction_read_only') AS transaction_read_only, current_setting('statement_timeout') AS statement_timeout, current_setting('server_version') AS server_version;",
    "track_schema": "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'track' AND column_name IN ('track_id','name','bytes','milliseconds') ORDER BY ordinal_position;",
    "track_scope": "SELECT COUNT(*) AS track_count, COUNT(bytes) AS bytes_known_count, COUNT(*) FILTER (WHERE bytes IS NULL) AS bytes_null_count, COUNT(milliseconds) AS milliseconds_known_count, COUNT(*) FILTER (WHERE milliseconds IS NULL) AS milliseconds_null_count, SUM(milliseconds::numeric) AS milliseconds_sum, AVG(milliseconds) AS average_milliseconds FROM public.track;",
    "sql-38_old": "SELECT track_id, name, bytes FROM public.track ORDER BY bytes DESC, track_id ASC LIMIT 3;",
    "sql-38_current_pending": "SELECT track_id, name, bytes FROM public.track ORDER BY bytes DESC NULLS LAST, track_id ASC LIMIT 3;",
    "sql-38_recommended": "SELECT track_id, name, bytes FROM public.track WHERE bytes IS NOT NULL ORDER BY bytes DESC, track_id ASC LIMIT 3;",
    "robust-23_recommended": "SELECT AVG(milliseconds) AS average_milliseconds FROM public.track;",
    "synthetic_desc_default": "SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint), (3, 80::bigint), (4, 80::bigint)) AS t(track_id, bytes) ORDER BY bytes DESC, track_id ASC LIMIT 3;",
    "synthetic_desc_nulls_last": "SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint), (3, 80::bigint), (4, 80::bigint)) AS t(track_id, bytes) ORDER BY bytes DESC NULLS LAST, track_id ASC LIMIT 3;",
    "synthetic_fewer_known_nulls_last": "SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint)) AS t(track_id, bytes) ORDER BY bytes DESC NULLS LAST, track_id ASC LIMIT 3;",
    "synthetic_fewer_known_exclusion": "SELECT track_id, bytes FROM (VALUES (1, NULL::bigint), (2, 100::bigint)) AS t(track_id, bytes) WHERE bytes IS NOT NULL ORDER BY bytes DESC, track_id ASC LIMIT 3;",
    "synthetic_average_null": "SELECT AVG(milliseconds) AS average_milliseconds, COUNT(milliseconds) AS nonnull_denominator FROM (VALUES (100), (300), (NULL::integer)) AS t(milliseconds);",
    "synthetic_average_empty": "SELECT AVG(milliseconds) AS average_milliseconds FROM (VALUES (100), (300)) AS t(milliseconds) WHERE false;",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="eval/artifacts/oct12/review-gold")
    parser.add_argument("--date-facts-only", action="store_true")
    args = parser.parse_args()
    destination = (ROOT / args.output).resolve()
    if not destination.is_relative_to(ROOT):
        raise SystemExit("Output must be inside the project")
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "readonly-verification.json"
    if output.exists():
        raise SystemExit("Verification already exists; use a new version instead of overwriting evidence.")
    settings = get_settings()
    started = datetime.now(timezone.utc).isoformat()
    records = []
    queries = QUERIES if not args.date_facts_only else {
        "invoice_available_dates": "SELECT COUNT(*) AS invoice_count, MIN(invoice_date) AS first_invoice_date, MAX(invoice_date) AS last_invoice_date, COUNT(*) FILTER (WHERE invoice_date IS NULL) AS null_invoice_date_count FROM public.invoice;",
        "invoice_yearly_summary": "SELECT EXTRACT(YEAR FROM invoice_date)::integer AS invoice_year, COUNT(*) AS invoice_count, SUM(total) AS invoice_amount FROM public.invoice GROUP BY EXTRACT(YEAR FROM invoice_date)::integer ORDER BY invoice_year;",
    }
    for identifier, sql in queries.items():
        before = time.perf_counter()
        try:
            result = execute_sql(sql, settings.db_url, settings.statement_timeout_ms, settings.max_rows)
            row = {"id": identifier, "sql": sql, "status": "executed", "result": asdict(result)}
        except Exception as exc:
            row = {"id": identifier, "sql": sql, "status": "failed", "error": sanitize_error(exc, settings)}
        row["elapsed_ms"] = round((time.perf_counter() - before) * 1000, 3)
        records.append(row)
    payload = {"created_at_utc": started, "source_script": "scripts/verify_oct12_gold.py", "invocation": ".\\.venv\\Scripts\\python.exe -B scripts/verify_oct12_gold.py --output " + destination.relative_to(ROOT).as_posix() + (" --date-facts-only" if args.date_facts_only else ""), "scope": "Actual available invoice dates/yearly aggregates only; no question predictions" if args.date_facts_only else "Only sql-38/robust-23 DEV gold SELECTs, schema/aggregate facts and synthetic VALUES; no model predictions", "read_only": True, "statement_timeout_ms": settings.statement_timeout_ms, "new_holdout_predictions": 0, "new_llm_requests": 0, "records": records}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "queries.sql").write_text("\n\n".join(f"-- {identifier}\n{sql}" for identifier, sql in queries.items()) + "\n", encoding="utf-8")
    print(json.dumps({"output": output.relative_to(ROOT).as_posix(), "queries": len(records), "failed": sum(r['status'] != 'executed' for r in records)}, ensure_ascii=False))
    return int(any(r["status"] != "executed" for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
