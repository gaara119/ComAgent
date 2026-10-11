"""Independently verify the saved D3 free-year growth answer, without new predictions."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import validate_sql
from qa_agent.sql.executor import execute_sql

def main():
    source = ROOT / 'eval/artifacts/d3/b/clarify-flow-v6/free-year-resumed.json'
    output = ROOT / 'eval/artifacts/d3/root-interface/free-growth-independent-readonly.json'
    if output.exists():
        raise RuntimeError('Do not overwrite an existing audit record')
    actual = json.loads(source.read_text(encoding='utf-8-sig'))['response']
    current = "SUM(CASE WHEN invoice_date >= DATE '2024-01-01' AND invoice_date < DATE '2025-01-01' THEN total ELSE 0 END)"
    base = "SUM(CASE WHEN invoice_date >= DATE '2023-01-01' AND invoice_date < DATE '2024-01-01' THEN total ELSE 0 END)"
    sql = f"SELECT {current} AS current_revenue, {base} AS base_revenue, ({current}-{base}) / NULLIF({base},0) AS yoy_growth_rate FROM public.invoice WHERE billing_country='USA' AND invoice_date >= DATE '2023-01-01' AND invoice_date < DATE '2025-01-01'"
    settings = get_settings()
    checked = validate_sql(sql, load_catalog(settings.catalog_path), max_rows=settings.max_rows)
    result = execute_sql(checked.sql, settings.db_url, settings.statement_timeout_ms, settings.max_rows)
    matched = actual['status'] == 'SUCCEEDED' and actual['table'] == result.table
    record = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        command=[sys.executable, '-B', *sys.argv], source_file=source.relative_to(ROOT).as_posix(),
        source_sha256=sha256(source.read_bytes()).hexdigest(),
        method='Existing qa_reader; fresh read-only transaction; unchanged 5000ms timeout; independent single-pass conditional sums; no model/API request',
        independent_sql=checked.sql, reference_result=result.table, actual_table=actual['table'],
        matched=matched, verdict='AI建议通过' if matched else 'AI发现错误',
        interpretation='Growth is a fraction, not an already multiplied percentage; NULLIF protects a zero base. Period and billing-country context verified separately in the saved flow.',
        human_review_status='pending_human_review', prediction_calls=0)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'matched': matched, 'reference_result': result.table, 'prediction_calls': 0}, ensure_ascii=False))
    return 0 if matched else 1

if __name__ == '__main__':
    raise SystemExit(main())
